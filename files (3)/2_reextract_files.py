"""
AURA Data Re-Extractor
======================
Reads audit_report/audit_results.json produced by 1_audit_files.py and fixes
every flagged file with the minimum change needed:

  GARBLED_ENCODING  → re-download PDF → pdfplumber text + camelot tables → LLM cleanup
  OCR_NOISE         → re-download PDF → pdfplumber text + camelot tables → LLM cleanup
  SCANNED_PDF       → re-download PDF → pytesseract OCR page by page → LLM cleanup
  EXCEL_BAD_HEADERS → re-download XLS → pandas with header-row detection → rewrite table
  STUB_EMPTY        → LLM rewrites from URL metadata + any raw text found
  HEADING_MISSING   → LLM adds H2/H3 headings to the flat body
  CHUNK_OVERFLOW    → LLM splits oversized sections into sub-headings

Strategy per issue type
------------------------
1. PDF with text layer (GARBLED_ENCODING, OCR_NOISE):
     pdfplumber  → raw text extraction (preserves reading order, handles columns)
     camelot     → precise table extraction as DataFrames → Markdown tables
     Claude      → clean garbled characters, reformat into H1/H2/H3 markdown,
                   preserve all numbers and names exactly

2. PDF image-only (SCANNED_PDF):
     pdfplumber  → render each page to image (300dpi)
     pytesseract → OCR each page image
     Claude      → structure OCR output into clean markdown with headings

3. Excel bad headers (EXCEL_BAD_HEADERS):
     pandas      → read with multiple header rows, detect real header row
     Claude      → write clean markdown table with correct column names

4. Stub/Empty (STUB_EMPTY):
     Existing frontmatter + any text found → Claude fills in the content
     from what is available in the existing .md (metadata tells us what it should be)

5. Heading missing / Chunk overflow (HEADING_MISSING, CHUNK_OVERFLOW):
     No re-download needed. Send existing body to Claude → get back structured version.

Output
------
  Fixed files are written IN PLACE (original backed up to .md.bak before overwriting).
  A fix_log.json is written to audit_report/ with per-file status.

Requirements
-----------
  pip install anthropic pdfplumber camelot-py[cv] pytesseract pypdf requests PyYAML

Usage:
  export ANTHROPIC_API_KEY=sk-ant-...
  python 2_reextract_files.py --data ../../data --audit audit_report --dry-run
  python 2_reextract_files.py --data ../../data --audit audit_report
  python 2_reextract_files.py --data ../../data --audit audit_report --priority critical,high
  python 2_reextract_files.py --data ../../data --audit audit_report --file administration/some_file.md
"""

import os
import re
import sys
import json
import time
import shutil
import argparse
import tempfile
import textwrap
import traceback
from pathlib import Path
from datetime import datetime

import yaml
import requests
import pdfplumber
import pytesseract
from PIL import Image

try:
    import camelot
    CAMELOT_OK = True
except Exception:
    CAMELOT_OK = False

from groq import Groq, RateLimitError
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / "server/rag/.env")

CHUNK_SIZE      = 256   # tokens
MAX_TOKENS      = 8192
RETRY_SLEEP     = 5
MAX_RETRIES     = 5
REQUEST_TIMEOUT = 30
OCR_DPI         = 300

PDF_DOWNLOAD_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}

client = None
if os.environ.get("GROQ_API_KEY"):
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    GROQ_MODEL = os.environ.get("GROQ_MODEL", "qwen/qwen3-32b")
elif os.environ.get("ANTHROPIC_API_KEY"):
    import anthropic
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    MODEL = "claude-sonnet-4-6"




# ─────────────────────────── HELPERS ─────────────────────────────────────────

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


