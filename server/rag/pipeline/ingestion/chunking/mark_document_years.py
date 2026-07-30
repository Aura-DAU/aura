"""
One-time (re-runnable) data-curation pass over /data.

Writes an explicit `document_year:` field into each markdown file's YAML
frontmatter wherever the year the document actually applies to can be
confidently determined — using the SAME precedence and regex as ingestion
(process_corpus.py): title -> filename -> path -> first 1000 chars of body.

Why this exists (see conversation): document_year previously had to be
re-derived at every ingestion run via runtime regex, and when nothing could
be found it silently fell back to scraped_date's year or today's date —
which has nothing to do with which academic year a policy applies to.
That fallback has been removed from process_corpus.py. This script instead
makes the corpus self-describing: run it once, and every file that HAS a
determinable year gets it written directly into frontmatter, so future
ingestion runs don't need to re-guess and can't silently drift.

Deliberately conservative: if no confident year signal exists anywhere for a
file (title/filename/path/body), we do NOT invent one. Those files are
listed in the "needs manual review" report instead — most are genuinely
year-agnostic pages (campus facilities, contact info, general policy pages
with no version), which is fine, but a human should confirm rather than
have the pipeline fabricate a year for them.

Usage:
    cd server/rag/pipeline/ingestion/chunking
    python3 mark_document_years.py /path/to/data [--dry-run]
"""
import argparse
import re
import sys
from pathlib import Path

import yaml

from year_extraction import extract_academic_or_calendar_year


FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)


def determine_year(file_path: Path, metadata: dict, body: str):
    """Same precedence as process_markdown_file's document_year block,
    minus the removed scraped_date/today fallbacks."""
    if metadata.get("document_year") is not None:
        return extract_academic_or_calendar_year(metadata.get("document_year")), "already marked"
    if metadata.get("year") is not None:
        return extract_academic_or_calendar_year(metadata.get("year")), "frontmatter:year"
    if metadata.get("batch_year") is not None:
        return extract_academic_or_calendar_year(metadata.get("batch_year")), "frontmatter:batch_year"
    if metadata.get("batch") is not None:
        return extract_academic_or_calendar_year(metadata.get("batch")), "frontmatter:batch"
    if metadata.get("tenure") is not None:
        return extract_academic_or_calendar_year(metadata.get("tenure")), "frontmatter:tenure"
    if metadata.get("semester") is not None:
        y = extract_academic_or_calendar_year(metadata.get("semester"))
        if y is not None:
            return y, "frontmatter:semester"

    title_val = metadata.get("title") or metadata.get("original_name")
    if title_val:
        y = extract_academic_or_calendar_year(title_val)
        if y is not None:
            return y, "title"

    y = extract_academic_or_calendar_year(file_path.name)
    if y is not None:
        return y, "filename"

    for part in file_path.parts:
        y = extract_academic_or_calendar_year(part)
        if y is not None:
            return y, "path"

    y = extract_academic_or_calendar_year(body[:1000])
    if y is not None:
        return y, "body"

    return None, None


