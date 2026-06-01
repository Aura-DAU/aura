"""
fix_rag_issues.py
=================
Fixes all RAG-blocking issues in Team D's markdown data files.

Issues addressed (per review):
  1.  Empty orphaned bullet lines (`* ` or `  * ` with no content)
  2.  [Image Present: ...] placeholder text
  3.  _icon_ CSS artifact token before email/phone
  4.  displayNone JavaScript class text
  5.  `play stop` media control text
  6.  javascript:void(0) A-Z alphabet filter links
  7.  ??? garbled encoding (flag for manual re-scrape)
  8.  &amp; HTML entity not decoded
  9.  ?_ga=... Google Analytics session IDs stripped from URLs
  10. ## (H2) headings normalised to # (H1)
  11. Â\xa0 UTF-8 encoding corruption in faculty profiles (bulk fix)
  12. Relative /sites/default/files/ URLs -> absolute https://www.daiict.ac.in/...

Run from repo root:
    python "data/Team D/fix_rag_issues.py"
"""

import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = BASE  # madhav-data/ is the parent of this script's dir
# Adjust: script is in  data/Team D/   and data is in data/Team D/madhav-data/
MADHAV = os.path.join(BASE, "madhav-data")

ABSOLUTE_BASE = "https://www.daiict.ac.in"

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def read(path):
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        return fh.read()

def write(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)

def all_md(root):
    for dirpath, _, filenames in os.walk(root):
        for fn in filenames:
            if fn.endswith(".md"):
                yield os.path.join(dirpath, fn)

# ---------------------------------------------------------------------------
# fix functions
# ---------------------------------------------------------------------------

def fix_empty_bullets(text):
    """
    Issue 1: Delete lines that are purely an empty bullet ( `* ` or `  * ` ).
    Match lines consisting only of optional leading spaces, a `*`, and then
    only whitespace (no content after the asterisk).
    """
    return re.sub(r'(?m)^[ \t]*\*[ \t]*$\n?', '', text)


def fix_image_present(text):
    """
    Issue 2: Remove [Image Present: ...] placeholder tokens.
    Replace with empty string (removes the token completely).
    """
    return re.sub(r'\[Image Present:[^\]]*\]', '', text)


def fix_icon_token(text):
    """
    Issue 3: Remove _icon_ CSS artifact tokens.
    `_icon_[email]` -> `[email]`  (just strip the leading `_icon_`)
    """
    return re.sub(r'_icon_', '', text)


def fix_display_none(text):
    """
    Issue 4: Remove standalone `displayNone` lines (and _displayNone_ variants).
    Also strip `displayNone ` when it appears as a prefix in list items.
    """
    # Remove standalone displayNone lines
    text = re.sub(r'(?m)^_?displayNone_?[ \t]*$\n?', '', text)
    # Strip inline `displayNone ` prefix in list items: `* displayNone Foo` -> `* Foo`
    text = re.sub(r'(?m)^([ \t]*\*[ \t]*)displayNone[ \t]+', r'\1', text)
    # Strip standalone `displayNone` word anywhere in a line (not preceded by a letter)
    text = re.sub(r'\bdisplayNone\b', '', text)
    return text


def fix_play_stop(text):
    """
    Issue 5: Remove `play stop` media control lines.
    """
    return re.sub(r'(?m)^[ \t]*play stop[ \t]*$\n?', '', text)


def fix_js_void_alphabet(text):
    """
    Issue 6: Remove javascript:void(0) A-Z alphabet filter lines.
    Pattern: `  * [A](javascript:void(0))` or escaped variants.
    """
    # Match lines like:   * [A](javascript:void(0)) or [A](javascript:void\(0\))
    return re.sub(
        r'(?m)^[ \t]*\*[ \t]*\[[A-Z]\]\(javascript:void\\?\(0\\?\)\)[ \t]*$\n?',
        '',
        text
    )


def flag_garbled(text, path):
    """
    Issue 7: Flag ??? garbled encoding corruption (don't auto-fix, note for re-scrape).
    Returns (text, has_garbled) — text unchanged, logs a warning.
    """
    # Common garbled patterns: sequences of ??? or replacement chars
    if re.search(r'\?{3,}', text):
        print(f"  [WARN] Garbled ??? encoding found in: {path}")
        print(f"         Manual re-scrape recommended from /events/5622 (and similar).")
    return text


def fix_html_entities(text):
    """
    Issue 8: Decode &amp; HTML entities to & in body text.
    Only replace &amp; not inside markdown link URLs to avoid breaking them,
    but since these appear in display text this is safe to do universally.
    """
    return text.replace('&amp;', '&')