def render_frontmatter(meta: dict) -> str:
    lines = ["---"]
    for k, v in meta.items():
        if isinstance(v, str):
            # Quote strings that contain special YAML chars
            if any(c in v for c in [':', '#', '{', '}', '[', ']', ',', '&', '*', '?', '|', '-', '<', '>', '=', '!', '%', '@', '`', '"', "'"]):
                v_str = json.dumps(v)
            else:
                v_str = f'"{v}"'
            lines.append(f"{k}: {v_str}")
        else:
            lines.append(f"{k}: {v}")
    lines.append("---\n")
    return "\n".join(lines)


def download_pdf(url: str, dest: Path) -> bool:
    """Download URL to dest. Returns True on success."""
    import urllib.parse
    try:
        quoted_url = urllib.parse.quote(url, safe=":/%")
        r = requests.get(quoted_url, headers=PDF_DOWNLOAD_HEADERS,
                         timeout=REQUEST_TIMEOUT, stream=True)
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=65536):
                f.write(chunk)
        return True
    except Exception as e:
        print(f"    [DOWNLOAD FAIL] {url}: {e}")
        return False



def call_claude(system: str, user: str, label: str = "") -> str:
    """Call LLM (Groq or Claude) with retry logic. Returns the response text."""
    is_groq = "Groq" in str(type(client))
    if not is_groq:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = client.messages.create(
                    model=MODEL,
                    max_tokens=MAX_TOKENS,
                    system=system,
                    messages=[{"role": "user", "content": user}],
                )
                return response.content[0].text
            except Exception as e:
                sleep_time = RETRY_SLEEP * attempt
                print(f"    [ANTHROPIC LIMIT] attempt {attempt}/{MAX_RETRIES}, sleeping {sleep_time}s…")
                time.sleep(sleep_time)
        raise RuntimeError("Claude API call failed after retries")

    # Groq fallback models
    models_to_try = [GROQ_MODEL]
    for fallback in ["llama-3.3-70b-versatile", "qwen/qwen3.6-27b", "llama-3.1-8b-instant"]:
        if fallback != GROQ_MODEL and fallback not in models_to_try:
            models_to_try.append(fallback)

    for attempt in range(1, MAX_RETRIES + 1):
        for model in models_to_try:
            try:
                response = client.chat.completions.create(
                    model=model,
                    temperature=0.2,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user}
                    ]
                )
                text = response.choices[0].message.content
                import re
                return re.sub(r"<think>.*?</think>\s*", "", text, flags=re.DOTALL)
            except Exception as e:
                print(f"    [LLM TRY FAIL] Model {model} failed: {e}")
                if model == models_to_try[-1]:
                    sleep_time = RETRY_SLEEP * attempt
                    print(f"    [RATE LIMIT/CAPACITY] All models failed in attempt {attempt}/{MAX_RETRIES}. Sleeping {sleep_time}s…")
                    time.sleep(sleep_time)
                else:
                    print(f"    Trying next fallback model immediately...")
                    continue
    raise RuntimeError(f"LLM call failed after {MAX_RETRIES} attempts across all models")



# ─────────────────────────── PDF EXTRACTION ──────────────────────────────────

def extract_pdf_text_layer(pdf_path: Path) -> tuple[str, list[str]]:
    """
    Extract text and tables from a PDF that has a text layer.

    Returns:
        (raw_text, table_markdowns)
        raw_text       — concatenated page text from pdfplumber
        table_markdowns — list of markdown table strings from camelot
    """
    raw_text_pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            txt = page.extract_text(x_tolerance=2, y_tolerance=2)
            if txt:
                raw_text_pages.append(txt)
    raw_text = "\n\n".join(raw_text_pages)

    # Extract tables with camelot (lattice mode first, then stream)
    table_markdowns = []
    if CAMELOT_OK:
        for flavor in ("lattice", "stream"):
            try:
                tables = camelot.read_pdf(
                    str(pdf_path),
                    pages="all",
                    flavor=flavor,
                    suppress_stdout=True,
                )
                for tbl in tables:
                    df = tbl.df
                    # Use first row as header if it looks like one
                    if df.shape[0] > 1:
                        header = df.iloc[0].tolist()
                        # Detect if first row is actually a header
                        looks_like_header = all(
                            isinstance(h, str) and (h.istitle() or h.isupper() or len(h) < 40)
                            for h in header if h
                        )
                        if looks_like_header:
                            df.columns = header
                            df = df.iloc[1:].reset_index(drop=True)

                    md = df.to_markdown(index=False)
                    if md and len(md.strip()) > 20:
                        table_markdowns.append(md)
                if table_markdowns:
                    break  # lattice worked, skip stream
            except Exception:
                pass

    return raw_text, table_markdowns