def insert_document_year(raw_content: str, year_value) -> str:
    """Insert `document_year: "..."` as the line right after `title:` in the
    frontmatter block (or at the top of frontmatter if no title line)."""
    m = FRONTMATTER_RE.match(raw_content)
    fm_text = m.group(1)
    year_line = f'document_year: "{year_value}"'
    lines = fm_text.split("\n")
    inserted = False
    for i, line in enumerate(lines):
        if line.startswith("title:"):
            lines.insert(i + 1, year_line)
            inserted = True
            break
    if not inserted:
        lines.insert(0, year_line)
    new_fm = "\n".join(lines)
    return raw_content[: m.start(1)] + new_fm + raw_content[m.end(1):]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data_dir", help="Path to the data/ folder")
    ap.add_argument("--dry-run", action="store_true", help="Report only, don't write files")
    args = ap.parse_args()

    data_dir = Path(args.data_dir)
    files = sorted(data_dir.rglob("*.md"))

    marked = []          # (path, year, source)
    already_marked = []  # path already had document_year
    unresolved = []      # no confident year anywhere

    for fp in files:
        # Faculty profile pages are ongoing/permanent and should not be stamped with a document_year
        if "faculty" in fp.parts:
            continue
        raw_orig = fp.read_text(encoding="utf-8", errors="ignore")
        # Same normalization process_corpus.py applies before matching
        # frontmatter: strip a leading BOM and normalize CRLF -> LF. Without
        # this, files saved with a UTF-8 BOM or Windows line endings (both
        # present in this corpus) silently fail the frontmatter match and
        # get treated as "no metadata" even though they have a normal
        # frontmatter block.
        raw = raw_orig.lstrip("\ufeff").replace("\r\n", "\n")
        bom_stripped = raw_orig != raw

        m = FRONTMATTER_RE.match(raw)
        metadata = {}
        body = raw
        fm_ok = True
        if m:
            try:
                metadata = yaml.safe_load(m.group(1)) or {}
                # Body starts right after the closing '---'; skip a following
                # newline if present (some files are missing it, e.g.
                # "---# Heading" with no blank line — tolerate that too).
                body_start = m.end()
                if body_start < len(raw) and raw[body_start] == "\n":
                    body_start += 1
                body = raw[body_start:]
            except Exception as e:
                fm_ok = False
                unresolved.append((fp, f"frontmatter parse error: {e}"))
                continue
        # If there's genuinely no frontmatter block, metadata stays {} and
        # body stays the whole file — we still try filename/path/body below
        # rather than giving up, since the year can often still be found
        # there even without a metadata dict.

        year_value, source = determine_year(fp, metadata, body)

        if source == "already marked":
            already_marked.append(fp)
            continue

        if year_value is None:
            reason = "no year signal in title/filename/path/body" if m else "no year signal (and no frontmatter block at all)"
            unresolved.append((fp, reason))
            continue

        if not m:
            # No frontmatter to insert a document_year line into — flag for
            # manual review rather than fabricating a frontmatter block.
            unresolved.append((fp, f"found year {year_value} via {source} but file has no frontmatter block to write it into"))
            continue

        marked.append((fp, year_value, source))
        if not args.dry_run:
            new_raw = insert_document_year(raw, year_value)
            if bom_stripped:
                new_raw = "\ufeff" + new_raw
            fp.write_text(new_raw, encoding="utf-8")

    print(f"Total markdown files scanned: {len(files)}")
    print(f"Already had document_year: {len(already_marked)}")
    print(f"Newly marked{' (dry-run, not written)' if args.dry_run else ''}: {len(marked)}")
    print(f"Left unresolved (needs manual review): {len(unresolved)}")
    print()

    by_source = {}
    for _, _, source in marked:
        by_source[source] = by_source.get(source, 0) + 1
    print("Newly marked, broken down by where the year came from:")
    for source, count in sorted(by_source.items(), key=lambda x: -x[1]):
        print(f"  {source}: {count}")
    print()

    report_path = data_dir.parent / "document_year_marking_report.txt"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"Total markdown files scanned: {len(files)}\n")
        f.write(f"Already had document_year: {len(already_marked)}\n")
        f.write(f"Newly marked: {len(marked)}\n")
        f.write(f"Left unresolved: {len(unresolved)}\n\n")
        f.write("=== Newly marked (path -> year, source) ===\n")
        for fp, year_value, source in marked:
            f.write(f"{fp.relative_to(data_dir.parent)} -> {year_value}  [{source}]\n")
        f.write("\n=== Needs manual review (no confident year found) ===\n")
        for fp, reason in unresolved:
            f.write(f"{fp.relative_to(data_dir.parent)}  [{reason}]\n")

    print(f"Full report written to: {report_path}")


if __name__ == "__main__":
    main()
