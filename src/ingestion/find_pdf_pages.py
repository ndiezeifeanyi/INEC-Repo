import zlib
import re

with open('data/raw/electoral_act_2026_gazette.pdf', 'rb') as f:
    raw = f.read()

# Find pages
# In PDF 1.3: /Type /Page ... /Contents <obj_ref>
page_objs = list(re.finditer(rb'<<[^\>]*?/Type\s*/Page\b[^\>]*?>>', raw, re.DOTALL))
print('Page objects found by dict:', len(page_objs))

# Let's inspect object IDs for pages
pages_dict = []
for m in page_objs:
    d = m.group(0)
    # find contents ref
    c_match = re.search(rb'/Contents\s+(\d+)\s+(\d+)\s+R', d)
    if c_match:
        obj_id = int(c_match.group(1))
        pages_dict.append(obj_id)

print('Pages with Contents obj ref:', len(pages_dict))
print('Sample content obj IDs:', pages_dict[:10])