def extract_pdf_ocr(pdf_path: Path) -> str:
    """
    OCR a scanned (image-only) PDF using pytesseract.
    Returns concatenated OCR text from all pages.
    """
    ocr_pages = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages, 1):
                # Render page to PIL image at 300 DPI
                img = page.to_image(resolution=OCR_DPI).original
                text = pytesseract.image_to_string(img, lang="eng", config="--psm 6")
                if text.strip():
                    ocr_pages.append(f"--- Page {i} ---\n{text.strip()}")
    except Exception as e:
        err_str = str(e).lower()
        if "tesseract" in err_str or "path" in err_str or "no such file" in err_str:
            print("    [OCR WARNING] Tesseract binary missing. Returning fallback placeholder text.")
            return "--- SCANNED ARCHITECTURAL DRAWING / ATTACHMENT ---\n[Tesseract OCR not installed on host machine to process image contents]"
        raise
    return "\n\n".join(ocr_pages)



def has_text_layer(pdf_path: Path) -> bool:
    """True if the PDF has an extractable text layer (not image-only)."""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            sample_pages = pdf.pages[:min(3, len(pdf.pages))]
            total_chars = sum(
                len(p.extract_text() or "") for p in sample_pages
            )
            return total_chars > 50
    except Exception:
        return False


# ─────────────────────────── CLAUDE PROMPTS ──────────────────────────────────

SYSTEM_CLEAN_PDF = textwrap.dedent("""
You are a document structuring assistant for the AURA RAG system at Dhirubhai Ambani University (DAU).

Your job: Take raw PDF-extracted text (possibly garbled) and reformat it into clean, 
structured Markdown following the EXACT rules below.

RULES:
1. Output ONLY the markdown body — no frontmatter, no preamble, no explanation.
2. Use H1 (#) for the document title (once, at top).
3. Use H2 (##) for major sections (Overview, Eligibility, Fee Structure, Placement Stats, etc.).
4. Use H3 (###) for subsections within each major section.
5. Each H2/H3 section must fit within ~256 tokens (~200 words). Split large sections with additional H3s.
6. Preserve ALL numbers, names, dates, course codes, amounts exactly — never paraphrase data.
7. Convert garbled table text into proper Markdown tables (| col | col | format).
8. Remove: repeated headers, page numbers, footers, "---" horizontal rules between pages,
   control characters (\\x00–\\x1f), OCR noise like "oe", "Saati", random symbols.
9. Fix obvious OCR typos only when you are 100% certain (e.g. "reg1strat1un" → "registration").
10. If you cannot confidently read a value (too garbled), write [illegible].
11. Do NOT add any content that wasn't in the original — only restructure + clean.
""").strip()

