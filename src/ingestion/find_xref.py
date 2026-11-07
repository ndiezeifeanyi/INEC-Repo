import re

with open('data/raw/electoral_act_2026_gazette.pdf', 'rb') as f:
    raw = f.read()

# Locate xref or startxref
startxref_pos = raw.rfind(b'startxref')
print('startxref_pos:', startxref_pos)
xref_offset = int(raw[startxref_pos+9:].strip().split()[0])
print('xref offset:', xref_offset)

# Read the object table or cross reference stream
xref_data = raw[xref_offset:xref_offset+500]
print('xref data preview:\n', xref_data[:200])

