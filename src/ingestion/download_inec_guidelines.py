import urllib.request
import hashlib
import os

os.makedirs('data/raw', exist_ok=True)

files_to_download = [
    ("https://inecnigeria.org/documents/guidelines/REGULATIONS-AND-GUIDELINES-FOR-2026.pdf", "data/raw/inec_regulations_and_guidelines_2026.pdf"),
    ("https://inecnigeria.org/documents/guidelines/Electronic_Transmission___Collation_Of_Result-5.pdf", "data/raw/inec_electronic_transmission_procedure.pdf")
]

for url, dest in files_to_download:
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
        sha = hashlib.sha256(data).hexdigest()
        with open(dest, 'wb') as f:
            f.write(data)
        print(f"Downloaded {dest}: size={len(data)}, sha256={sha}")
    except Exception as e:
        print(f"Failed {url}: {e}")