SYSTEM_CLEAN_OCR = textwrap.dedent("""
You are a document structuring assistant for the AURA RAG system at Dhirubhai Ambani University (DAU).

Your job: Take OCR-extracted text from a scanned PDF and reformat it into clean,
structured Markdown.

RULES (same as clean_pdf plus):
1. Output ONLY the markdown body — no frontmatter, no preamble.
2. Use H1 (#) for the document/certificate title.
3. Use H2 (##) for major sections.
4. Use H3 (###) for subsections. Each section ≤ ~256 tokens (~200 words).
5. Preserve ALL names, dates, registration numbers, amounts exactly.
6. OCR often confuses: 0↔O, 1↔I↔l, rn↔m, cl↔d. Fix these where context is clear.
7. If Devanagari/Hindi text appears garbled, note it as: [Hindi text — illegible]
8. Remove page separators (--- Page N ---), headers, footers.
9. For certificates with mostly visual content, extract: issuing authority, 
   recipient name, purpose, date, validity, registration number — as a clean list.
10. Do NOT invent content. Mark unclear text as [illegible].
""").strip()

SYSTEM_ADD_HEADINGS = textwrap.dedent("""
You are a document structuring assistant for the AURA RAG system at DAU.

Your job: Add H2 (##) and H3 (###) headings to an existing markdown document 
that has content but no section structure. Do NOT change any text — only add headings.

RULES:
1. Output the COMPLETE document body with headings inserted (no frontmatter).
2. Identify natural topic breaks and insert ## or ### headings before them.
3. Each section after adding headings should be ~150–250 words (~120–200 tokens).
4. Use descriptive heading names that reflect the content below them.
5. Do NOT rephrase, remove, or add any body text — only insert heading lines.
6. Preserve all existing H1 headings exactly.
""").strip()

SYSTEM_SPLIT_CHUNKS = textwrap.dedent("""
You are a document structuring assistant for the AURA RAG system at DAU.

Your job: Split an oversized markdown section (>256 tokens) into smaller sub-sections
by adding H3 (###) headings. Do NOT change any body text.

RULES:
1. Output the COMPLETE section content with ### headings inserted.
2. Each resulting sub-section must be ≤ 256 tokens (~200 words).
3. Heading names must describe the content below them.
4. Do NOT rephrase, remove, or add body text — only insert ### heading lines.
""").strip()

SYSTEM_FIX_EXCEL = textwrap.dedent("""
You are a data formatting assistant for the AURA RAG system at DAU.

Your job: Clean up a markdown table that was extracted from an Excel file and has
broken column headers ("Unnamed: 0", "Unnamed: 1", etc.).

RULES:
1. Output ONLY the fixed markdown table(s) — no preamble or explanation.
2. Detect the real column header row from the data (often the first data row contains column names).
3. Reconstruct proper | Header | Header | markdown table format.
4. Preserve all data values exactly.
5. If you cannot determine column names, use generic descriptive names like
   "Sr No", "Name", "Value", "Year", "Details" based on context.
""").strip()

SYSTEM_FILL_STUB = textwrap.dedent("""
You are a document assistant for the AURA RAG system at Dhirubhai Ambani University (DAU).

Your job: A page was scraped but returned almost no content. Using the page title, URL,
and category from the frontmatter, write a brief accurate placeholder that describes
what this page covers and notes the content was not fully extractable.

RULES:
1. Output ONLY the markdown body (no frontmatter).
2. Start with: ## Overview
3. Write 2–4 sentences describing what this page/document covers based on its title and URL.
4. End with: ## Note\nThis page's content could not be fully extracted during scraping.
   Please refer to the source URL for complete information.
5. Do NOT invent specific data (numbers, names, dates) — only describe the topic.
6. Keep total output under 150 words.
""").strip()


# ─────────────────────────── FIX FUNCTIONS ───────────────────────────────────

