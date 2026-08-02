#!/usr/bin/env python3
"""
audit_data.py — DAU PWA Data Quality Auditor
=============================================
Scans every .md file in data/ and produces a JSON report classifying
each file into one of the severity categories below.

Usage (from repo root):
    python scripts/audit_data.py
    python scripts/audit_data.py --data-dir data --output audit_report.json

Severity Categories:
    CRITICAL  — Control chars / binary mojibake garbage
    WARN      — OCR noise / broken tables / missing H1+H2 structure
    LOW       — Stub / near-empty content (<200 chars)
    CHUNK     — A section exceeds 512 tokens (will be auto-split but flag it)
    OK        — No issues detected
"""

import os
import re
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List
# ---------------------------------------------------------------------------
# Token counter — lightweight estimate for audit (no model download needed)
# For exact counts, see format_for_rag.py which loads BAAI/bge-base-en-v1.5
# ---------------------------------------------------------------------------
def count_tokens(text: str) -> int:
    """Fast estimate: ~4 chars per token (conservative for English text)."""
    return max(1, len(text) // 4)


CHUNK_SIZE = 256          # from config.py
CHUNK_WARN_MULTIPLIER = 2 # warn if section > 512 tokens (will be split but may fragment badly)

# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

# Control characters (excluding \t \n \r which are fine)
CONTROL_CHAR_RE = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]')

# Raw binary / Latin-1 mojibake (runs of high-byte chars)
BINARY_RE = re.compile(r'[\x80-\xff]{6,}')

# Spaced-out OCR letters: "I T 4 9 2 :" (every other char is a space)
SPACED_OCR_RE = re.compile(r'(?:[A-Za-z0-9] ){5,}[A-Za-z0-9]')

# Long runs of the same consonant (corrupted font maps)
CONSONANT_RUN_RE = re.compile(r'[bcdfghjklmnpqrstvwxyz]{15,}', re.IGNORECASE)

# Markdown table header: | Col1 | Col2 |
TABLE_HEADER_RE = re.compile(r'^\|.+\|$')
# Markdown table separator: | --- | :---: |
TABLE_SEP_RE = re.compile(r'^\|[\s\|:\-]+\|$')

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def strip_frontmatter(text: str) -> str:
    """Return body text with YAML front-matter removed."""
    return re.sub(r'^---[\s\S]*?---\s*', '', text).strip()


def parse_frontmatter(text: str) -> Dict:
    text = text.lstrip('\ufeff')
    m = re.match(r'^---\s*\n(.*?)\n---', text, re.DOTALL)
    if not m:
        return {}
    result = {}
    for line in m.group(1).splitlines():
        kv = re.match(r'^(\w+)\s*:\s*"?(.*?)"?\s*$', line)
        if kv:
            result[kv.group(1)] = kv.group(2).strip().strip('"').strip("'")
    return result


# ---------------------------------------------------------------------------
# Individual issue detectors
# ---------------------------------------------------------------------------

def detect_control_chars(text: str) -> List[str]:
    chars = set(CONTROL_CHAR_RE.findall(text))
    if chars:
        return [f"Control chars: {[repr(c) for c in sorted(chars)]}"]
    return []


def detect_binary(text: str) -> List[str]:
    m = BINARY_RE.search(text)
    if m:
        return [f"Binary/mojibake at pos {m.start()}: {m.group(0)[:20]!r}"]
    return []


def detect_ocr_noise(text: str) -> List[str]:
    issues = []
    m = SPACED_OCR_RE.search(text)
    if m:
        issues.append(f"Spaced OCR chars: {m.group(0)[:30]!r}")
    m = CONSONANT_RUN_RE.search(text)
    if m:
        issues.append(f"Consonant-run corruption: {m.group(0)[:30]!r}")
    return issues


def detect_broken_tables(body: str) -> List[str]:
    """Detect malformed markdown tables."""
    issues = []
    lines = body.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        if TABLE_HEADER_RE.match(line):
            expected_cols = line.count('|') - 1
            # Next line must be separator
            if i + 1 >= len(lines) or not TABLE_SEP_RE.match(lines[i + 1].rstrip()):
                issues.append(f"L{i+1}: Table header not followed by separator")
                i += 1
                continue
            # Check data rows
            j = i + 2
            while j < len(lines) and TABLE_HEADER_RE.match(lines[j].rstrip()):
                row_cols = lines[j].rstrip().count('|') - 1
                if abs(row_cols - expected_cols) > 1:
                    issues.append(f"L{j+1}: Row has {row_cols} cols, expected {expected_cols}")
                j += 1
            i = j
            continue
        i += 1
    return issues[:5]


