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

from dotenv import load_dotenv
possible_env_paths = [
    Path(__file__).resolve().parents[1] / "server" / "rag" / ".env",
    Path(__file__).resolve().parent / ".env",
]
env_loaded = False
for p in possible_env_paths:
    if p.exists():
        load_dotenv(p)
        env_loaded = True
        break
if not env_loaded:
    load_dotenv()

from groq import Groq, RateLimitError, APIStatusError, APIConnectionError

# ─────────────────────────── CONFIG ──────────────────────────────────────────

CHUNK_SIZE      = 256   # tokens — must match chunker/config.py
MODEL           = "openai/gpt-oss-120b"
MAX_TOKENS      = 3000
RETRY_SLEEP     = 3     # seconds between Claude retries
MAX_RETRIES     = 3
REQUEST_TIMEOUT = 30    # seconds for PDF downloads
OCR_DPI         = 300

PDF_DOWNLOAD_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}

client = Groq(api_key=os.environ.get("GROQ_API_KEY", ""))


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
    try:
        r = requests.get(url, headers=PDF_DOWNLOAD_HEADERS,
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
    """Call LLM with fallback model rotation on Groq. Returns the response text."""
    models_to_try = [
        "openai/gpt-oss-120b",
        "llama-3.3-70b-versatile",
        "qwen/qwen3.6-27b",
        "llama-3.1-8b-instant"
    ]
    
    for model in models_to_try:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                current_max_tokens = MAX_TOKENS
                if model == "llama-3.1-8b-instant":
                    prompt_tokens = estimate_tokens(system) + estimate_tokens(user)
                    current_max_tokens = max(800, min(MAX_TOKENS, 5800 - prompt_tokens))

                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user}
                    ],
                    max_tokens=current_max_tokens,
                    temperature=0.1,
                )
                content = response.choices[0].message.content
                if content:
                    return content
                raise ValueError("Received empty response content from model")
            except (RateLimitError, APIStatusError, APIConnectionError) as e:
                status_code = getattr(e, "status_code", None)
                print(f"    [API ERROR] Model {model} (attempt {attempt}/{MAX_RETRIES}): status {status_code}, error: {e}")
                
                # If we hit 429, 503, 413, we rotate to the next model immediately
                if status_code in (429, 503, 413):
                    print(f"    [ROTATE] Capacity/rate limit hit (status {status_code}). Switching to next model…")
                    break  # break the retry loop to try the next model
                
                if attempt == MAX_RETRIES:
                    print(f"    [ROTATE] Max retries reached for {model}. Switching to next model…")
                    break
                
                sleep_time = RETRY_SLEEP * attempt
                print(f"    [RETRY] Sleeping {sleep_time}s before retry…")
                time.sleep(sleep_time)
            except Exception as e:
                print(f"    [UNEXPECTED ERROR] Model {model}: {e}")
                if attempt == MAX_RETRIES:
                    break
                time.sleep(RETRY_SLEEP)
                
    raise RuntimeError(f"All models in fallback rotation failed for {label}")


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
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, 1):
            # Render page to PIL image at 300 DPI
            img = page.to_image(resolution=OCR_DPI).original
            text = pytesseract.image_to_string(img, lang="eng", config="--psm 6")
            if text.strip():
                ocr_pages.append(f"--- Page {i} ---\n{text.strip()}")
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
    if not url or "pdf" not in url.lower():
        print(f"    [SKIP] No PDF URL available for {md_path.name}, using LLM on existing text.")
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
            raise RuntimeError("Download failed or file too small")

        if has_text_layer(tmp_pdf):
            print(f"    Text layer found — using pdfplumber + camelot")
            raw_text, table_mds = extract_pdf_text_layer(tmp_pdf)
            tables_section = ""
            if table_mds:
                tables_section = "\n\nEXTRACTED TABLES (already in Markdown):\n" + "\n\n".join(table_mds)
            user_prompt = (
                f"Title: {meta.get('title', '')}\nURL: {url}\n"
                f"Category: {meta.get('category', '')}\n\n"
                f"RAW TEXT:\n{raw_text[:10000]}"
                f"{tables_section}"
            )
            return call_claude(SYSTEM_CLEAN_PDF, user_prompt, label=md_path.name)
        else:
            print(f"    No text layer — running OCR")
            try:
                ocr_text = extract_pdf_ocr(tmp_pdf)
            except Exception as ocr_err:
                print(f"    [OCR FAIL] {ocr_err}. Falling back to cleaning existing text.")
                return call_claude(
                    SYSTEM_CLEAN_OCR,
                    f"Title: {meta.get('title','')}\nURL: {url}\n\nRAW TEXT TO CLEAN:\n{body[:12000]}",
                    label=md_path.name
                )
            user_prompt = (
                f"Title: {meta.get('title', '')}\nURL: {url}\n"
                f"Category: {meta.get('category', '')}\n\n"
                f"OCR TEXT:\n{ocr_text[:12000]}"
            )
            return call_claude(SYSTEM_CLEAN_OCR, user_prompt, label=md_path.name)

    except Exception as e:
        print(f"    [DOWNLOAD/PROCESS FAIL] {e}. Falling back to cleaning existing text.")
        return call_claude(
            SYSTEM_CLEAN_PDF,
            f"Title: {meta.get('title','')}\nURL: {url}\n\nRAW TEXT TO CLEAN:\n{body[:12000]}",
            label=md_path.name
        )

    finally:
        try:
            tmp_pdf.unlink()
        except Exception:
            pass


