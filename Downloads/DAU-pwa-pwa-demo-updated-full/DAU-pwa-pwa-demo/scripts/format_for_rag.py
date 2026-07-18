#!/usr/bin/env python3
"""
format_for_rag.py — RAG Chunk Compliance Formatter
===================================================
Takes a markdown file and ensures it is well-structured for the
256-token chunk limit used by the DAU RAG pipeline:

  1. Reads the file and splits on H2 (##) boundaries.
  2. Any H2 section exceeding 256 tokens is automatically split
     into logical sub-sections (### H3 headings).
  3. Long paragraphs (>256 tokens) are split at sentence boundaries.
  4. Tables are kept intact (they are converted to sentences at ingest time).
  5. Writes the formatted file back (in-place or to --output).

Usage:
    python scripts/format_for_rag.py data/academics/some_file.md
    python scripts/format_for_rag.py data/academics/some_file.md --output out.md
    python scripts/format_for_rag.py --all data/           # process entire folder
"""

import re
import sys
import argparse
from pathlib import Path
from typing import List, Tuple

# ---------------------------------------------------------------------------
# Token counter
# ---------------------------------------------------------------------------
try:
    from transformers import AutoTokenizer
    _tok = AutoTokenizer.from_pretrained("BAAI/bge-base-en-v1.5")
    def count_tokens(text: str) -> int:
        return len(_tok.encode(text, add_special_tokens=False))
