"""
Official Corpus Ingestion & Rebuild Engine for Electoral Act 2026 & INEC Procedures.
Treats official Gazette PDF as source of record.
Uses pypdf for robust PDF object parsing.
Excludes Table of Contents (Pages 3-8).
Treats First Schedule (Election Petitions) as separate part with IDs like EA2026-SCH1-P7.
Enforces unique chunk IDs across all records (fails build on duplicate).
"""

import os
import re
import json
import hashlib
from datetime import date
from typing import List, Dict, Any, Set
import pypdf

GAZETTE_PDF = "data/raw/electoral_act_2026_gazette.pdf"
GAZETTE_URL = "https://nass.gov.ng/documents/download/11248"
EXPECTED_GAZETTE_SHA256 = "dee5a37b62b920c9cfaf009b7dc1dcf5ccb5cbbeff807f5487eac868ce882fd6"

TRANSMISSION_PDF = "data/raw/inec_electronic_transmission_procedure.pdf"
TRANSMISSION_URL = "https://inecnigeria.org/documents/guidelines/Electronic_Transmission___Collation_Of_Result-5.pdf"

RETRIEVAL_DATE = "2026-11-07"

PARTS_INDEX = [
    (1, 7, "Part I: Establishment and Functions of Independent National Electoral Commission"),
    (8, 8, "Part II: Staff of the Commission"),
    (9, 23, "Part III: National Register of Voters and Voters' Registration"),
    (24, 74, "Part IV: Procedure at Election"),
    (75, 102, "Part V: Political Parties"),
    (103, 113, "Part VI: Procedure for Election to Area Council"),
    (114, 129, "Part VII: Electoral Offences"),
    (130, 145, "Part VIII: Determination of Election Petitions"),
    (146, 156, "Part IX: Miscellaneous Provisions"),
]

def get_part_title(sec_num: int) -> str:
    for s_start, s_end, title in PARTS_INDEX:
        if s_start <= sec_num <= s_end:
            return title
    return "Part IX: Miscellaneous Provisions"

