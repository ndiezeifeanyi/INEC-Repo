import zlib
import re
import json

with open('data/raw/electoral_act_2026_gazette.pdf', 'rb') as f:
    raw = f.read()

stream_offsets = [m.start() for m in re.finditer(b'stream[\r\n]+', raw)]
pages = []
for offset in stream_offsets:
    match = re.match(rb'stream[\r\n]+', raw[offset:offset+20])
    if not match: continue
    start = offset + match.end()
    end = raw.find(b'endstream', start)
    if end == -1: continue
    try:
        decomp = zlib.decompress(raw[start:end])
        tj_list = re.findall(rb'\((.*?)\)\s*Tj', decomp)
        tj_arr = re.findall(rb'\[(.*?)\]\s*TJ', decomp, re.DOTALL)
        items = [s.decode('latin1', errors='ignore') for s in tj_list]
        for arr in tj_arr:
            sub = re.findall(rb'\((.*?)\)', arr)
            items.append("".join(s.decode('latin1', errors='ignore') for s in sub))
        full = " ".join(items)
        if len(full) > 30:
            pages.append(full)
    except Exception:
        pass

print(f"Extracted {len(pages)} pages.")

# Full text of Electoral Act
full_pdf_text = "\n".join(pages)

# Find sections by regex
# Sections look like: "28. —(1)" or "47. —(1)" or "152."
section_pattern = r'(\b(\d{1,3})\.\s*—?\s*(?:\\\()?([0-9a-zA-Z]{0,2})(?:\\\))?\s+([^0-9]{10,}?)(?=\b\d{1,3}\.\s*—|\Z))'

chunks = []
# Let's search specifically for Section numbers 1 to 153 in the extracted pages
for p_idx, page in enumerate(pages):
    # clean escapes
    cleaned = page.replace(r'\(', '(').replace(r'\)', ')').replace(r'\037', 'fi')
    # find section markers
    matches = re.finditer(r'(?:^|\s)(\d{1,3})\.\s*—?\s*(?:\(([0-9a-zA-Z]+)\))?\s*(.*?)(?=(?:\s\d{1,3}\.\s*—)|\Z)', cleaned, re.DOTALL)
    for m in matches:
        sec_num = m.group(1)
        subsec = m.group(2)
        body = m.group(3).strip()
        if len(body) > 40 and not sec_num.startswith('0'):
            chunk_id = f"EA2026-S{sec_num}" + (f"-SS{subsec}" if subsec else "")
            chunks.append({
                "chunk_id": chunk_id,
                "section": sec_num,
                "subsection": subsec,
                "page": p_idx + 1,
                "raw_text": body[:600]
            })

print(f"Total extracted section chunks from PDF: {len(chunks)}")
with open('data/raw/extracted_chunks_manifest.json', 'w', encoding='utf-8') as f:
    json.dump(chunks, f, indent=2)
print("Saved data/raw/extracted_chunks_manifest.json")
