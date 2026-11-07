import zlib
import re

with open('data/raw/inec_electronic_transmission_procedure.pdf', 'rb') as f:
    raw = f.read()

stream_offsets = [m.start() for m in re.finditer(b'stream[\r\n]+', raw)]
print('Total streams:', len(stream_offsets))

extracted_texts = []
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
            extracted_texts.append(full)
    except Exception:
        pass

print(f"Extracted {len(extracted_texts)} text streams from Electronic Transmission PDF")
for i, t in enumerate(extracted_texts[:5]):
    print(f"\n--- STREAM {i} ({len(t)} chars) ---")
    print(t[:300])