def compute_sha256(filepath: str) -> str:
    with open(filepath, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

def clean_text(raw: str) -> str:
    text = " ".join(raw.split())
    text = text.replace(r"\(", "(").replace(r"\)", ")")
    text = text.replace("\x00", "").replace("\r", " ")
    return " ".join(text.split())

def generate_plain_language(content: str, sec: str, sub: str) -> str:
    # Concise plain-English summary for voter readability
    if sec == "47" and sub == "2":
        return "The Presiding Officer must use BVAS (or other official electronic device) to verify and authenticate each voter before giving them a ballot paper."
    elif sec == "47" and sub == "1":
        return "You must go in person to your registered polling unit with your permanent voter card (PVC) to be accredited."
    elif sec == "47" and sub == "3":
        return "If the BVAS device breaks down and cannot be replaced the same day, election at that polling unit is postponed until the next day."
    elif sec == "50" and sub == "2":
        return "Voting and result transmission must follow the official procedures established by INEC."
    elif sec == "51" and sub == "2":
        return "If total votes cast exceed the number of accredited voters in a polling unit (over-voting), the election in that polling unit is cancelled."
    elif sec == "28":
        return "INEC must publish an official notice stating election dates and nomination venues at least 360 days before general elections."
    elif sec == "29":
        return "Only a party candidate who contested the party primaries has legal standing to challenge primary nomination affidavits at the Federal High Court."
    elif sec == "154":
        return "The Electoral Act 2022 is repealed. The Electoral Act 2026 is the governing law for elections across Nigeria."
    elif sec == "12":
        return "A Nigerian citizen aged 18 or older resident or originating from a constituency is entitled to register as a voter."
    elif sec == "60":
        return "The Presiding Officer counts votes openly, enters results in Form EC8A, and transmits results according to INEC guidelines."
    else:
        # Default plain summary trims leading legal boilerplate
        summary = content[:200]
        return summary + ("..." if len(content) > 200 else "")

def rebuild_corpus():
    print(f"Loading {GAZETTE_PDF}...")
    actual_sha256 = compute_sha256(GAZETTE_PDF)
    print(f"Verified SHA-256: {actual_sha256}")
    assert actual_sha256 == EXPECTED_GAZETTE_SHA256, (
        f"SHA256 mismatch! Expected {EXPECTED_GAZETTE_SHA256}, got {actual_sha256}"
    )

    reader = pypdf.PdfReader(GAZETTE_PDF)
    total_pages = len(reader.pages)
    print(f"Total pages in Gazette: {total_pages}")
    assert total_pages == 121, f"Expected 121 pages, got {total_pages}"

    # Exclude Table of Contents (Pages 3 to 8, index 2 to 7)
    # Main Act: Pages 9 to 74 (index 8 to 73)
    main_text = ""
    for p_idx in range(8, 74):
        p_num = p_idx + 1
        page_txt = reader.pages[p_idx].extract_text()
        main_text += f"\n<<<PAGE_{p_num}>>>\n" + page_txt

    # Parse Sections 1 to 156
    sec_positions = []
    for sec in range(1, 157):
        pattern = rf'(?:^|\n)\s*{sec}\s*[\.—\-]\s*(?:\((\d+)\))?'
        m = re.search(pattern, main_text)
        if m:
            sec_positions.append((sec, m.start()))
        else:
            print(f"Warning: Section {sec} anchor not found directly")

    sec_positions.sort(key=lambda x: x[1])
    print(f"Located {len(sec_positions)} sections in Main Body.")

    chunks: List[Dict[str, Any]] = []
    seen_ids: Set[str] = set()

    for i, (sec, pos) in enumerate(sec_positions):
        next_pos = sec_positions[i+1][1] if i + 1 < len(sec_positions) else len(main_text)
        sec_raw = main_text[pos:next_pos]

        # Determine page number
        prev_pages = re.findall(r'<<<PAGE_(\d+)>>>', main_text[:pos+50])
        page = int(prev_pages[-1]) if prev_pages else 9

        # Clean out page anchors
        cleaned_sec = re.sub(r'<<<PAGE_\d+>>>\n', '', sec_raw).strip()
        part_title = get_part_title(sec)

        # Look for subsections: e.g. (1), (2), (3) starting with capital letter
        sub_pattern = re.compile(
            r'(?:^|\n)\s*(?:\d{1,3}\s*[\.—\-\u2014\u2013]+\s*)?\((\d{1,2})\)\s+([A-Z].*?)(?=(?:\n\s*(?:\d{1,3}\s*[\.—\-\u2014\u2013]+\s*)?\(\d{1,2}\)\s+[A-Z]|\Z))',
            re.DOTALL
        )
        sub_matches = list(sub_pattern.finditer(cleaned_sec))

        if len(sub_matches) > 1:
            for sm in sub_matches:
                sub_num = sm.group(1)
                content = clean_text(sm.group(2))
                cid = f"EA2026-S{sec}-SS{sub_num}"
                if cid in seen_ids:
                    raise ValueError(f"Duplicate chunk ID: {cid}")
                seen_ids.add(cid)

                plain = generate_plain_language(content, str(sec), str(sub_num))
                chunks.append({
                    "chunk_id": cid,
                    "document_title": "Electoral Act 2026",
                    "document_source_url": GAZETTE_URL,
                    "document_sha256": actual_sha256,
                    "document_version": "Official Gazette No. 40, Vol. 113",
                    "retrieval_date": RETRIEVAL_DATE,
                    "part_title": part_title,
                    "section_number": str(sec),
                    "subsection_number": str(sub_num),
                    "page": page,
                    "content_english": content,
                    "content_plain": plain,
                    "legal_status": "ENACTED"
                })
        else:
            # Single section chunk
            cid = f"EA2026-S{sec}-SS1"
            if cid in seen_ids:
                raise ValueError(f"Duplicate chunk ID: {cid}")
            seen_ids.add(cid)

            content = clean_text(cleaned_sec)
            plain = generate_plain_language(content, str(sec), "1")
            chunks.append({
                "chunk_id": cid,
                "document_title": "Electoral Act 2026",
                "document_source_url": GAZETTE_URL,
                "document_sha256": actual_sha256,
                "document_version": "Official Gazette No. 40, Vol. 113",
                "retrieval_date": RETRIEVAL_DATE,
                "part_title": part_title,
                "section_number": str(sec),
                "subsection_number": "1",
                "page": page,
                "content_english": content,
                "content_plain": plain,
                "legal_status": "ENACTED"
            })

    print(f"Extracted {len(chunks)} chunks from Main Act Body.")

    # First Schedule: Pages 75 to 113 (index 74 to 112)
    # Rules of Procedure for Election Petitions (Paragraphs 1 to 55)
    sch1_text = ""
    for p_idx in range(74, 113):
        p_num = p_idx + 1
        page_txt = reader.pages[p_idx].extract_text()
        sch1_text += f"\n<<<PAGE_{p_num}>>>\n" + page_txt

    para_positions = []
    for p_num in range(1, 56):
        pattern = rf'(?:^|\n)\s*{p_num}\s*[\.—\-]\s*(?:\((\d+)\))?'
        m = re.search(pattern, sch1_text)
        if m:
            para_positions.append((p_num, m.start()))

    para_positions.sort(key=lambda x: x[1])
    print(f"Located {len(para_positions)} paragraphs in First Schedule.")

    for i, (para, pos) in enumerate(para_positions):
        next_pos = para_positions[i+1][1] if i + 1 < len(para_positions) else len(sch1_text)
        para_raw = sch1_text[pos:next_pos]

        prev_pages = re.findall(r'<<<PAGE_(\d+)>>>', sch1_text[:pos+50])
        page = int(prev_pages[-1]) if prev_pages else 75

        cleaned_para = re.sub(r'<<<PAGE_\d+>>>\n', '', para_raw).strip()
        part_title = "First Schedule: Rules of Procedure for Election Petitions"

        # Unique chunk ID for First Schedule: e.g. EA2026-SCH1-P7
        cid = f"EA2026-SCH1-P{para}"
        if cid in seen_ids:
            raise ValueError(f"Duplicate chunk ID: {cid}")
        seen_ids.add(cid)

        content = clean_text(cleaned_para)
        plain = f"First Schedule Paragraph {para} provides official procedural rules for election petitions filed under the Electoral Act 2026."
        chunks.append({
            "chunk_id": cid,
            "document_title": "Electoral Act 2026 (First Schedule)",
            "document_source_url": GAZETTE_URL,
            "document_sha256": actual_sha256,
            "document_version": "Official Gazette No. 40, Vol. 113",
            "retrieval_date": RETRIEVAL_DATE,
            "part_title": part_title,
            "section_number": f"SCH1-P{para}",
            "subsection_number": None,
            "page": page,
            "content_english": content,
            "content_plain": plain,
            "legal_status": "ENACTED"
        })

    print(f"Total chunks in Electoral Act corpus: {len(chunks)}")
    print(f"Unique chunk IDs count: {len(seen_ids)} (all unique)")

    # Hard Constraint: Write ONLY through this script
    os.makedirs("data/processed", exist_ok=True)
    out_file = "data/processed/electoral_act_2026.jsonl"
    with open(out_file, "w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    print(f"Successfully generated {out_file} with {len(chunks)} chunks.")

    # Process INEC Electronic Transmission Procedure PDF if present
    if os.path.exists(TRANSMISSION_PDF):
        trans_sha256 = compute_sha256(TRANSMISSION_PDF)
        trans_reader = pypdf.PdfReader(TRANSMISSION_PDF)
        trans_chunks = []
        for p_idx, page in enumerate(trans_reader.pages):
            p_text = clean_text(page.extract_text())
            if len(p_text) > 40:
                cid = f"INEC2026-ET-PAGE{p_idx+1}"
                trans_chunks.append({
                    "chunk_id": cid,
                    "document_title": "INEC Electronic Transmission & Collation Procedure (2026)",
                    "document_source_url": TRANSMISSION_URL,
                    "document_sha256": trans_sha256,
                    "document_version": "Official Publication (Rev 5)",
                    "retrieval_date": RETRIEVAL_DATE,
                    "part_title": "Electronic Transmission Procedure",
                    "section_number": f"PAGE-{p_idx+1}",
                    "subsection_number": None,
                    "page": p_idx + 1,
                    "content_english": p_text,
                    "content_plain": f"Official INEC procedure specifying step-by-step electronic transmission from polling unit BVAS to collation servers.",
                    "legal_status": "ENACTED"
                })
        with open("data/processed/inec_transmission_procedure.jsonl", "w", encoding="utf-8") as f:
            for tc in trans_chunks:
                f.write(json.dumps(tc, ensure_ascii=False) + "\n")
        print(f"Successfully generated inec_transmission_procedure.jsonl with {len(trans_chunks)} chunks.")

    # Validate and cleanup any files without source URL and retrieval date
    bulletins_path = "data/processed/inec_bulletins.jsonl"
    if os.path.exists(bulletins_path):
        valid = True
        with open(bulletins_path, "r", encoding="utf-8") as bf:
            for l in bf:
                if l.strip():
                    rec = json.loads(l)
                    if not rec.get("source_url") or not rec.get("retrieval_date"):
                        valid = False
        if not valid:
            os.remove(bulletins_path)
            print(f"Removed invalid bulletins file: {bulletins_path}")

    # inec_guidelines_2026 was handwritten and lacked underlying raw PDF
    if os.path.exists("data/processed/inec_guidelines_2026.jsonl"):
        os.remove("data/processed/inec_guidelines_2026.jsonl")

if __name__ == "__main__":
    rebuild_corpus()
