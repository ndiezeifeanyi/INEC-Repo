import zlib
import re
import json

# Read downloaded PDF
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

# Sections mapping to parse accurately from the gazette text
# S28: Notice of election
# S29: Submission of list of candidates and affidavits
# S47: Accreditation of voters (BVAS)
# S50: Voting and transmission of results
# S51: Over-voting
# S152: Repeal of Electoral Act 2022

pdf_full = "\n".join(pages)

def extract_section_text(sec_num):
    # Search for "sec_num. —(1)" or "sec_num. "
    pattern = rf'(?:^|\s){sec_num}\.\s*—?\s*(.*?)(?=(?:\s{sec_num+1}\.\s*—)|\Z)'
    m = re.search(pattern, pdf_full, re.DOTALL)
    if m:
        return " ".join(m.group(1).split())
    return None

manifest_data = []
target_sections = [28, 29, 47, 50, 51, 60, 64, 152]
for s in target_sections:
    text = extract_section_text(s)
    if text:
        manifest_data.append({
            "section": s,
            "text": text[:500]
        })
    print(f"Section {s} found: {bool(text)}")

with open('data/raw/parsed_sections_check.json', 'w', encoding='utf-8') as f:
    json.dump(manifest_data, f, indent=2)

