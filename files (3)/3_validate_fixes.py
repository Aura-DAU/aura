"""
AURA Fix Validator
==================
After running 2_reextract_files.py, this script re-audits every file
that was fixed (according to fix_log.json) and produces a before/after
comparison showing which issues were resolved and which remain.

Also validates:
  - No sections exceed 256 tokens after fixing
  - Frontmatter is intact
  - H2/H3 structure is present where needed
  - No garbled characters remain

Usage:
    python 3_validate_fixes.py --data ../../data --audit audit_report

Output:
    audit_report/validation_report.json   — before vs after per file
    audit_report/validation_summary.txt   — human-readable summary
"""

import json
import sys
import re
import argparse
from pathlib import Path
from datetime import datetime

import yaml

CHUNK_SIZE = 256
CTRL_CHAR_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
HEADING_RE   = re.compile(r"^(#{1,6})\s+(.+)", re.MULTILINE)


def estimate_tokens(text: str) -> int:
    return int(len(text.split()) * 1.3)


def parse_frontmatter(content: str) -> tuple[dict, str]:
    content = content.lstrip("\ufeff").replace("\r\n", "\n")
    match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
    if not match:
        return {}, content
    try:
        meta = yaml.safe_load(match.group(1)) or {}
        if not isinstance(meta, dict):
            meta = {}
    except Exception:
        meta = {}
    return meta, content[match.end():]


def get_issues(content: str) -> list[str]:
    """Re-run the same checks as 1_audit_files.py and return issue list."""
    meta, body = parse_frontmatter(content)
    issues = []
    main_content = body.strip()
    lines = main_content.split("\n")

    # CRLF
    if "\r\n" in content:
        issues.append("CRLF_ENCODING")

    # Frontmatter
    for f in ["title", "url", "category"]:
        if not meta.get(f):
            issues.append("FRONTMATTER_BROKEN")
            break

    # Stub
    stripped = re.sub(r"^#{1,6}\s+.*$", "", main_content, flags=re.MULTILINE)
    stripped = re.sub(r"^---+$", "", stripped, flags=re.MULTILINE).strip()
    if len(stripped.split()) < 30:
        issues.append("STUB_EMPTY")

    # Garbled
    garbled = [l for l in lines if CTRL_CHAR_RE.search(l)]
    if len(garbled) > 5:
        issues.append("GARBLED_ENCODING")

    # OCR noise
    OCR_NOISE = [
        re.compile(r"\s;\s"),
        re.compile(r"\bSaati\b"),
        re.compile(r"\boe\b"),
        re.compile(r"[A-Za-z]{2,}\d[A-Za-z]{2,}"),
    ]
    for pat in OCR_NOISE:
        if len(pat.findall(main_content)) >= 3:
            issues.append("OCR_NOISE")
            break

    # Excel bad headers
    if len(re.findall(r"Unnamed:\s*\d+", main_content)) >= 3:
        issues.append("EXCEL_BAD_HEADERS")

    # Heading missing
    headings = HEADING_RE.findall(main_content)
    h23_count = sum(1 for level, _ in headings if len(level) in (2, 3))
    word_count = len(main_content.split())
    if word_count > 150 and h23_count == 0:
        issues.append("HEADING_MISSING")

    # Chunk overflow
    sections = _extract_sections(main_content)
    for sec in sections:
        if estimate_tokens(sec["content"]) > CHUNK_SIZE:
            issues.append("CHUNK_OVERFLOW")
            break

    return list(set(issues))


def _extract_sections(body: str) -> list[dict]:
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


