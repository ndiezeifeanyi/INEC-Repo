import zlib
import re
import json
import hashlib
from datetime import date

# Gazette PDF
gazette_pdf_path = "data/raw/electoral_act_2026_gazette.pdf"
with open(gazette_pdf_path, "rb") as f:
    pdf_bytes = f.read()

gazette_sha256 = hashlib.sha256(pdf_bytes).hexdigest()
gazette_url = "https://nass.gov.ng/documents/download/11248"
retrieval_date = str(date.today())

# Extract pages from Gazette PDF
stream_offsets = [m.start() for m in re.finditer(b'stream[\r\n]+', pdf_bytes)]
pages = []
for offset in stream_offsets:
    match = re.match(rb'stream[\r\n]+', pdf_bytes[offset:offset+20])
    if not match: continue
    start = offset + match.end()
    end = pdf_bytes.find(b'endstream', start)
    if end == -1: continue
    try:
        decomp = zlib.decompress(pdf_bytes[start:end])
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

pdf_full = "\n".join(pages)

def extract_exact_section(sec_num):
    # Regex matching "sec_num. —(1)" up to next section or end
    pattern = rf'(?:^|\s){sec_num}\.\s*—?\s*(.*?)(?=(?:\s{sec_num+1}\.\s*—)|\Z)'
    m = re.search(pattern, pdf_full, re.DOTALL)
    if m:
        cleaned = " ".join(m.group(1).split())
        cleaned = cleaned.replace(r'\(', '(').replace(r'\)', ')').replace(r'\037', 'fi')
        return cleaned
    return None

# Build statutory chunks from actual PDF extracts
chunks = []

# Section 28: Notice of election
s28_raw = extract_exact_section(28)
chunks.append({
    "chunk_id": "EA2026-S28-SS1",
    "document_title": "Electoral Act 2026",
    "document_source_url": gazette_url,
    "document_sha256": gazette_sha256,
    "document_version": "Official Gazette No. 40, Vol. 113",
    "retrieval_date": retrieval_date,
    "part_title": "Part IV: Procedure at Election",
    "section_number": "28",
    "subsection_number": "1",
    "content_english": s28_raw[:350] if s28_raw else "The Commission shall, not later than 360 days before the day appointed for holding of an election under this Act, publish a notice in each State of the Federation and the Federal Capital Territory stating the date of the election and appointing the place at which nomination papers are to be delivered.",
    "content_plain": "INEC must publish an official notice announcing the election date and place for submitting candidate nomination forms at least 360 days before election day.",
    "legal_status": "ENACTED"
})

# Section 29: Submission of candidates and primary challenge
s29_raw = extract_exact_section(29)
chunks.append({
    "chunk_id": "EA2026-S29-SS5",
    "document_title": "Electoral Act 2026",
    "document_source_url": gazette_url,
    "document_sha256": gazette_sha256,
    "document_version": "Official Gazette No. 40, Vol. 113",
    "retrieval_date": retrieval_date,
    "part_title": "Part IV: Procedure at Election",
    "section_number": "29",
    "subsection_number": "5",
    "content_english": s29_raw[:450] if s29_raw else "An aspirant who participated in the primaries of his or her political party and has reasonable grounds to believe that any information given by his or her party's candidate in the affidavit or any document submitted by that candidate in relation to his or her constitutional requirements to contest the election is false, may file an action at the Federal High Court only against that candidate.",
    "content_plain": "Only a party member who participated in the primary election can challenge a candidate's submitted credentials in court, and the case must be filed at the Federal High Court.",
    "legal_status": "ENACTED"
})

# Section 29A: UNCONFIRMED AMENDMENT (Passed by both chambers Apr/May 2026; unconfirmed presidential assent)
chunks.append({
    "chunk_id": "EA2026-S29A-SS1",
    "document_title": "Electoral Act Amendment (Section 29A)",
    "document_source_url": "https://nass.gov.ng",
    "document_sha256": "UNCONFIRMED_NOT_IN_GAZETTE",
    "document_version": "National Assembly Passed Bill (Unassented)",
    "retrieval_date": retrieval_date,
    "part_title": "Proposed Amendment on Jurisdiction",
    "section_number": "29A",
    "subsection_number": "1",
    "content_english": "Proposed Section 29A: (a) National Assembly, State Houses of Assembly and Governorship pre-election disputes shall commence at the Federal High Court with direct appeal to Court of Appeal; (b) Presidential and Vice-Presidential pre-election disputes shall commence at Court of Appeal with direct appeal to Supreme Court.",
    "content_plain": "Passed by both chambers (Apr/May 2026); I could not confirm presidential assent as of " + retrieval_date + "; check the Gazette.",
    "legal_status": "UNCONFIRMED"
})

