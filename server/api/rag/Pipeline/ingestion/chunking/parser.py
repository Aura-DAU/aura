import re
import yaml

def extract_frontmatter(content):

    """
    Extract YAML frontmatter from markdown files.

    Returns:
        metadata (dict)
        body (str)
    """

    content = content.lstrip("\ufeff")

    match = re.match(
        r"^---\n(.*?)\n---\n",
        content,
        re.DOTALL
    )

    if not match:
        return {}, content
    
    metadata = yaml.safe_load(match.group(1))
    body = content[match.end():]

    return metadata, body