def fix_scanned_pdf(md_path: Path, url: str, meta: dict, body: str) -> str:
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

    except Exception as e:
        print(f"    [DOWNLOAD/OCR FAIL] {e}. Falling back to cleaning existing text.")
        return call_claude(
            SYSTEM_CLEAN_OCR,
            f"Title: {meta.get('title','')}\nURL: {url}\n\nRAW TEXT TO CLEAN:\n{body[:12000]}",
            label=md_path.name
        )

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
                new_body = fix_scanned_pdf(md_path, url, meta, new_body)
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

    # Safeguard against empty or extremely short LLM output
    if not dry_run and log["fixes_applied"]:
        orig_body_stripped = body.strip()
        new_body_stripped = new_body.strip()
        if len(new_body_stripped) == 0 or (len(new_body_stripped) < 50 and len(orig_body_stripped) >= 50):
            print(f"    [ABORT] Fixed body is unexpectedly empty or extremely short ({len(new_body_stripped)} chars) "
                  f"compared to original ({len(orig_body_stripped)} chars). Aborting write to prevent data loss.")
            log["status"] = "error"
            log["error"] = "Safeguard: LLM response empty or extremely short compared to original body"
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
    ap.add_argument("--retry-errors", action="store_true",     help="Only retry files that had errors in fix_log.json")
    args = ap.parse_args()

    data_root  = Path(args.data).resolve()
    audit_dir  = Path(args.audit)
    audit_json = audit_dir / "audit_results.json"
    fix_log_path = audit_dir / "fix_log.json"

    # ── Pre-flight checks ────────────────────────────────────────────────────
    if not os.environ.get("GROQ_API_KEY"):
        print("[ERROR] GROQ_API_KEY environment variable not set.")
        print("        export GROQ_API_KEY=...")
        sys.exit(1)

    if not audit_json.exists():
        print(f"[ERROR] Audit file not found: {audit_json}")
        print("        Run 1_audit_files.py first.")
        sys.exit(1)

    if not data_root.exists():
        print(f"[ERROR] data/ directory not found: {data_root}")
        sys.exit(1)

    # ── Load failed files if requested ────────────────────────────────────────
    failed_files = set()
    if args.retry_errors:
        if fix_log_path.exists():
            try:
                with open(fix_log_path, encoding="utf-8") as f:
                    old_log = json.load(f)
                    for entry in old_log.get("logs", []):
                        if entry.get("status") in ("error", "dry-run"):
                            failed_files.add(entry.get("file"))
                print(f"Loaded {len(failed_files)} failed files from previous run.")
            except Exception as e:
                print(f"Warning: Could not read fix_log.json: {e}")
        else:
            print("Warning: --retry-errors specified but fix_log.json does not exist.")

    # ── Load audit results ────────────────────────────────────────────────────
    with open(audit_json, encoding="utf-8") as f:
        audit_data = json.load(f)

    all_records = audit_data["results"]

    # ── Filter ───────────────────────────────────────────────────────────────
    target_priorities = {p.strip() for p in args.priority.split(",")}
    target_issues     = {i.strip().upper() for i in args.issue.split(",")} if args.issue else None

    records_to_fix = []
    for rec in all_records:
        if args.retry_errors and rec["file"] not in failed_files:
            continue
        if not args.retry_errors:
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

        # Sleep to avoid hitting TPM rate limits
        if not args.dry_run and log["status"] == "fixed" and i < len(records_to_fix):
            time.sleep(2)

        # Save progress after each file (in case of interruption)
        with open(fix_log_path, "w", encoding="utf-8") as f:
            json.dump({
                "generated": datetime.now().isoformat(),
                "total": len(records_to_fix),
                "counts": counts,
                "logs": fix_logs,
            }, f, indent=2, ensure_ascii=False)

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
