# DAU PWA — Data Scripts

Three utility scripts for auditing, re-extracting, and formatting the `data/` markdown corpus for the RAG pipeline.

---

## 1. `audit_data.py` — Quality Auditor

Scans every `.md` file and classifies it by severity.

```bash
# Run from repo root
python scripts/audit_data.py
python scripts/audit_data.py --data-dir data --output audit_report.json
```

### Severity Levels

| Level | Meaning |
|-------|---------|
| `CRITICAL` | Control characters (`\x0c`, `\x01`, etc.) or binary mojibake garbage |
| `WARN` | OCR noise (spaced letters, consonant runs) / broken tables / missing H1+H2 headings |
| `LOW` | Stub file — less than 200 characters of body content |
| `CHUNK` | A section exceeds 512 tokens and will fragment badly at ingest |
| `OK` | No issues detected |

**Output:** `audit_report.json` — one entry per file with `path`, `severity`, `issues[]`, `url`.

---

## 2. `reextract.py` — Smart Re-Extractor

Re-downloads from the source URL and re-extracts content using the best available strategy:

| Source Type | Strategy |
|-------------|----------|
| Text-based PDF | `pdfplumber` (preserves tables) |
| Scanned / image PDF | Tesseract OCR via `pdf2image` |
| Excel (`.xlsx`) | `openpyxl` → Markdown table |
| Word (`.docx`) | `python-docx` → Markdown |
| HTML page | Stripped via regex |
| All types | **Gemini LLM cleanup** (optional) for structure + heading generation |

```bash
# Re-extract a single file
python scripts/reextract.py --file data/academics/some_policy.md

# Re-extract all CRITICAL files from the audit report
python scripts/reextract.py --from-audit audit_report.json --severity CRITICAL

# Re-extract CRITICAL + WARN, dry-run only
python scripts/reextract.py --from-audit audit_report.json --severity CRITICAL WARN --dry-run

# Skip LLM (faster, no API key needed)
python scripts/reextract.py --file data/academics/some_policy.md --no-llm
```

### Required ENV Variable
Set `GEMINI_API_KEY` in your shell or in `server/rag/.env` for LLM-based cleanup.

---

## 3. `format_for_rag.py` — RAG Compliance Formatter

Ensures every H2 section fits within the **256-token** chunk limit:
- Splits oversized H2 sections at paragraph/sentence boundaries
- Table-heavy sections are kept intact (tables are converted at ingest time)
- Generates `## Section (continued N)` headings for auto-split sections

```bash
# Format a single file (in-place)
python scripts/format_for_rag.py data/academics/some_file.md

# Format to a new output path
python scripts/format_for_rag.py data/academics/some_file.md --output out.md

# Format ALL files under data/
python scripts/format_for_rag.py --all data/
```

---

## Recommended Workflow

```
1. Run audit
   python scripts/audit_data.py

2. Re-extract broken files
   python scripts/reextract.py --from-audit audit_report.json --severity CRITICAL WARN

3. Format for RAG compliance
   python scripts/format_for_rag.py --all data/

4. Re-audit to confirm
   python scripts/audit_data.py --output audit_report_after.json

5. Commit only the data/ .md files
   git add data/
   git commit -m "fix(data): re-extract and format N files for RAG compliance"
```

---

## Dependencies

```bash
pip install pdfplumber PyMuPDF pdf2image pytesseract openpyxl python-docx requests transformers google-generativeai
```

> **Tesseract** must also be installed system-wide:
> - Windows: https://github.com/UB-Mannheim/tesseract/wiki
> - Ubuntu: `sudo apt-get install tesseract-ocr`