def main():
    ap = argparse.ArgumentParser(description="AURA Fix Validator")
    ap.add_argument("--data",  default="../../data",   help="Path to data/ directory")
    ap.add_argument("--audit", default="audit_report", help="Path to audit_report/ directory")
    args = ap.parse_args()

    data_root     = Path(args.data).resolve()
    audit_dir     = Path(args.audit)
    fix_log_path  = audit_dir / "fix_log.json"
    orig_audit    = audit_dir / "audit_results.json"
    out_json      = audit_dir / "validation_report.json"
    out_txt       = audit_dir / "validation_summary.txt"

    if not fix_log_path.exists():
        print(f"[ERROR] fix_log.json not found: {fix_log_path}")
        print("        Run 2_reextract_files.py first.")
        sys.exit(1)

    with open(fix_log_path, encoding="utf-8") as f:
        fix_log = json.load(f)

    with open(orig_audit, encoding="utf-8") as f:
        orig_audit_data = json.load(f)

    orig_by_file = {r["file"]: r for r in orig_audit_data["results"]}

    print(f"\n{'─'*60}")
    print(f"  AURA Fix Validator")
    print(f"  Validating {len(fix_log['logs'])} fixed files")
    print(f"{'─'*60}\n")

    validations = []
    resolved_total   = 0
    remaining_total  = 0
    new_issues_total = 0

    for log_entry in fix_log["logs"]:
        fname   = log_entry["file"]
        md_path = data_root / fname

        before_issues = orig_by_file.get(fname, {}).get("issues", [])
        entry = {
            "file":          fname,
            "fix_status":    log_entry["status"],
            "fixes_applied": log_entry.get("fixes_applied", []),
            "before_issues": before_issues,
            "after_issues":  [],
            "resolved":      [],
            "remaining":     [],
            "new_issues":    [],
            "validation":    "unknown",
        }

        if log_entry["status"] in ("missing", "error", "skipped", "dry-run"):
            entry["validation"] = log_entry["status"]
            validations.append(entry)
            continue

        if not md_path.exists():
            entry["validation"] = "missing"
            validations.append(entry)
            continue

        try:
            content     = md_path.read_text(encoding="utf-8", errors="replace")
            after_issues = get_issues(content)
        except Exception as e:
            entry["validation"] = f"read_error: {e}"
            validations.append(entry)
            continue

        before_set = set(before_issues)
        after_set  = set(after_issues)

        resolved   = sorted(before_set - after_set)
        remaining  = sorted(before_set & after_set)
        new_issues = sorted(after_set - before_set)

        entry["after_issues"]  = sorted(after_set)
        entry["resolved"]      = resolved
        entry["remaining"]     = remaining
        entry["new_issues"]    = new_issues

        resolved_total   += len(resolved)
        remaining_total  += len(remaining)
        new_issues_total += len(new_issues)

        if not remaining and not new_issues:
            entry["validation"] = "✅ CLEAN"
        elif new_issues:
            entry["validation"] = "⚠️ NEW ISSUES"
        elif remaining:
            entry["validation"] = "🟡 PARTIAL"
        else:
            entry["validation"] = "✅ CLEAN"

        icon = entry["validation"][:2]
        print(f"  {icon}  {fname}")
        if resolved:
            print(f"       RESOLVED  : {', '.join(resolved)}")
        if remaining:
            print(f"       REMAINING : {', '.join(remaining)}")
        if new_issues:
            print(f"       NEW       : {', '.join(new_issues)}")

        validations.append(entry)

    # ── Stats ─────────────────────────────────────────────────────────────────
    clean   = sum(1 for v in validations if "CLEAN"   in v.get("validation",""))
    partial = sum(1 for v in validations if "PARTIAL" in v.get("validation",""))
    broken  = sum(1 for v in validations if "NEW"     in v.get("validation",""))
    errored = sum(1 for v in validations if "error"   in v.get("validation",""))

    print(f"\n{'─'*60}")
    print("  VALIDATION SUMMARY")
    print(f"{'─'*60}")
    print(f"  ✅ Fully clean    : {clean}")
    print(f"  🟡 Partial fix    : {partial}")
    print(f"  ⚠️  New issues     : {broken}")
    print(f"  ❌ Errors         : {errored}")
    print(f"\n  Issues resolved  : {resolved_total}")
    print(f"  Issues remaining : {remaining_total}")
    print(f"  Issues introduced: {new_issues_total}")

    # ── Save JSON ─────────────────────────────────────────────────────────────
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump({
            "generated": datetime.now().isoformat(),
            "summary": {
                "clean": clean, "partial": partial,
                "new_issues": broken, "errors": errored,
                "issues_resolved": resolved_total,
                "issues_remaining": remaining_total,
                "issues_introduced": new_issues_total,
            },
            "validations": validations,
        }, f, indent=2, ensure_ascii=False)

    # ── Save human-readable txt ───────────────────────────────────────────────
    lines = [
        "AURA Fix Validation Report",
        f"Generated: {datetime.now().isoformat()}",
        "=" * 60,
        f"Fully clean     : {clean}",
        f"Partial fix     : {partial}",
        f"New issues      : {broken}",
        f"Errors          : {errored}",
        f"Issues resolved : {resolved_total}",
        f"Issues remaining: {remaining_total}",
        "",
        "FILES NEEDING FURTHER ATTENTION:",
        "-" * 60,
    ]
    for v in validations:
        if v.get("remaining") or v.get("new_issues"):
            lines.append(f"  {v['file']}")
            if v["remaining"]:
                lines.append(f"    Still broken : {', '.join(v['remaining'])}")
            if v["new_issues"]:
                lines.append(f"    New problems : {', '.join(v['new_issues'])}")
    with open(out_txt, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"\n  Reports saved:")
    print(f"    {out_json}")
    print(f"    {out_txt}")
    print(f"{'─'*60}\n")


if __name__ == "__main__":
    main()
