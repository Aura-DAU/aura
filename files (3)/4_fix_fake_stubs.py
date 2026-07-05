#!/usr/bin/env python3
"""
4_fix_fake_stubs.py
-------------------
Finds every markdown file under data/ that contains the hallucination disclaimer:
  "This page's content could not be fully extracted during scraping."

For each file:
  1. Reads the `url` frontmatter field.
  2. Fetches the live URL and extracts real content with BeautifulSoup.
  3. Replaces the placeholder body with real content.
  4. If URL is dead/403/timeout -> sets extraction_status: "unreachable" and leaves
     an honest note.
  5. Social media domains (facebook, instagram, x.com, linkedin, youtube) ->
     sets extraction_status: "social_media_js_wall".

Usage:
  python "files (3)/4_fix_fake_stubs.py" --data data
"""

import argparse
import re
import sys
import time
from pathlib import Path

import requests
import yaml
from bs4 import BeautifulSoup

DISCLAIMER = "could not be fully extracted during scraping"

SOCIAL_DOMAINS = ("facebook.com", "instagram.com", "x.com", "linkedin.com", "youtube.com")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}

BOILERPLATE_STRINGS = [
    "Skip to main content",
    "Dhirubhai Ambani University",
    "Search form",
    "You are here",
    "Breadcrumb",
    "Main menu",
    "Footer menu",
    "Copyright",
    "Privacy Policy",
    "Website Policies",
]


def parse_frontmatter(content: str) -> tuple:
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
    body = content[match.end():]
    return meta, body


def build_frontmatter(meta: dict) -> str:
    lines = ["---"]
    for k, v in meta.items():
        if isinstance(v, list):
            lines.append(f"{k}: {v!r}")
        elif isinstance(v, str) and any(c in v for c in ':#{}[]|>&!%@`'):
            lines.append(f'{k}: "{v}"')
        elif isinstance(v, (bool, int, float)):
            lines.append(f"{k}: {v!r}")
        else:
            lines.append(f"{k}: {v}")
    lines.append("---")
    return "\n".join(lines) + "\n"


def extract_content(url: str) -> tuple:
    """
    Returns (status, content_or_error)
    status: "ok" | "unreachable" | "social_media_js_wall" | "empty"
    """
    if not url or url.strip() == "":
        return "unreachable", "No URL provided in frontmatter."

    if any(domain in url for domain in SOCIAL_DOMAINS):
        return "social_media_js_wall", None

    try:
        resp = requests.get(url, headers=HEADERS, timeout=15, allow_redirects=True)
    except requests.exceptions.ConnectionError as e:
        return "unreachable", f"Connection error: {e}"
    except requests.exceptions.Timeout:
        return "unreachable", "Request timed out after 15s."
    except Exception as e:
        return "unreachable", f"Unexpected error: {e}"

    if resp.status_code == 404:
        return "unreachable", f"HTTP 404 Not Found: {url}"
    if resp.status_code in (403, 401):
        return "unreachable", f"HTTP {resp.status_code} Access Denied: {url}"
    if resp.status_code >= 400:
        return "unreachable", f"HTTP {resp.status_code}: {url}"

    soup = BeautifulSoup(resp.text, "html.parser")

    # Remove nav, footer, script, style, sidebar
    for tag in soup.find_all(["nav", "footer", "script", "style", "header"]):
        tag.decompose()
    for cls in ["sidebar", "breadcrumb", "menu", "search-form", "block-search"]:
        for el in soup.find_all(class_=re.compile(cls, re.I)):
            el.decompose()

    # Try main content selectors in priority order
    main = (
        soup.find("main")
        or soup.find(class_=re.compile(r"content|main|article|page-content", re.I))
        or soup.find("article")
        or soup.find("body")
    )

    if not main:
        return "empty", "Could not find main content block on page."

    # Extract text
    paragraphs = []
    for el in main.find_all(["h1", "h2", "h3", "h4", "p", "li", "td", "th"]):
        text = el.get_text(separator=" ", strip=True)
        # Skip boilerplate lines
        if any(bp.lower() in text.lower() for bp in BOILERPLATE_STRINGS):
            continue
        if len(text) > 15:
            paragraphs.append(text)

    content = "\n\n".join(paragraphs)
    words = content.split()
    if len(words) < 30:
        return "empty", f"Only {len(words)} words extracted after boilerplate removal."

    return "ok", content


def content_to_markdown(raw_text: str) -> str:
    """Convert extracted paragraphs to clean markdown."""
    lines = []
    for para in raw_text.split("\n\n"):
        para = para.strip()
        if not para:
            continue
        lines.append(para)
    return "\n\n".join(lines)