except Exception:
    def count_tokens(text: str) -> int:
        return max(1, len(text) // 4)

CHUNK_SIZE = 256
SPLIT_TARGET = 200       # aim to keep sections below this

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def strip_frontmatter(text: str) -> Tuple[str, str]:
    """Return (frontmatter_str, body_str)."""
    text = text.lstrip('\ufeff')
    m = re.match(r'^(---[\s\S]*?---)\s*', text)
    if m:
        return m.group(1), text[m.end():]
    return "", text


def split_into_sentences(paragraph: str) -> List[str]:
    """Split a paragraph into sentences at [.?!] boundaries."""
    sentences = re.split(r'(?<=[.?!])\s+', paragraph.strip())
    return [s for s in sentences if s.strip()]


def split_paragraph_by_tokens(para: str, max_tokens: int = SPLIT_TARGET) -> List[str]:
    """Split a long paragraph into token-limited sub-paragraphs."""
    sentences = split_into_sentences(para)
    groups = []
    current = []
    current_tokens = 0
    for sent in sentences:
        t = count_tokens(sent)
        if current_tokens + t > max_tokens and current:
            groups.append(" ".join(current))
            current = [sent]
            current_tokens = t
        else:
            current.append(sent)
            current_tokens += t
    if current:
        groups.append(" ".join(current))
    return groups


def is_table_line(line: str) -> bool:
    return line.strip().startswith('|')


def is_heading(line: str, level: int = None) -> bool:
    if level:
        return bool(re.match(rf'^{"#"*level} ', line))
    return bool(re.match(r'^#{1,6} ', line))


def split_section_content(h2_title: str, content: str) -> List[str]:
    """
    Given an H2 section's content, split into sub-sections if it
    exceeds CHUNK_SIZE tokens. Returns list of markdown block strings.
    """
    total_tokens = count_tokens(content)
    if total_tokens <= CHUNK_SIZE:
        return [f"## {h2_title}\n\n{content}"]

    # Already has H3 — split on them
    if re.search(r'^### ', content, re.MULTILINE):
        h3_blocks = re.split(r'(?=^### )', content, flags=re.MULTILINE)
        results = []
        for block in h3_blocks:
            block = block.strip()
            if not block:
                continue
            results.append(f"## {h2_title}\n\n{block}")
        return results

    # No H3 — split content by paragraphs, then by sentences if needed
    paragraphs = re.split(r'\n{2,}', content.strip())
    groups = []
    current_group = []
    current_tokens = 0

    for para in paragraphs:
        para_tokens = count_tokens(para)
        # If single paragraph is huge, split by sentences
        if para_tokens > CHUNK_SIZE:
            sub_paras = split_paragraph_by_tokens(para)
            for sp in sub_paras:
                sp_tokens = count_tokens(sp)
                if current_tokens + sp_tokens > SPLIT_TARGET and current_group:
                    groups.append("\n\n".join(current_group))
                    current_group = [sp]
                    current_tokens = sp_tokens
                else:
                    current_group.append(sp)
                    current_tokens += sp_tokens
        else:
            if current_tokens + para_tokens > SPLIT_TARGET and current_group:
                groups.append("\n\n".join(current_group))
                current_group = [para]
                current_tokens = para_tokens
            else:
                current_group.append(para)
                current_tokens += para_tokens

    if current_group:
        groups.append("\n\n".join(current_group))

    # Build output with auto-generated H3 sub-sections
    if len(groups) == 1:
        return [f"## {h2_title}\n\n{groups[0]}"]

    results = []
    for i, group in enumerate(groups):
        if i == 0:
            results.append(f"## {h2_title}\n\n{group}")
        else:
            results.append(f"## {h2_title} (continued {i+1})\n\n{group}")
    return results


# ---------------------------------------------------------------------------
# Main formatter
# ---------------------------------------------------------------------------

def format_for_rag(text: str) -> Tuple[str, int, int]:
    """
    Format markdown text for RAG compliance.
    Returns (formatted_text, sections_before, sections_after).
    """
    fm, body = strip_frontmatter(text)

    # Split on H2 boundaries
    parts = re.split(r'(?=^## )', body, flags=re.MULTILINE)

    # Separate preamble (H1 + intro before first H2) from H2 sections
    preamble = ""
    h2_sections = []
    for part in parts:
        if re.match(r'^## ', part):
            h2_sections.append(part.strip())
        else:
            preamble += part

    sections_before = len(h2_sections)
    new_h2_sections = []

    for sec in h2_sections:
        # Parse H2 title
        first_line, *rest_lines = sec.splitlines()
        h2_title = re.sub(r'^## ', '', first_line).strip()
        content = "\n".join(rest_lines).strip()

        # Check if table dominates — keep table sections intact
        table_lines = sum(1 for l in content.splitlines() if is_table_line(l))
        total_lines = len(content.splitlines())
        is_table_heavy = total_lines > 0 and table_lines / total_lines > 0.5

        if is_table_heavy or count_tokens(content) <= CHUNK_SIZE:
            new_h2_sections.append(f"## {h2_title}\n\n{content}")
        else:
            splits = split_section_content(h2_title, content)
            new_h2_sections.extend(splits)

    sections_after = len(new_h2_sections)

    # Rebuild document
    body_new = preamble.strip() + "\n\n" + "\n\n".join(new_h2_sections)
    body_new = re.sub(r'\n{3,}', '\n\n', body_new).strip()

    if fm:
        result = fm + "\n\n" + body_new + "\n"
    else:
        result = body_new + "\n"

    return result, sections_before, sections_after


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def process_file(fp: Path, output: Path = None):
    text = fp.read_text(encoding='utf-8', errors='replace')
    formatted, before, after = format_for_rag(text)
    out_path = output or fp
    out_path.write_text(formatted, encoding='utf-8')
    diff = after - before
    sign = f"+{diff}" if diff >= 0 else str(diff)
    print(f"  {fp.name}: {before} → {after} H2 sections ({sign}) — {len(formatted)} chars")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Format markdown for RAG 256-token compliance")
    parser.add_argument("path",     nargs="?", help="Single .md file to format")
    parser.add_argument("--output", help="Output path (default: in-place)")
    parser.add_argument("--all",    help="Process all .md files under this directory")
    args = parser.parse_args()

    if args.all:
        base = Path(args.all)
        files = sorted(base.rglob("*.md"))
        print(f"Processing {len(files)} files under {base} …\n")
        for fp in files:
            process_file(fp)
    elif args.path:
        fp = Path(args.path)
        if not fp.exists():
            print(f"ERROR: {fp} not found")
            sys.exit(1)
        out = Path(args.output) if args.output else None
        process_file(fp, out)
    else:
        parser.print_help()
        sys.exit(1)
