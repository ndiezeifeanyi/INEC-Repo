import urllib.request
import re

url = 'https://inecnigeria.org/elections/guidelines'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        html = resp.read().decode('utf-8', errors='ignore')
    links = re.findall(r'href=[\'"]([^\'"]+)[\'"]', html, re.IGNORECASE)
    pdf_links = [l for l in links if '.pdf' in l.lower()]
    print('PDF links found on inec guidelines page:', pdf_links)
    # Save the HTML as raw source of record
    with open('data/raw/inec_guidelines_page.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print('Saved data/raw/inec_guidelines_page.html')
except Exception as e:
    print('Failed:', e)

