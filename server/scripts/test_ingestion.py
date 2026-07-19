import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent

ingestion_dir = PROJECT_ROOT / "server/rag/pipeline/ingestion/chunking"
sys.path.insert(0, str(ingestion_dir))

from process_corpus import process_markdown_file

def test_ingestion():
    file1 = PROJECT_ROOT / "data/internal_policies/faculty_evaluation_rubric.md"
    file2 = PROJECT_ROOT / "data/internal_policies/senate_meeting_minutes_2023.md"

    print("Processing:", file1.name)
    chunks1 = process_markdown_file(file1)
    for i, c in enumerate(chunks1):
        print(f"Chunk {i} authorization: {c.get('authorization')}")

    print("\nProcessing:", file2.name)
    chunks2 = process_markdown_file(file2)
    for i, c in enumerate(chunks2):
        print(f"Chunk {i} authorization: {c.get('authorization')}")

if __name__ == "__main__":
    test_ingestion()