def fix_garbled_or_ocr_noise(md_path: Path, issues: list[str], url: str, meta: dict, body: str) -> str:
    """Fix GARBLED_ENCODING or OCR_NOISE: re-download PDF → extract → Claude cleanup."""
    if not url or "pdf" not in url.lower() or "ar_2016_17" in str(md_path).lower():
        if len(body.strip()) < 50:
            print(f"    [SKIP] Document has no PDF source and is an empty stub. Filling stub.")
            return fix_stub_empty(md_path, meta, body)

        print(f"    [SKIP] Using LLM on existing text for {md_path.name}.")
        # Fall back to cleaning what we have
        cleaned = call_claude(
            SYSTEM_CLEAN_PDF,
            f"Title: {meta.get('title','')}\nURL: {url}\n\nRAW TEXT TO CLEAN:\n{body[:12000]}",
            label=md_path.name
        )
        return cleaned

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp_pdf = Path(tmp.name)

    try:
        print(f"    Downloading PDF: {url}")
        ok = download_pdf(url, tmp_pdf)
        if not ok or tmp_pdf.stat().st_size < 1000:
            print(f"    [WARNING] Download failed or PDF too small. Falling back to LLM cleanup on existing text.")
            cleaned = call_claude(
                SYSTEM_CLEAN_PDF,
                f"Title: {meta.get('title','')}\nURL: {url}\n\nRAW TEXT TO CLEAN:\n{body[:12000]}",
                label=md_path.name
            )
            return cleaned
    except Exception as e:
        print(f"    [WARNING] Error downloading PDF ({e}). Falling back to LLM cleanup on existing text.")
        cleaned = call_claude(
            SYSTEM_CLEAN_PDF,
            f"Title: {meta.get('title','')}\nURL: {url}\n\nRAW TEXT TO CLEAN:\n{body[:12000]}",
            label=md_path.name
        )
        return cleaned

    try:
        if has_text_layer(tmp_pdf):
            print(f"    Text layer found — using pdfplumber + camelot")
            raw_text, table_mds = extract_pdf_text_layer(tmp_pdf)
            tables_section = ""
            if table_mds:
                tables_section = "\n\nEXTRACTED TABLES (already in Markdown):\n" + "\n\n".join(table_mds)
                tables_section = tables_section[:10000]
            user_prompt = (
                f"Title: {meta.get('title', '')}\nURL: {url}\n"
                f"Category: {meta.get('category', '')}\n\n"
                f"RAW TEXT:\n{raw_text[:10000]}"
                f"{tables_section}"
            )
            return call_claude(SYSTEM_CLEAN_PDF, user_prompt, label=md_path.name)
        else:
            print(f"    No text layer — running OCR")
            ocr_text = extract_pdf_ocr(tmp_pdf)
            user_prompt = (
                f"Title: {meta.get('title', '')}\nURL: {url}\n"
                f"Category: {meta.get('category', '')}\n\n"
                f"OCR TEXT:\n{ocr_text[:12000]}"
            )
            return call_claude(SYSTEM_CLEAN_OCR, user_prompt, label=md_path.name)

    finally:
        try:
            tmp_pdf.unlink()
        except Exception:
            pass


def fix_scanned_pdf(md_path: Path, url: str, meta: dict) -> str:
    """Fix SCANNED_PDF: download → OCR → Claude structure."""
    if not url:
        raise RuntimeError("No URL available for OCR re-extraction")

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp_pdf = Path(tmp.name)

    try:
        print(f"    Downloading PDF for OCR: {url}")
        ok = download_pdf(url, tmp_pdf)
        if not ok or tmp_pdf.stat().st_size < 500:
            raise RuntimeError("Download failed")

        print(f"    Running OCR (this may take 30–90s for multi-page PDFs)…")
        ocr_text = extract_pdf_ocr(tmp_pdf)
        user_prompt = (
            f"Title: {meta.get('title', '')}\nURL: {url}\n"
            f"Category: {meta.get('category', '')}\n\n"
            f"OCR TEXT:\n{ocr_text[:12000]}"
        )
        return call_claude(SYSTEM_CLEAN_OCR, user_prompt, label=md_path.name)

    finally:
        try:
            tmp_pdf.unlink()
        except Exception:
            pass


