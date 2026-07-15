
from pathlib import Path

def extract_frontmatter(content: str) -> tuple[dict, str]:
    """Extremely basic frontmatter parser for validation purposes."""
    import yaml

    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            try:
                metadata = yaml.safe_load(parts[1]) or {}
                return metadata, parts[2]
            except yaml.YAMLError:
                # Ignore frontmatter YAML syntax errors and return default empty metadata
                pass
    return {}, content

def main():
    repo_root = Path(__file__).resolve().parent.parent.parent
    data_dir = repo_root / "data"

    missing_auth_files = []

    print(f"Scanning directory: {data_dir}")
    md_files = list(data_dir.rglob("*.md"))
    print(f"Found {len(md_files)} markdown files.")

    for file_path in md_files:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        metadata, _ = extract_frontmatter(content)

        # Check if 'authorization' field exists in metadata
        if "authorization" not in metadata:
            missing_auth_files.append(file_path.relative_to(repo_root))

    if missing_auth_files:
        print(f"\nFound {len(missing_auth_files)} files missing 'authorization' field in frontmatter:")
        for missing in sorted(missing_auth_files):
            print(f"  - {missing}")
    else:
        print("\nAll files have the 'authorization' field!")

if __name__ == "__main__":
    main()