def fix_file(filepath: Path, dry_run: bool = False) -> dict:
    content = filepath.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(content)
    url = str(meta.get("url", "") or "").strip()
    title = str(meta.get("title", filepath.stem)).strip()

    print(f"\n{'='*70}")
    print(f"FILE: {filepath}")
    print(f"URL:  {url or '(none)'}")
    print(f"\n--- BEFORE (first 20 lines of body) ---")
    body_lines = body.strip().split("\n")
    for line in body_lines[:20]:
        print(line)
    if len(body_lines) > 20:
        print(f"  ... ({len(body_lines) - 20} more lines)")

    status, fetched = extract_content(url)

    if status == "social_media_js_wall":
        platform = next((d for d in SOCIAL_DOMAINS if d in url), "social media")
        new_body = (
            f"# {title}\n\n"
            f"This file links to an official DA-IICT social media account.\n\n"
            f"**Platform URL:** {url}\n\n"
            f"Social media pages require JavaScript execution and authentication "
            f"and cannot be scraped via standard HTTP requests. "
            f"Please visit the URL directly for up-to-date content.\n"
        )
        meta["extraction_status"] = "social_media_js_wall"
        result_label = f"SOCIAL_MEDIA_JS_WALL ({platform})"

    elif status == "unreachable":
        new_body = (
            f"# {title}\n\n"
            f"> **Note:** The source URL for this page could not be reached during extraction.\n"
            f">\n"
            f"> - URL attempted: {url or '(none)'}\n"
            f"> - Error: {fetched}\n\n"
            f"Please verify the source URL is still active and re-run extraction if needed.\n"
        )
        meta["extraction_status"] = "unreachable"
        result_label = f"UNREACHABLE -- {fetched}"

    elif status == "empty":
        new_body = (
            f"# {title}\n\n"
            f"> **Note:** The page was reachable but yielded fewer than 30 words of "
            f"content after boilerplate removal.\n"
            f">\n"
            f"> - URL: {url}\n"
            f"> - Details: {fetched}\n\n"
            f"The page may be dynamically rendered or consist primarily of images/media.\n"
        )
        meta["extraction_status"] = "sparse_content"
        result_label = f"SPARSE -- {fetched}"

    else:
        # status == "ok"
        md_content = content_to_markdown(fetched)
        new_body = f"# {title}\n\n{md_content}\n"
        meta["extraction_status"] = "live_fetched"
        # Remove the hallucination marker — this is now real content
        if "fixes_applied" in meta:
            fixes = meta["fixes_applied"]
            if isinstance(fixes, list) and "STUB_EMPTY" in fixes:
                fixes.remove("STUB_EMPTY")
            if not fixes:
                del meta["fixes_applied"]
        result_label = f"LIVE FETCHED -- {len(fetched.split())} words"

    meta["last_fixed"] = "2026-07-05"

    new_content = build_frontmatter(meta) + "\n" + new_body

    print(f"\n--- AFTER (first 20 lines of new body) ---")
    new_body_lines = new_body.strip().split("\n")
    for line in new_body_lines[:20]:
        print(line)
    last_10 = new_body_lines[-10:] if len(new_body_lines) > 20 else []
    if last_10:
        print(f"  ... ({len(new_body_lines) - 20} more lines) ...")
        for line in last_10:
            print(line)

    print(f"\n>>> RESULT: {result_label}")

    if not dry_run:
        filepath.write_text(new_content, encoding="utf-8")

    return {
        "file": str(filepath),
        "url": url,
        "status": status,
        "detail": fetched if status != "ok" else f"{len(fetched.split())} words fetched",
    }


def main():
    parser = argparse.ArgumentParser(description="Fix fake stub files with live content.")
    parser.add_argument("--data", default="data", help="Path to the data directory.")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing.")
    args = parser.parse_args()

    data_dir = Path(args.data)
    if not data_dir.exists():
        print(f"ERROR: data directory not found: {data_dir}", file=sys.stderr)
        sys.exit(1)

    # Find all files with the disclaimer
    stub_files = sorted([
        f for f in data_dir.rglob("*.md")
        if DISCLAIMER in f.read_text(encoding="utf-8", errors="replace")
    ])

    print(f"Found {len(stub_files)} files with hallucination disclaimer.")
    if args.dry_run:
        print("DRY RUN -- no files will be modified.\n")

    results = {
        "ok": [],
        "unreachable": [],
        "social_media_js_wall": [],
        "sparse_content": [],
        "errors": [],
    }

    for i, filepath in enumerate(stub_files, 1):
        print(f"\n[{i}/{len(stub_files)}] Processing: {filepath.relative_to(data_dir)}")
        try:
            r = fix_file(filepath, dry_run=args.dry_run)
            bucket = r["status"] if r["status"] in results else "ok"
            results[bucket].append(r)
        except Exception as e:
            print(f"  ERROR processing {filepath}: {e}")
            results["errors"].append({"file": str(filepath), "error": str(e)})
        # Polite delay between requests
        time.sleep(0.5)

    print(f"\n{'='*70}")
    print("FINAL SUMMARY")
    print(f"{'='*70}")
    print(f"  Live fetched (ok)          : {len(results['ok'])}")
    print(f"  Unreachable (marked)       : {len(results['unreachable'])}")
    print(f"  Social media JS wall       : {len(results['social_media_js_wall'])}")
    print(f"  Sparse content (marked)    : {len(results['sparse_content'])}")
    print(f"  Script errors              : {len(results['errors'])}")
    total = sum(len(v) for v in results.values())
    print(f"  Total processed            : {total}")


if __name__ == "__main__":
    main()
