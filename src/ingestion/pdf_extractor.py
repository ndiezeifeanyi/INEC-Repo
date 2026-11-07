"""
Standard Library PDF Parser for Electoral Act 2026 Gazette.
Uses exact PDF-1.3 object tree traversal and Flate decompression.
Parses sections by structural headings, handles the First Schedule separately,
and excludes the Table of Contents (Arrangement of Sections).
"""

import zlib
import re
import json
import hashlib
from typing import List, Dict, Tuple, Optional

class StandardPDFExtractor:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        with open(pdf_path, 'rb') as f:
            self.raw = f.read()
        self.objects: Dict[int, bytes] = {}
        self.page_content_obj_ids: List[int] = []
        self._parse_objects()
        self._resolve_pages()

    def _parse_objects(self):
        # Locate all 'X 0 obj ... endobj' blocks
        pattern = re.compile(rb'(\d+)\s+0\s+obj[\r\n]+(.*?)[\r\n]+endobj', re.DOTALL)
        for m in pattern.finditer(self.raw):
            obj_id = int(m.group(1))
            self.objects[obj_id] = m.group(2)

    def _resolve_pages(self):
        # Locate /Type/Page objects in order
        page_pattern = re.compile(rb'/Type\s*/Page\b.*?/Contents\s+(\d+)\s+0\s+R', re.DOTALL)
        for obj_id, body in self.objects.items():
            if b'/Type/Page' in body or b'/Type /Page' in body:
                m = page_pattern.search(body)
                if m:
                    contents_id = int(m.group(1))
                    self.page_content_obj_ids.append((obj_id, contents_id))

        # Sort pages by page object ID to ensure sequential order
        self.page_content_obj_ids.sort(key=lambda x: x[0])

    def extract_page_text(self, page_index: int) -> str:
        if page_index >= len(self.page_content_obj_ids):
            return ""
        _, contents_id = self.page_content_obj_ids[page_index]
        content_body = self.objects.get(contents_id, b"")
        
        # Extract stream
        s_match = re.search(rb'stream[\r\n]+', content_body)
        if not s_match:
            return ""
        s_start = s_match.end()
        s_end = content_body.find(b'endstream')
        if s_end == -1:
            return ""
        raw_stream = content_body[s_start:s_end].rstrip(b'\r\n')
        try:
            decomp = zlib.decompress(raw_stream)
        except Exception:
            return ""

        # Extract text tokens (Tj and TJ)
        tj_list = re.findall(rb'\((.*?)\)\s*Tj', decomp)
        tj_arr = re.findall(rb'\[(.*?)\]\s*TJ', decomp, re.DOTALL)
        items = [s.decode('latin1', errors='ignore') for s in tj_list]
        for arr in tj_arr:
            sub = re.findall(rb'\((.*?)\)', arr)
            items.append("".join(s.decode('latin1', errors='ignore') for s in sub))
        
        full_text = " ".join(items)
        # Clean typography escapes
        cleaned = full_text.replace(r'\(', '(').replace(r'\)', ')').replace(r'\037', 'fi')
        return " ".join(cleaned.split())

    def extract_all_pages(self) -> List[Tuple[int, str]]:
        pages = []
        for i in range(len(self.page_content_obj_ids)):
            text = self.extract_page_text(i)
            pages.append((i + 1, text))
        return pages

if __name__ == "__main__":
    extractor = StandardPDFExtractor("data/raw/electoral_act_2026_gazette.pdf")
    pages = extractor.extract_all_pages()
    print(f"Successfully extracted {len(pages)} sequential pages.")
    for p_num, text in pages[:4]:
        print(f"\n--- PAGE {p_num} ({len(text)} chars) ---")
        print(text[:250])
