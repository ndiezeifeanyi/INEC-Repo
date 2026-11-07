import zlib
import re

with open('data/raw/electoral_act_2026_gazette.pdf', 'rb') as f:
    raw = f.read()

streams = re.findall(rb'stream[\r\n]+(.*?)[\r\n]+endstream', raw, re.DOTALL)
print('Total streams found:', len(streams))
decompressed_text = []
for i, s in enumerate(streams):
    try:
        data = zlib.decompress(s)
        words = re.findall(rb'[A-Za-z0-9,.:;()\-]{2,}', data)
        text_frag = ' '.join(w.decode('latin1') for w in words)
        if len(text_frag) > 50:
            decompressed_text.append(f"--- STREAM {i} ---\n" + text_frag[:300])
    except Exception:
        pass

print('Decompressed streams with text:', len(decompressed_text))
for item in decompressed_text[:10]:
    print(item)
