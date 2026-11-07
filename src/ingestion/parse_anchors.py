with open('data/raw/inec_guidelines_page.html', 'r', encoding='utf-8') as f:
    html = f.read()

import re
matches = re.findall(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', html, re.DOTALL)
for href, text in matches:
    clean_text = ' '.join(text.split())
    if any(k in clean_text.lower() or k in href.lower() for k in ['guideline', 'regulation', 'transmission', '2026', 'electoral']):
        print(f"HREF: {href} | TEXT: {clean_text}")
