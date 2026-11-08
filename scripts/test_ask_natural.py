import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from src.web.app import app

client = TestClient(app)

queries = [
    ("Natural 1 (Over-Voting)", "What happens if more ballots are counted than accredited voters at a polling station?"),
    ("Natural 1 (Voter Card / PVC)", "Can I vote if I do not have my permanent voter card on election day?"),
    ("Natural 4 (Notice of Election)", "How many days before the election must the commission publish the official notice?"),
    ("Natural 4 (Scores Transmission to Portal)", "How are election scores sent from polling booths to the national portal?")
]

results = {}
for label, q in queries:
    res = client.post("/api/v1/ask", json={"query": q, "language": "en"})
    assert res.status_code == 200, f"Failed for {label}: {res.text}"
    results[label] = res.json()

print(json.dumps(results, indent=2))