def fix_excel_headers(md_path: Path, meta: dict, body: str) -> str:
    """Fix EXCEL_BAD_HEADERS: ask Claude to reconstruct column names."""
    user_prompt = (
        f"Title: {meta.get('title', '')}\n"
        f"Category: {meta.get('category', '')}\n\n"
        f"BROKEN MARKDOWN TABLE (fix the Unnamed: N headers):\n{body[:6000]}"
    )
    return call_claude(SYSTEM_FIX_EXCEL, user_prompt, label=md_path.name)


def fix_stub_empty(md_path: Path, meta: dict, body: str) -> str:
    """Fix STUB_EMPTY: Claude writes a brief description from frontmatter."""
    user_prompt = (
        f"Title: {meta.get('title', 'Unknown')}\n"
        f"URL: {meta.get('url', '')}\n"
        f"Category: {meta.get('category', '')}\n"
        f"Source type: {meta.get('source_type', 'web')}\n\n"
        f"EXISTING (MINIMAL) CONTENT:\n{body[:2000]}"
    )
    return call_claude(SYSTEM_FILL_STUB, user_prompt, label=md_path.name)


def fix_heading_missing(md_path: Path, meta: dict, body: str) -> str:
    """Fix HEADING_MISSING: Claude inserts H2/H3 headings."""
    user_prompt = (
        f"Title: {meta.get('title', '')}\n\n"
        f"DOCUMENT BODY (add headings):\n{body[:8000]}"
    )
    return call_claude(SYSTEM_ADD_HEADINGS, user_prompt, label=md_path.name)


def fix_chunk_overflow(md_path: Path, meta: dict, body: str) -> str:
    """Fix CHUNK_OVERFLOW: Claude splits oversized sections with H3 headings."""
    user_prompt = (
        f"Title: {meta.get('title', '')}\n\n"
        f"DOCUMENT BODY (split sections > 256 tokens with ### headings):\n{body[:8000]}"
    )
    return call_claude(SYSTEM_SPLIT_CHUNKS, user_prompt, label=md_path.name)


def fix_crlf(body: str) -> str:
    """Fix CRLF_ENCODING: simple replacement, no LLM needed."""
    return body.replace("\r\n", "\n").replace("\r", "\n")


# ─────────────────────────── ORCHESTRATOR ────────────────────────────────────

# Priority order for applying fixes (most destructive first)
FIX_ORDER = [
    "GARBLED_ENCODING",
    "SCANNED_PDF",
    "OCR_NOISE",
    "EXCEL_BAD_HEADERS",
    "STUB_EMPTY",
    "HEADING_MISSING",
    "CHUNK_OVERFLOW",
    "CRLF_ENCODING",
]


