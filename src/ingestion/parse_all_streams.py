import zlib
import re

with open('data/raw/electoral_act_2026_gazette.pdf', 'rb') as f:
    raw = f.read()

streams = re.findall(rb'stream[\r\n]+(.*?)[\r\n]+endstream', raw, re.DOTALL)
print(f"Total streams: {len(streams)}")

for i, s in enumerate(streams):
    try:
        data = zlib.decompress(s)
        # Check for TJ array operators: [(text) 12 (more)] TJ
        tj_arrays = re.findall(rb'\[(.*?)\]\s*TJ', data, re.DOTALL)
        if tj_arrays:
            print(f"Stream {i} has {len(tj_arrays)} TJ arrays")
            for arr in tj_arrays[:10]:
                strings = re.findall(rb'\((.*?)\)', arr)
                line = "".join(s.decode('latin1', errors='ignore') for s in strings)
                print("  TJ line:", line)
        # Also simple Tj
        tj_simple = re.findall(rb'\((.*?)\)\s*Tj', data)
        if tj_simple:
            print(f"Stream {i} has {len(tj_simple)} simple Tj items")
    except Exception as e:
        pass
