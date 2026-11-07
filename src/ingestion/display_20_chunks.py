import json
import random

with open('data/raw/extracted_chunks_manifest.json', 'r', encoding='utf-8') as f:
    chunks = json.load(f)

# Select 20 representative chunks across sections (early, middle, late)
random.seed(42)
sampled = random.sample(chunks, min(20, len(chunks)))

print(f"{'CHUNK ID':<18} | {'PAGE':<5} | {'PDF RAW TEXT EXTRACT'}")
print("-" * 100)
for i, c in enumerate(sampled, 1):
    raw_preview = " ".join(c['raw_text'].split())[:120]
    print(f"{i:2d}. {c['chunk_id']:<14} | P.{c['page']:<3} | {raw_preview}...")
