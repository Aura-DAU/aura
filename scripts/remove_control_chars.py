import re
from pathlib import Path

# Control characters pattern (excluding \t, \n, \r)
CONTROL_CHAR_RE = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f\x16]')

def clean_file(fp: Path):
    text = fp.read_text(encoding='utf-8', errors='replace')
    cleaned, count = CONTROL_CHAR_RE.subn('', text)
    if count > 0:
        fp.write_text(cleaned, encoding='utf-8')
        print(f"Cleaned {count} control chars from {fp.name}")

if __name__ == "__main__":
    data_dir = Path("data")
    for fp in data_dir.rglob("*.md"):
        clean_file(fp)
