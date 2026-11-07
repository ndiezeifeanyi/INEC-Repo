import urllib.request
import hashlib
import os

url = "https://inecnigeria.org/documents/guidelines/REGULATIONS-AND-GUIDELINES-FOR-2026.pdf"
req = urllib.request.Request(
    url,
    headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://inecnigeria.org/elections/guidelines',
        'Accept': 'application/pdf,*/*'
    }
)

print(f"Requesting {url}...")
try:
    with urllib.request.urlopen(req, timeout=15) as resp:
        print("Status:", resp.status)
        print("Headers:", resp.headers)
        data = resp.read()
        print("Read bytes:", len(data))
        sha = hashlib.sha256(data).hexdigest()
        dest = "data/raw/inec_regulations_and_guidelines_2026.pdf"
        with open(dest, "wb") as f:
            f.write(data)
        print(f"Saved {dest}, SHA256: {sha}")
except Exception as e:
    print("Error:", e)

