"""
AURA Data Quality Auditor
=========================
Scans every .md file in the data/ directory and tests for:

  1. STUB / EMPTY       — file has no real content (just frontmatter + title)
  2. GARBLED_ENCODING   — control chars from broken PDF font CMap extraction
  3. OCR_NOISE          — garbled table text, semicolons as col separators, ligature errors
  4. SCANNED_PDF        — image-only PDF pages with near-zero extractable text
  5. EXCEL_BAD_HEADERS  — "Unnamed: N" column headers from multi-row Excel headers
  6. HEADING_MISSING    — file has no H2/H3 structure (single flat block, bad for RAG)
  7. CHUNK_OVERFLOW     — a section exceeds 256 tokens (will cause oversized chunks in RAG)
  8. CRLF_ENCODING      — Windows CRLF line endings (breaks YAML frontmatter parsing)
  9. FRONTMATTER_BROKEN — YAML frontmatter missing required fields

Usage:
    python 1_audit_files.py --data ../../data --out audit_report

Output:
    audit_report/audit_results.json   — full machine-readable report
    audit_report/audit_summary.csv    — one row per file, easy to sort/filter
    audit_report/to_reextract.txt     — list of files that need re-extraction
"""

import re
import os
import sys
import csv
import json
import argparse
import yaml
from pathlib import Path
from datetime import datetime

# ─────────────────────────── TOKEN ESTIMATION ────────────────────────────────
# Matches the BGE-base-en-v1.5 tokenizer used in chunker.py
# (roughly 1.3 subword tokens per whitespace-split word for English text)
CHUNK_SIZE = 256   # must match chunking/config.py

def estimate_tokens(text: str) -> int:
    return int(len(text.split()) * 1.3)


# ─────────────────────────── DETECTION RULES ─────────────────────────────────

REQUIRED_FM_FIELDS = ["title", "url", "category"]

# Control chars that signal broken PDF font-encoding (not tab/CR/LF)
CTRL_CHAR_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")

# OCR noise patterns found in scanned academic PDFs.
# IMPORTANT: patterns are deliberately tight to avoid false positives on
# legitimate academic abbreviations like IT, DA, Ph, CS, ICT, BTech etc.
OCR_NOISE_PATTERNS = [
    # " ; " used as column separator in garbled tables (space-semicolon-space)
    re.compile(r"(?<!\w)\s;\s(?!\w)"),
    # \boe\b as a standalone word (fi/oe ligature artefact from PDF fonts)
    re.compile(r"\boe\b"),
    # The word "Saati" which appears exclusively as OCR garbling of numbers
    re.compile(r"\bSaati\b"),
    # Digit embedded in the middle of an all-lowercase word (e.g. reg1strat1un, ab3cd)
    re.compile(r"\b[a-z]{2,}\d+[a-z]{2,}\b"),
    # Curly brace used as table cell delimiter ({| or |}) — never valid markdown
    re.compile(r"\{\||\|\}"),
    # Three or more repeated identical non-space, non-dash, non-pipe, non-hash, non-star chars in a row
    # (e.g. "aaa", "sss", "eee") — common in garbled scans but not in normal text
    re.compile(r"([^\s\-|#*])\1{3,}"),
]

# Excel "Unnamed" column headers
UNNAMED_COL_RE = re.compile(r"Unnamed:\s*\d+")

# Heading pattern
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)", re.MULTILINE)


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """Extract YAML frontmatter and body. Returns (metadata_dict, body_str)."""
    content = content.lstrip("\ufeff").replace("\r\n", "\n")
    match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
    if not match:
        return {}, content
    try:
        metadata = yaml.safe_load(match.group(1)) or {}
        if not isinstance(metadata, dict):
            metadata = {}
    except Exception:
        metadata = {"_yaml_error": True}
    body = content[match.end():]
    return metadata, body