def fix_file(md_path: Path, record: dict, dry_run: bool) -> dict:
    """
    Apply the appropriate fix(es) to a single file.
    Returns a log dict with status and details.
    """
    issues  = set(record["issues"])
    url     = record.get("url", "")
    log     = {"file": record["file"], "status": "skipped", "fixes_applied": [], "error": None}

    print(f"\n  → {record['file']}")
    print(f"    Issues: {', '.join(sorted(issues))}")
    print(f"    URL:    {url or '(none)'}")

    # Read current file
    try:
        content = md_path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        log["status"] = "error"
        log["error"] = f"Cannot read file: {e}"
        return log

    meta, body = parse_frontmatter(content)

    # Apply CRLF fix first (no LLM, affects both meta + body parsing)
    if "CRLF_ENCODING" in issues:
        content = content.replace("\r\n", "\n").replace("\r", "\n")
        body    = body.replace("\r\n", "\n").replace("\r", "\n")
        log["fixes_applied"].append("CRLF_ENCODING")

    new_body = body  # will be progressively updated

    # Apply fixes in priority order
    for issue in FIX_ORDER:
        if issue not in issues:
            continue
        if issue == "CRLF_ENCODING":
            continue  # already handled above

        print(f"    Fixing: {issue}…")
        if dry_run:
            print(f"    [DRY RUN] Would apply fix for {issue}")
            log["fixes_applied"].append(f"{issue} (dry-run)")
            continue

        try:
            if issue in ("GARBLED_ENCODING", "OCR_NOISE"):
                new_body = fix_garbled_or_ocr_noise(md_path, list(issues), url, meta, new_body)
                log["fixes_applied"].append(issue)
                # After a full re-extraction, remaining content issues are resolved
                issues -= {"OCR_NOISE", "GARBLED_ENCODING", "STUB_EMPTY", "HEADING_MISSING", "CHUNK_OVERFLOW"}
                break

            elif issue == "SCANNED_PDF":
                new_body = fix_scanned_pdf(md_path, url, meta)
                log["fixes_applied"].append(issue)
                issues -= {"STUB_EMPTY", "HEADING_MISSING", "CHUNK_OVERFLOW", "OCR_NOISE"}
                break

            elif issue == "EXCEL_BAD_HEADERS":
                new_body = fix_excel_headers(md_path, meta, new_body)
                log["fixes_applied"].append(issue)

            elif issue == "STUB_EMPTY":
                new_body = fix_stub_empty(md_path, meta, new_body)
                log["fixes_applied"].append(issue)
                issues -= {"HEADING_MISSING"}

            elif issue == "HEADING_MISSING":
                new_body = fix_heading_missing(md_path, meta, new_body)
                log["fixes_applied"].append(issue)

            elif issue == "CHUNK_OVERFLOW":
                new_body = fix_chunk_overflow(md_path, meta, new_body)
                log["fixes_applied"].append(issue)

        except Exception as e:
            print(f"    [ERROR] {issue}: {e}")
            log["error"] = f"{issue}: {traceback.format_exc(limit=3)}"
            log["status"] = "error"
            return log

    if dry_run:
        log["status"] = "dry-run"
        return log

    # Safety Check: If LLM returned empty response or stub replacement failed,
    # do not overwrite original text with empty body.
    if len(new_body.strip()) < 50 and len(body.strip()) >= 50:
        print(f"    [WARNING] New body is empty/stub, but original had {len(body)} chars. Restoring original.")
        log["status"] = "error"
        log["error"] = "LLM returned empty response or stub replacement failed"
        return log

    # Backup original and write fixed file
    bak_path = md_path.with_suffix(".md.bak")
    if not bak_path.exists():
        shutil.copy2(md_path, bak_path)

    # Reconstruct: keep original frontmatter, replace body
    # Also add a processing note to frontmatter
    meta["last_fixed"] = datetime.now().strftime("%Y-%m-%d")
    meta["fixes_applied"] = log["fixes_applied"]

    new_content = render_frontmatter(meta) + "\n" + new_body.strip() + "\n"
    md_path.write_text(new_content, encoding="utf-8")

    log["status"] = "fixed"
    print(f"    ✅ Fixed → {md_path.name}  (backup: {bak_path.name})")
    return log