def detect_heading_structure(body: str) -> List[str]:
    issues = []
    if not re.search(r'^# .+', body, re.MULTILINE):
        issues.append("No H1 heading found")
    if not re.search(r'^## .+', body, re.MULTILINE):
        issues.append("No H2 headings — sections not structured for RAG chunking")
    return issues


def detect_chunk_violations(body: str) -> List[str]:
    """Flag sections that are so large they will produce bad chunk splits."""
    issues = []
    # Split on H2 and H3 boundaries
    sections = re.split(r'(?=^#{2,3} )', body, flags=re.MULTILINE)
    for sec in sections:
        sec = sec.strip()
        if not sec:
            continue
        tokens = count_tokens(sec)
        if tokens > CHUNK_SIZE * CHUNK_WARN_MULTIPLIER:
            first_line = sec.splitlines()[0][:70]
            issues.append(f"~{tokens} tokens (>{CHUNK_SIZE*CHUNK_WARN_MULTIPLIER}) in section: {first_line!r}")
    return issues[:4]


# ---------------------------------------------------------------------------
# Per-file audit
# ---------------------------------------------------------------------------

def audit_file(fp: Path) -> Dict:
    try:
        text = fp.read_text(encoding='utf-8', errors='replace')
    except Exception as e:
        return {
            "path": str(fp), "title": "", "url": "",
            "severity": "CRITICAL",
            "issues": [f"Cannot read file: {e}"],
            "content_chars": 0,
        }

    fm = parse_frontmatter(text)
    body = strip_frontmatter(text)
    content_chars = len(body)

    issues: List[str] = []

    # CRITICAL
    issues += detect_control_chars(text)
    issues += detect_binary(text)

    # WARN
    issues += detect_ocr_noise(body)
    issues += detect_broken_tables(body)
    issues += detect_heading_structure(body)

    # LOW
    if content_chars < 200:
        issues.append(f"Stub: only {content_chars} chars of body content")

    # CHUNK
    issues += detect_chunk_violations(body)

    # Determine severity
    if detect_control_chars(text) or detect_binary(text):
        severity = "CRITICAL"
    elif detect_ocr_noise(body) or detect_broken_tables(body) or detect_heading_structure(body):
        severity = "WARN"
    elif content_chars < 200:
        severity = "LOW"
    elif detect_chunk_violations(body):
        severity = "CHUNK"
    else:
        severity = "OK"

    return {
        "path": str(fp),
        "title": fm.get("title", ""),
        "url": fm.get("url", ""),
        "scraped_by": fm.get("scraped_by", ""),
        "severity": severity,
        "issues": issues,
        "content_chars": content_chars,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

SEVERITY_ORDER = {"CRITICAL": 0, "WARN": 1, "LOW": 2, "CHUNK": 3, "OK": 4}


def run_audit(data_dir: Path, output_path: Path):
    md_files = sorted(data_dir.rglob("*.md"))
    print(f"Scanning {len(md_files)} markdown files under {data_dir} …\n")

    results = []
    counts = {"CRITICAL": 0, "WARN": 0, "LOW": 0, "CHUNK": 0, "OK": 0}

    for fp in md_files:
        r = audit_file(fp)
        results.append(r)
        counts[r["severity"]] += 1
        sym = {"CRITICAL": "✗", "WARN": "!", "LOW": "~", "CHUNK": "C", "OK": "✓"}[r["severity"]]
        if r["severity"] != "OK":
            print(f"  [{sym}] {fp.relative_to(data_dir)}  ({r['severity']})")
            for iss in r["issues"][:2]:
                print(f"       -> {iss}")

    results.sort(key=lambda x: SEVERITY_ORDER[x["severity"]])
    output_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")

    print("\n" + "=" * 70)
    print(f"  Audit complete — {data_dir}")
    print("=" * 70)
    print(f"  CRITICAL : {counts['CRITICAL']:4d}  control chars / binary garbage")
    print(f"  WARN     : {counts['WARN']:4d}  OCR noise / broken tables / missing headings")
    print(f"  LOW      : {counts['LOW']:4d}  stub / near-empty (<200 chars)")
    print(f"  CHUNK    : {counts['CHUNK']:4d}  sections exceed {CHUNK_SIZE*2} tokens")
    print(f"  OK       : {counts['OK']:4d}")
    print(f"  TOTAL    : {len(results):4d}")
    print("=" * 70)
    print(f"\nFull report → {output_path}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Audit DAU PWA data/ markdown quality")
    parser.add_argument("--data-dir", default="data",           help="Root data directory")
    parser.add_argument("--output",   default="audit_report.json", help="Output JSON path")
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    if not data_dir.is_dir():
        print(f"ERROR: {data_dir} not found")
        sys.exit(1)

    run_audit(data_dir, Path(args.output))