def fix_ga_urls(text):
    """
    Issue 9: Strip ?_ga=... (and &_ga=...) Google Analytics session params from URLs.
    Handles both ?_ga=... standalone and ?_ga=...&other=params cases.
    """
    # Strip ?_ga=<value> (possibly followed by &more_params)
    text = re.sub(r'\?_ga=[^)"\s]+', '', text)
    # Strip &_ga=<value> when _ga is not the first param
    text = re.sub(r'&_ga=[^)"\s]+', '', text)
    return text


def fix_headings(text):
    """
    Issue 10: Normalise ## headings to # (H2 -> H1) throughout.
    Only convert ## that are NOT already inside a code block.
    Strategy: process line by line, skip code fences.
    """
    lines = text.split('\n')
    in_fence = False
    result = []
    for line in lines:
        if line.strip().startswith('```'):
            in_fence = not in_fence
        if not in_fence and re.match(r'^##\s', line):
            line = line[1:]  # strip one leading #
        result.append(line)
    return '\n'.join(result)


def fix_xa0_encoding(text):
    """
    Issue 11: Remove Â\xa0 UTF-8 double-encoding corruption.
    The sequence Â\xa0 is a mis-decoded non-breaking space (U+00A0).
    Replace with a plain space.
    """
    # Â followed by \xa0 (non-breaking space) -> single space
    text = text.replace('Â\xa0', ' ')
    text = text.replace('\u00c2\u00a0', ' ')  # same in unicode escape form
    # Also fix standalone \xa0 -> regular space
    text = text.replace('\u00a0', ' ')
    return text


def fix_relative_urls(text):
    """
    Issue 12: Convert relative /sites/default/files/ URLs to absolute.
    Also handle other common relative paths that appear in markdown links.
    Only convert paths that start with / (not already absolute).
    Captures path AFTER the opening paren so the paren itself is not duplicated.
    """
    def absolutify(m):
        prefix = m.group(1)   # the `](` part
        url = m.group(2)      # the path starting with /
        # Only fix if it's a relative URL (starts with /) and not already absolute
        if url.startswith('/') and not url.startswith('//'):
            return f'{prefix}{ABSOLUTE_BASE}{url}'
        return m.group(0)

    # Match markdown link URLs: ]( /path...)
    # Group 1 = ]( , Group 2 = the /path
    text = re.sub(r'(\]\()(/[^)"\s]+)', absolutify, text)

    # Cleanup any double-paren artifacts (e.g. `url))` -> `url)`) that may have
    # been introduced by a previous run of this script or the scraper.
    text = re.sub(r'\)\)', ')', text)
    return text


# ---------------------------------------------------------------------------
# orchestration
# ---------------------------------------------------------------------------

FIXES = [
    ("Empty bullets",             fix_empty_bullets),
    ("[Image Present:] placeholders", fix_image_present),
    ("_icon_ tokens",             fix_icon_token),
    ("displayNone artifacts",     fix_display_none),
    ("play stop tokens",          fix_play_stop),
    ("javascript:void A-Z links", fix_js_void_alphabet),
    ("HTML &amp; entities",       fix_html_entities),
    ("GA session IDs in URLs",    fix_ga_urls),
    ("H2->H1 heading normalise",  fix_headings),
    ("Â\\xa0 encoding corruption", fix_xa0_encoding),
    ("Relative -> absolute URLs", fix_relative_urls),
]

def process_file(path):
    original = read(path)
    text = original

    # Apply flag-only check (issue 7, no mutation)
    flag_garbled(text, path)

    # Apply all mutating fixes
    for label, fn in FIXES:
        text = fn(text)

    if text != original:
        write(path, text)
        return True
    return False


def main():
    if not os.path.isdir(MADHAV):
        print(f"ERROR: madhav-data directory not found at {MADHAV}")
        sys.exit(1)

    changed = 0
    total = 0
    for path in all_md(MADHAV):
        total += 1
        rel = os.path.relpath(path, MADHAV)
        try:
            if process_file(path):
                changed += 1
                print(f"  [FIXED] {rel}")
        except Exception as e:
            print(f"  [ERROR] {rel}: {e}")

    print(f"\nDone. {changed}/{total} files modified.")
    print("\nReminder (Issue 7): Files with ??? garbled names need manual re-scrape from /events/5622")
    print("  - academics/people_overview.md")
    print("  - student_services/students_tab.md")


if __name__ == "__main__":
    main()