def audit_file(filepath: Path, data_root: Path) -> dict:
    """
    Audit a single .md file. Returns an audit record dict.
    """
    rel = str(filepath.relative_to(data_root))
    result = {
        "file": rel,
        "issues": [],
        "issue_details": {},
        "needs_reextract": False,
        "priority": "ok",   # ok | low | medium | high | critical
        "source_type": None,
        "url": None,
    }

    # ── Read file ─────────────────────────────────────────────────────────────
    raw_bytes = filepath.read_bytes()
    has_crlf = b"\r\n" in raw_bytes
    try:
        content = raw_bytes.decode("utf-8", errors="replace")
    except Exception:
        result["issues"].append("READ_ERROR")
        result["needs_reextract"] = True
        result["priority"] = "critical"
        return result

    metadata, body = parse_frontmatter(content)
    result["source_type"] = metadata.get("source_type", "web")
    result["url"] = metadata.get("url", "")
    file_size = filepath.stat().st_size
    fixed_issues = set(metadata.get("fixes_applied", []))

    # ── 8. CRLF ───────────────────────────────────────────────────────────────
    if has_crlf:
        result["issues"].append("CRLF_ENCODING")
        result["issue_details"]["crlf"] = "File uses Windows CRLF line endings; YAML parser may misread frontmatter."

    # ── 9. FRONTMATTER BROKEN ─────────────────────────────────────────────────
    if metadata.get("_yaml_error"):
        result["issues"].append("FRONTMATTER_BROKEN")
        result["issue_details"]["frontmatter"] = "YAML parse error in frontmatter."
    else:
        missing_fields = [f for f in REQUIRED_FM_FIELDS if not metadata.get(f)]
        if missing_fields:
            result["issues"].append("FRONTMATTER_BROKEN")
            result["issue_details"]["frontmatter"] = f"Missing required fields: {missing_fields}"

    # Strip frontmatter for content analysis
    main_content = body.strip()

    # ── 1. STUB / EMPTY ───────────────────────────────────────────────────────
    # Strip headings and horizontal rules, count real content words
    stripped = re.sub(r"^#{1,6}\s+.*$", "", main_content, flags=re.MULTILINE)
    stripped = re.sub(r"^---+$", "", stripped, flags=re.MULTILINE)
    stripped = stripped.strip()
    word_count = len(stripped.split())

    FAKE_STUB_DISCLAIMER = "could not be fully extracted during scraping"
    has_disclaimer = FAKE_STUB_DISCLAIMER in main_content

    # Files honestly marked as non-fetchable by 4_fix_fake_stubs.py should not
    # be re-flagged. These statuses mean the URL was attempted and documented.
    HONEST_STATUSES = {"sparse_content", "unreachable", "social_media_js_wall", "live_fetched"}
    extraction_status = metadata.get("extraction_status", "")
    is_honestly_marked = extraction_status in HONEST_STATUSES

    if (word_count < 30 or has_disclaimer) and "STUB_EMPTY" not in fixed_issues and not is_honestly_marked:
        result["issues"].append("STUB_EMPTY")
        if has_disclaimer:
            result["issue_details"]["stub"] = (
                "File contains LLM hallucination disclaimer: "
                "'could not be fully extracted during scraping'. "
                "Body is a generated placeholder, not real scraped content."
            )
        else:
            result["issue_details"]["stub"] = (
                f"Only {word_count} content words after stripping headings/rules. "
                "Page likely image-only or URL returned no content."
            )

    # ── 2. GARBLED_ENCODING ───────────────────────────────────────────────────
    lines = main_content.split("\n")
    garbled_lines = [l for l in lines if CTRL_CHAR_RE.search(l)]
    garbled_ratio = len(garbled_lines) / max(len(lines), 1)

    if (len(garbled_lines) > 5 or garbled_ratio > 0.05) and "GARBLED_ENCODING" not in fixed_issues:
        result["issues"].append("GARBLED_ENCODING")
        result["issue_details"]["garbled"] = (
            f"{len(garbled_lines)} lines ({garbled_ratio:.1%}) contain control chars "
            f"(\\x00–\\x1f). PDF used non-standard font encoding (no CMap). "
            f"Sample: {repr(garbled_lines[0][:80]) if garbled_lines else ''}"
        )

    # ── 3. OCR_NOISE ──────────────────────────────────────────────────────────
    ocr_hits = {}
    for pat in OCR_NOISE_PATTERNS:
        matches = pat.findall(main_content)
        if len(matches) >= 3:   # 3+ occurrences = systematic, not incidental
            ocr_hits[pat.pattern] = len(matches)

    if ocr_hits and "OCR_NOISE" not in fixed_issues:
        result["issues"].append("OCR_NOISE")
        result["issue_details"]["ocr_noise"] = (
            f"Systematic OCR artefacts detected: {ocr_hits}. "
            "Tables likely garbled; text needs re-extraction with pdfplumber + LLM cleanup."
        )

    # ── 4. SCANNED_PDF ────────────────────────────────────────────────────────
    is_pdf = str(metadata.get("source_type", "")).upper() == "PDF" or "pdf" in str(metadata.get("url", "")).lower()
    if is_pdf and word_count < 80 and file_size < 3000 and "SCANNED_PDF" not in fixed_issues:
        result["issues"].append("SCANNED_PDF")
        result["issue_details"]["scanned_pdf"] = (
            f"Source is PDF but only {word_count} content words extracted ({file_size} bytes). "
            "PDF likely image-only (certificate, scan, diagram). Needs OCR."
        )

    # ── 5. EXCEL_BAD_HEADERS ─────────────────────────────────────────────────
    unnamed_count = len(UNNAMED_COL_RE.findall(main_content))
    if unnamed_count >= 3 and "EXCEL_BAD_HEADERS" not in fixed_issues:
        result["issues"].append("EXCEL_BAD_HEADERS")
        result["issue_details"]["excel_headers"] = (
            f"{unnamed_count} 'Unnamed: N' column headers found. "
            "Excel file has merged header rows; re-read with header=[0,1] or manual row detection."
        )

    # ── 6. HEADING_MISSING ────────────────────────────────────────────────────
    headings = HEADING_RE.findall(main_content)
    h2_h3_count = sum(1 for level, _ in headings if len(level) in (2, 3))
    if word_count > 150 and h2_h3_count == 0:
        result["issues"].append("HEADING_MISSING")
        result["issue_details"]["heading_missing"] = (
            f"File has {word_count} words but zero H2/H3 headings. "
            "RAG section extractor will produce one giant chunk. "
            "Add H2/H3 headings to break content into logical sections."
        )

    # ── 7. CHUNK_OVERFLOW ────────────────────────────────────────────────────
    # Split body into sections using same logic as section_extracter.py
    sections = _extract_sections_simple(main_content)
    overflowing = []
    for sec in sections:
        tok = estimate_tokens(sec["content"])
        if tok > CHUNK_SIZE:
            label = sec.get("h2") or sec.get("h1") or "(root)"
            overflowing.append({"section": label, "tokens": tok})

    if overflowing:
        result["issues"].append("CHUNK_OVERFLOW")
        result["issue_details"]["chunk_overflow"] = (
            f"{len(overflowing)} sections exceed {CHUNK_SIZE} tokens. "
            f"Worst: {max(overflowing, key=lambda x: x['tokens'])}. "
            "Chunker will split mid-sentence unless sections are subdivided."
        )

    # ── Derive priority + needs_reextract ────────────────────────────────────
    critical_issues = {"GARBLED_ENCODING", "SCANNED_PDF", "STUB_EMPTY"}
    high_issues     = {"OCR_NOISE", "EXCEL_BAD_HEADERS", "FRONTMATTER_BROKEN"}
    # HEADING_MISSING and CHUNK_OVERFLOW do NOT require re-scraping the source URL —
    # they are fixed by LLM post-processing of the existing markdown body.
    medium_issues   = {"HEADING_MISSING", "CHUNK_OVERFLOW"}
    low_issues      = {"CRLF_ENCODING"}

    issue_set = set(result["issues"])
    if issue_set & critical_issues:
        result["priority"] = "critical"
        result["needs_reextract"] = True
    elif issue_set & high_issues:
        result["priority"] = "high"
        # needs_reextract = True only for issues that need source re-download;
        # FRONTMATTER_BROKEN alone is fixable without re-scraping.
        result["needs_reextract"] = bool(issue_set & {"OCR_NOISE", "EXCEL_BAD_HEADERS"})
    elif issue_set & medium_issues:
        result["priority"] = "medium"
        result["needs_reextract"] = False  # LLM post-process on existing body
    elif issue_set & low_issues:
        result["priority"] = "low"
        result["needs_reextract"] = False
    else:
        result["priority"] = "ok"

    return result


