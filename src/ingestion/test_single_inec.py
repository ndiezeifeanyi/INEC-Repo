import urllib.request
import urllib.parse
import hashlib
import os

base_url = "https://inecnigeria.org"
links = [
    "/documents/guidelines/REGULATIONS-AND-GUIDELINES-FOR-2026.pdf",
    "/documents/guidelines/Electronic_Transmission___Collation_Of_Result-5.pdf"
]

for l in links:
    full_url = urllib.parse.urljoin(base_url, l)
    fname = os.path.basename(l)
    dest = os.path.join("data/raw", fname)
    print(f"Testing {full_url}...")
    try:
        req = urllib.request.Request(full_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read()
            sha = hashlib.sha256(data).hexdigest()
            with open(dest, "wb") as f:
                f.write(data)
            print(f"SUCCESS: {dest} ({len(data)} bytes, sha256={sha})")
    except Exception as e:
        print(f"FAILED {full_url}: {e}")

