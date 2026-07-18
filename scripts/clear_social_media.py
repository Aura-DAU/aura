from pathlib import Path
import re

social_files = [
    'data/student_services/social_media/instagram_page.md',
    'data/student_services/social_media/youtube_channel.md',
    'data/student_services/social_media/twitter_page.md',
    'data/student_services/social_media/facebook_page.md',
    'data/student_services/social_media/linkedin_page.md',
]

for path in social_files:
    fp = Path(path)
    if not fp.exists():
        continue
    text = fp.read_text(encoding='utf-8', errors='replace')
    m = re.match(r'^(---[\s\S]*?---)\s*', text)
    fm = m.group(1) if m else ''
    title_m = re.search(r'^title:\s*["\']?(.*?)["\']?\s*$', fm, re.MULTILINE)
    url_m   = re.search(r'^url:\s*["\']?(.*?)["\']?\s*$',   fm, re.MULTILINE)
    title = title_m.group(1).strip().strip('"').strip("'") if title_m else fp.stem
    url   = url_m.group(1).strip().strip('"').strip("'")   if url_m   else ''
    clean_body = f"# {title}\n\n## Overview\n\nThis page links to the official DA-IICT {title} account.\n\n## Official Link\n\n- [{title}]({url})\n"
    fp.write_text(fm + '\n\n' + clean_body, encoding='utf-8')
    print(f"Cleared: {fp.name}")