def _extract_sections_simple(body: str) -> list[dict]:
    """Simplified section extractor matching section_extracter.py logic."""
    lines = body.split("\n")
    sections = []
    current = {"h1": None, "h2": None, "h3": None, "content": []}

    def flush():
        text = "\n".join(current["content"]).strip()
        if text:
            sections.append({**current, "content": text})

    for line in lines:
        m = HEADING_RE.match(line)
        if m:
            level = len(m.group(1))
            title = m.group(2).strip()
            flush()
            current["content"] = []
            if level == 1:
                current = {"h1": title, "h2": None, "h3": None, "content": []}
            elif level == 2:
                current["h2"] = title
                current["h3"] = None
            elif level == 3:
                current["h3"] = title
        else:
            current["content"].append(line)

    flush()
    return sections


# ─────────────────────────── MAIN ────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="AURA Data Quality Auditor")
    parser.add_argument("--data", default="../../data",
                        help="Path to the data/ directory (default: ../../data)")
    parser.add_argument("--out", default="audit_report",
                        help="Output directory for reports (default: audit_report)")
    parser.add_argument("--filter", default=None,
                        help="Only audit files under this subfolder (e.g. 'administration')")
    args = parser.parse_args()

    data_root = Path(args.data).resolve()
    out_dir   = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    if not data_root.exists():
        print(f"[ERROR] data directory not found: {data_root}")
        sys.exit(1)

    md_files = sorted(data_root.rglob("*.md"))
    if args.filter:
        md_files = [f for f in md_files if args.filter in str(f)]

    print(f"\n{'─'*60}")
    print(f"  AURA Data Quality Auditor")
    print(f"  Data dir : {data_root}")
    print(f"  Files    : {len(md_files)}")
    print(f"  Output   : {out_dir}/")
    print(f"{'─'*60}\n")

    results = []
    counts  = {"ok": 0, "low": 0, "medium": 0, "high": 0, "critical": 0}

    for i, fp in enumerate(md_files, 1):
        rec = audit_file(fp, data_root)
        results.append(rec)
        counts[rec["priority"]] += 1

        status_icon = {
            "ok": "✅", "low": "⚠️ ", "medium": "🟡",
            "high": "🔴", "critical": "🚨"
        }.get(rec["priority"], "?")

        issues_str = ", ".join(rec["issues"]) if rec["issues"] else "—"
        print(f"[{i:4d}/{len(md_files)}] {status_icon} {rec['priority'].upper():8s} | "
              f"{issues_str:45s} | {rec['file']}")

    # ── JSON report ──────────────────────────────────────────────────────────
    json_out = out_dir / "audit_results.json"
    with open(json_out, "w", encoding="utf-8") as f:
        json.dump({
            "generated": datetime.now().isoformat(),
            "data_root": str(data_root),
            "total_files": len(results),
            "counts": counts,
            "results": results,
        }, f, indent=2, ensure_ascii=False)

    # ── CSV report ───────────────────────────────────────────────────────────
    csv_out = out_dir / "audit_summary.csv"
    with open(csv_out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "priority", "needs_reextract", "file", "issues", "url", "source_type"
        ])
        writer.writeheader()
        for rec in sorted(results, key=lambda r: (
            ["critical","high","medium","low","ok"].index(r["priority"]), r["file"]
        )):
            writer.writerow({
                "priority": rec["priority"],
                "needs_reextract": rec["needs_reextract"],
                "file": rec["file"],
                "issues": " | ".join(rec["issues"]),
                "url": rec.get("url", ""),
                "source_type": rec.get("source_type", ""),
            })

    # ── Files-to-reextract list ───────────────────────────────────────────────
    reextract_out = out_dir / "to_reextract.txt"
    to_reextract = [r for r in results if r["needs_reextract"]]
    with open(reextract_out, "w", encoding="utf-8") as f:
        for rec in sorted(to_reextract, key=lambda r: r["priority"]):
            issues = " | ".join(rec["issues"])
            f.write(f"{rec['priority'].upper():8s}  {issues:50s}  {rec['file']}\n")

    # ── Summary ───────────────────────────────────────────────────────────────
    print(f"\n{'─'*60}")
    print("  AUDIT COMPLETE")
    print(f"{'─'*60}")
    print(f"  Total files  : {len(results)}")
    print(f"  ✅  OK        : {counts['ok']}")
    print(f"  ⚠️   Low       : {counts['low']}")
    print(f"  🟡  Medium    : {counts['medium']}")
    print(f"  🔴  High      : {counts['high']}")
    print(f"  🚨  Critical  : {counts['critical']}")
    print(f"\n  Files needing re-extraction: {len(to_reextract)}")
    print(f"\n  Reports saved to:")
    print(f"    {json_out}")
    print(f"    {csv_out}")
    print(f"    {reextract_out}")
    print(f"{'─'*60}\n")


if __name__ == "__main__":
    main()
