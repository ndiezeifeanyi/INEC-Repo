import zlib
import re

with open('data/raw/electoral_act_2026_gazette.pdf', 'rb') as f:
    raw = f.read()

streams = re.findall(rb'stream[\r\n]+(.*?)[\r\n]+endstream', raw, re.DOTALL)
for i, s in enumerate(streams):
    try:
        data = zlib.decompress(s)
        # Search for Tj or TJ PDF text operators
        tj_matches = re.findall(rb'\((.*?)\)\s*Tj', data)
        if tj_matches:
            text_lines = [m.decode('latin1', errors='ignore') for m in tj_matches]
            print(f"=== STREAM {i}: Found {len(text_lines)} Tj text chunks ===")
            print('\n'.join(text_lines[:40]))
    except Exception as e:
        pass

