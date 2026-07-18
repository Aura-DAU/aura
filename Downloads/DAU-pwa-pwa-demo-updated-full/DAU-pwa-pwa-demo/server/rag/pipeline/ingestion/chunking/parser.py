import re
import yaml

def extract_frontmatter(content):

    """
    Extract YAML frontmatter from markdown files.

    Returns:
        metadata (dict)
        body (str)
    """

    content = content.lstrip("\ufeff").replace("\r\n", "\n")

    match = re.match(
        r"^---\n(.*?)\n---\n",
        content,
        re.DOTALL
    )

    if not match:
        return {}, content

    # safe_load returns None for empty frontmatter and may return a
    # non-dict for malformed YAML; downstream code expects a dict.
    metadata = yaml.safe_load(match.group(1))
    if not isinstance(metadata, dict):
        metadata = {}
    body = content[match.end():]

    return metadata, body
