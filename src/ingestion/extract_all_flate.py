import zlib
import re

with open('data/raw/electoral_act_2026_gazette.pdf', 'rb') as f:
    raw = f.read()

# Find all occurrences of "stream"
stream_offsets = [m.start() for m in re.finditer(b'stream[\r\n]+', raw)]
print('Total stream offsets:', len(stream_offsets))

pages_text = []

for offset in stream_offsets:
    # Find start of stream data
    match = re.match(rb'stream[\r\n]+', raw[offset:offset+20])
    if not match:
        continue
    data_start = offset + match.end()
    end_offset = raw.find(b'endstream', data_start)
    if end_offset == -1:
        continue
    stream_data = raw[data_start:end_offset]
    try:
        decomp = zlib.decompress(stream_data)
        # Check if contains Tj or TJ
        tj_list = re.findall(rb'\((.*?)\)\s*Tj', decomp)
        tj_arr = re.findall(rb'\[(.*?)\]\s*TJ', decomp, re.DOTALL)
        extracted = []
        for s in tj_list:
            extracted.append(s.decode('latin1', errors='ignore'))
        for arr in tj_arr:
            sub = re.findall(rb'\((.*?)\)', arr)
            extracted.append("".join(s.decode('latin1', errors='ignore') for s in sub))
        full = " ".join(extracted)
        if len(full) > 30:
            pages_text.append(full)
    except Exception:
        pass

print(f"Extracted text streams: {len(pages_text)}")
for i, pt in enumerate(pages_text[:15]):
    print(f"\n--- EXTRACTED STREAM {i} ({len(pt)} chars) ---")
    print(pt[:400])