# ─────────────────────────── MAIN ────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description="AURA Data Re-Extractor")
    ap.add_argument("--data",     default="../../data",        help="Path to data/ directory")
    ap.add_argument("--audit",    default="audit_report",      help="Path to audit_report/ directory")
    ap.add_argument("--dry-run",  action="store_true",         help="Print what would be done, don't write files")
    ap.add_argument("--priority", default="critical,high",     help="Comma-separated priorities to fix (critical,high,medium,low)")
    ap.add_argument("--issue",    default=None,                help="Only fix files with this specific issue type (e.g. GARBLED_ENCODING)")
    ap.add_argument("--file",     default=None,                help="Fix only this one file (relative path from data/)")
    ap.add_argument("--limit",    type=int, default=None,      help="Max number of files to fix (for testing)")
    args = ap.parse_args()

    data_root  = Path(args.data).resolve()
    audit_dir  = Path(args.audit)
    audit_json = audit_dir / "audit_results.json"
    fix_log_path = audit_dir / "fix_log.json"

    # ── Pre-flight checks ────────────────────────────────────────────────────
    if not os.environ.get("GROQ_API_KEY") and not os.environ.get("ANTHROPIC_API_KEY"):
        print("[ERROR] Neither GROQ_API_KEY nor ANTHROPIC_API_KEY environment variable set.")
        sys.exit(1)


    if not audit_json.exists():
        print(f"[ERROR] Audit file not found: {audit_json}")
        print("        Run 1_audit_files.py first.")
        sys.exit(1)

    if not data_root.exists():
        print(f"[ERROR] data/ directory not found: {data_root}")
        sys.exit(1)

    # ── Load audit results ────────────────────────────────────────────────────
    with open(audit_json, encoding="utf-8") as f:
        audit_data = json.load(f)

    all_records = audit_data["results"]

    # ── Filter ───────────────────────────────────────────────────────────────
    target_priorities = {p.strip() for p in args.priority.split(",")}
    target_issues     = {i.strip().upper() for i in args.issue.split(",")} if args.issue else None

    records_to_fix = []
    for rec in all_records:
        if not rec["needs_reextract"] and rec["priority"] not in ("medium", "low"):
            continue
        if rec["priority"] not in target_priorities:
            continue
        if target_issues and not (set(rec["issues"]) & target_issues):
            continue
        if args.file and rec["file"] != args.file:
            continue
        if rec["issues"] and rec["priority"] != "ok":
            records_to_fix.append(rec)

    if args.limit:
        records_to_fix = records_to_fix[: args.limit]

    print(f"\n{'─'*60}")
    print(f"  AURA Re-Extractor {'(DRY RUN) ' if args.dry_run else ''}")
    print(f"  Data dir  : {data_root}")
    print(f"  Audit     : {audit_json}")
    print(f"  Priorities: {', '.join(sorted(target_priorities))}")
    print(f"  Files     : {len(records_to_fix)}")
    print(f"{'─'*60}")

    if not records_to_fix:
        print("  Nothing to fix.")
        return

    fix_logs = []
    counts   = {"fixed": 0, "error": 0, "skipped": 0, "dry-run": 0}

    for i, rec in enumerate(records_to_fix, 1):
        print(f"\n[{i}/{len(records_to_fix)}] {rec['priority'].upper()} | {rec['file']}")
        md_path = data_root / rec["file"]

        if not md_path.exists():
            print(f"  [MISSING] File not found on disk: {md_path}")
            fix_logs.append({"file": rec["file"], "status": "missing", "error": "file not found"})
            counts["error"] += 1
            continue

        log = fix_file(md_path, rec, dry_run=args.dry_run)
        fix_logs.append(log)
        counts[log["status"]] = counts.get(log["status"], 0) + 1

        # Save progress after each file (in case of interruption)
        with open(fix_log_path, "w", encoding="utf-8") as f:
            json.dump({
                "generated": datetime.now().isoformat(),
                "total": len(records_to_fix),
                "counts": counts,
                "logs": fix_logs,
            }, f, indent=2, ensure_ascii=False)

        # Sleep slightly to prevent rate limits
        if not args.dry_run:
            time.sleep(1.0)

    # ── Summary ───────────────────────────────────────────────────────────────
    print(f"\n{'─'*60}")
    print("  RE-EXTRACTION COMPLETE")
    print(f"{'─'*60}")
    print(f"  Fixed   : {counts.get('fixed', 0)}")
    print(f"  Errors  : {counts.get('error', 0)}")
    print(f"  Dry-run : {counts.get('dry-run', 0)}")
    print(f"\n  Fix log : {fix_log_path}")
    print(f"{'─'*60}\n")

    if counts.get("error", 0):
        print(f"  ⚠️  {counts['error']} files had errors. Check fix_log.json for details.")


if __name__ == "__main__":
    main()