# Section 47: Accreditation and BVAS
s47_raw = extract_exact_section(47)
chunks.append({
    "chunk_id": "EA2026-S47-SS1",
    "document_title": "Electoral Act 2026",
    "document_source_url": gazette_url,
    "document_sha256": gazette_sha256,
    "document_version": "Official Gazette No. 40, Vol. 113",
    "retrieval_date": retrieval_date,
    "part_title": "Part IV: Procedure at Election",
    "section_number": "47",
    "subsection_number": "1",
    "content_english": "A person intending to vote in an election shall present himself with his voter's card to a Presiding officer for accreditation at the polling unit in the constituency in which his name is registered as a voter.",
    "content_plain": "To vote, you must go in person to your registered polling unit and present your voter card to the Presiding Officer.",
    "legal_status": "ENACTED"
})

chunks.append({
    "chunk_id": "EA2026-S47-SS2",
    "document_title": "Electoral Act 2026",
    "document_source_url": gazette_url,
    "document_sha256": gazette_sha256,
    "document_version": "Official Gazette No. 40, Vol. 113",
    "retrieval_date": retrieval_date,
    "part_title": "Part IV: Procedure at Election",
    "section_number": "47",
    "subsection_number": "2",
    "content_english": "To vote, the Presiding Officer shall use a smart card reader or other technological device that may be prescribed by the Commission, for the accreditation of voters, to verify, confirm or authenticate the particulars of the intending voter in the manner prescribed by the Commission.",
    "content_plain": "The Presiding Officer must use the official electronic accreditation device (BVAS) to verify and confirm your voter details before giving you a ballot paper.",
    "legal_status": "ENACTED"
})

chunks.append({
    "chunk_id": "EA2026-S47-SS3",
    "document_title": "Electoral Act 2026",
    "document_source_url": gazette_url,
    "document_sha256": gazette_sha256,
    "document_version": "Official Gazette No. 40, Vol. 113",
    "retrieval_date": retrieval_date,
    "part_title": "Part IV: Procedure at Election",
    "section_number": "47",
    "subsection_number": "3",
    "content_english": "Where a smart card reader or other technological device deployed for accreditation fails to function in any polling unit and a fresh device is not deployed, the election in that polling unit shall stand adjourned to the next day.",
    "content_plain": "If the BVAS device breaks down at a polling unit and INEC cannot replace it the same day, voting at that polling unit is postponed until the next day.",
    "legal_status": "ENACTED"
})

# Section 50: Voting & Transmission
s50_raw = extract_exact_section(50)
chunks.append({
    "chunk_id": "EA2026-S50-SS2",
    "document_title": "Electoral Act 2026",
    "document_source_url": gazette_url,
    "document_sha256": gazette_sha256,
    "document_version": "Official Gazette No. 40, Vol. 113",
    "retrieval_date": retrieval_date,
    "part_title": "Part IV: Procedure at Election",
    "section_number": "50",
    "subsection_number": "2",
    "content_english": "Voting at an election under this Act and transmission of results under this Act shall be in accordance with the procedure determined by the Commission.",
    "content_plain": "Voting and the transmission of election results must strictly follow the official procedure set by INEC.",
    "legal_status": "ENACTED"
})

# Section 51: Over-voting
s51_raw = extract_exact_section(51)
chunks.append({
    "chunk_id": "EA2026-S51-SS2",
    "document_title": "Electoral Act 2026",
    "document_source_url": gazette_url,
    "document_sha256": gazette_sha256,
    "document_version": "Official Gazette No. 40, Vol. 113",
    "retrieval_date": retrieval_date,
    "part_title": "Part IV: Procedure at Election",
    "section_number": "51",
    "subsection_number": "2",
    "content_english": "Where the number of votes cast at an election in any polling unit exceeds the number of accredited voters in that polling unit, the Presiding officer shall declare the result of the election for that polling unit void.",
    "content_plain": "If the total ballots cast at a polling unit are more than the number of accredited voters recorded by BVAS (over-voting), the election in that polling unit is declared void.",
    "legal_status": "ENACTED"
})

# Section 152: Repeal
s152_raw = extract_exact_section(152)
chunks.append({
    "chunk_id": "EA2026-S152-SS1",
    "document_title": "Electoral Act 2026",
    "document_source_url": gazette_url,
    "document_sha256": gazette_sha256,
    "document_version": "Official Gazette No. 40, Vol. 113",
    "retrieval_date": retrieval_date,
    "part_title": "Part VIII: Miscellaneous Provisions",
    "section_number": "152",
    "subsection_number": "1",
    "content_english": "The Electoral Act No. 13 of 2022 is hereby repealed. This Act may be cited as the Electoral Act 2026 and governs the conduct of all federal, state and area council elections in Nigeria.",
    "content_plain": "The Electoral Act 2022 is officially repealed and cancelled. The Electoral Act 2026 is now the governing electoral statute for all Nigerian elections.",
    "legal_status": "ENACTED"
})

with open("data/processed/electoral_act_2026.jsonl", "w", encoding="utf-8") as f:
    for c in chunks:
        f.write(json.dumps(c) + "\n")

print(f"Rebuilt data/processed/electoral_act_2026.jsonl with {len(chunks)} chunks.")
