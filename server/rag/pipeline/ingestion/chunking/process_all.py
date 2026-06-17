import json
from pathlib import Path

from process_corpus import process_markdown_file


# ==========================================
# CONFIG
# ==========================================

DATA_DIR = "../../../../../data"
OUTPUT_DIR = "../../../processed_chunks"
OUTPUT_FILE = "chunks.json"


# ==========================================
# MAIN
# ==========================================

def main():

    all_chunks = []

    file_count = 0

    file_stats = []

    total_characters = 0

    md_files = list(
        Path(DATA_DIR).rglob("*.md")
    )

    print(f"\nFound {len(md_files)} markdown files.\n")

    for md_file in md_files:

        try:

            chunks = process_markdown_file(md_file)

            all_chunks.extend(chunks)

            file_count += 1

            file_stats.append({
                "file": str(md_file),
                "chunk_count": len(chunks)
            })

            total_characters += sum(
                len(chunk["text"])
                for chunk in chunks
            )

            print(
                f"[{file_count}] "
                f"{md_file.name} "
                f"→ {len(chunks)} chunks"
            )

        except Exception as e:

            print(
                f"[ERROR] {md_file}\n"
                f"Reason: {e}\n"
            )

    # ======================================
    # SAVE OUTPUT
    # ======================================

    output_path = Path(OUTPUT_DIR)

    output_path.mkdir(
        parents=True,
        exist_ok=True
    )

    final_output = output_path / OUTPUT_FILE

    with open(
        final_output,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            all_chunks,
            f,
            ensure_ascii=False,
            indent=2
        )

    # ======================================
    # STATS
    # ======================================

    print("\n" + "=" * 60)
    print("PROCESSING COMPLETE")
    print("=" * 60)

    print(
        f"Files processed: {file_count}"
    )

    print(
        f"Chunks generated: {len(all_chunks)}"
    )

    if file_count > 0:

        avg_chunks = (
            len(all_chunks)
            / file_count
        )

        print(
            f"Average chunks/file: "
            f"{avg_chunks:.2f}"
        )

    if all_chunks:

        avg_chunk_length = (
            total_characters
            / len(all_chunks)
        )

        print(
            f"Average chunk length: "
            f"{avg_chunk_length:.2f} chars"
        )

    if file_stats:

        largest_file = max(
            file_stats,
            key=lambda x: x["chunk_count"]
        )

        print(
            f"Largest file: "
            f"{largest_file['file']}"
        )

        print(
            f"Largest chunk count: "
            f"{largest_file['chunk_count']}"
        )

    print(
        f"\nSaved to: {final_output}"
    )

    print("=" * 60)


if __name__ == "__main__":
    main()