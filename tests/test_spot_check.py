import pytest
from src.retrieval.translate_hybrid import TranslationHybridRetriever
from src.generation.prompt_builder import GroundedAnswerGenerator

def test_spot_check_result_transmission():
    """
    Spot-check test for Result Transmission.
    Gazette Citation:
      - Section 60(3) (Gazette Page 28-29): Mandates electronic transmission of polling unit results
        to IREV portal after Form EC8A is signed and stamped.
      - Section 50(2) (Gazette Page 26): Mandates voting and transmission of results under the Act
        shall be in accordance with procedure determined by the Commission.
    """
    retriever = TranslationHybridRetriever()
    
    # Query 1: Result transmission to IReV
    results = retriever.retrieve("electronic transmission results Form EC8A IREV portal", top_k=3)
    top_chunk_ids = [chunk.chunk_id for chunk, _ in results]
    top_sections = [chunk.section_number for chunk, _ in results]
    
    # Verify either Section 60(3) or Section 50(2) is in the top-3 results
    assert any(cid in ["EA2026-S60-SS3", "EA2026-S50-SS2"] or sec in ["60", "50"] 
               for cid, sec in zip(top_chunk_ids, top_sections)), \
        f"Expected Section 60 or 50 in top results for result transmission, got: {top_chunk_ids}"

def test_spot_check_voter_accreditation():
    """
    Spot-check test for Voter Accreditation.
    Gazette Citation:
      - Section 47(1) (Gazette Page 25): Requires voter to present himself with permanent voters card (PVC).
      - Section 47(2) (Gazette Page 25): Mandates use of Bimodal Voter Accreditation System (BVAS)
        to verify, confirm, or authenticate voter particulars.
    """
    retriever = TranslationHybridRetriever()
    
    # Query 2: Voter accreditation with PVC and BVAS
    results = retriever.retrieve("voter accreditation permanent voters card PVC BVAS", top_k=3)
    top_chunk_ids = [chunk.chunk_id for chunk, _ in results]
    top_sections = [chunk.section_number for chunk, _ in results]
    
    # Verify Section 47(1) or 47(2) is in top results
    assert any(cid in ["EA2026-S47-SS1", "EA2026-S47-SS2", "EA2026-S47-SS3"] or sec == "47"
               for cid, sec in zip(top_chunk_ids, top_sections)), \
        f"Expected Section 47 in top results for voter accreditation, got: {top_chunk_ids}"

def test_spot_check_natural_queries():
    """
    Spot-check test with natural language English queries (no section words or statutory jargon).
    Reports results honestly across key civic areas:
      1. Over-voting cancellation -> Target: Section 51(2)
      2. Notice of election requirement -> Target: Section 28(1)
      3. Primary election challenge standing -> Target: Section 29(5)
      4. Result transmission -> Target: Section 60(3)
      5. Voter accreditation / PVC -> Target: Section 47(1)-(2)
    """
    retriever = TranslationHybridRetriever()
    
    # 1. Over-voting natural query
    res_ov = retriever.retrieve("What happens if more ballots are counted than accredited voters at a polling station?", top_k=3)
    ov_cids = [c.chunk_id for c, _ in res_ov]
    assert "EA2026-S51-SS2" in ov_cids, f"Expected Section 51(2) in top-3 for over-voting, got: {ov_cids}"

    # 2. Notice of election natural query
    res_notice = retriever.retrieve("How many days before the election must the commission publish the official notice?", top_k=3)
    notice_cids = [c.chunk_id for c, _ in res_notice]
    assert "EA2026-S28-SS1" in notice_cids, f"Expected Section 28(1) in top-3 for election notice, got: {notice_cids}"

    # 3. Primary election challenge standing natural query
    res_primary = retriever.retrieve("Who is allowed to challenge the outcome of a political party primary election in court?", top_k=3)
    primary_cids = [c.chunk_id for c, _ in res_primary]
    assert any("EA2026-S29" in cid for cid in primary_cids), f"Expected Section 29 in top-3 for primary challenge, got: {primary_cids}"

    # 4. Result transmission natural query
    res_trans = retriever.retrieve("How are election scores sent from polling booths to the national portal?", top_k=3)
    trans_cids = [c.chunk_id for c, _ in res_trans]
    assert any(cid in ["EA2026-S60-SS3", "EA2026-S62-SS4", "INEC2026-ET-PAGE3"] for cid in trans_cids), f"Expected result transmission provision in top-3, got: {trans_cids}"

    # 5. Voter card requirement natural query (restored)
    res_card = retriever.retrieve("Can I vote if I do not have my permanent voter card on election day?", top_k=5)
    card_cids = [c.chunk_id for c, _ in res_card]
    card_secs = [c.section_number for c, _ in res_card]
    assert any(cid in ["EA2026-S47-SS1", "EA2026-S47-SS3"] or sec == "47" for cid, sec in zip(card_cids, card_secs)), \
        f"Expected Section 47 (accreditation/PVC) in retrieved results for voter card query, got: {card_cids}"

def test_spot_check_real_time_upload_requirement():
    """
    Test requirement:
      'Must results be uploaded in real time?' must return Section 60(3) and state
      that the enacted text sets no real-time requirement.
      Print the proviso verbatim from the Gazette chunk.
    """
    retriever = TranslationHybridRetriever()
    generator = GroundedAnswerGenerator()
    query = "Must results be uploaded in real time?"

    # 1. Retrieve
    retrieved = retriever.retrieve(query, top_k=3, lang="en")
    top_cids = [c.chunk_id for c, _ in retrieved]
    assert "EA2026-S60-SS3" in top_cids, f"Expected Section 60(3) in top-3 for real-time query, got: {top_cids}"

    # 2. Extract top chunk (Section 60(3))
    s60_chunk = next(c for c, _ in retrieved if c.chunk_id == "EA2026-S60-SS3")
    assert s60_chunk.section_number == "60"
    assert s60_chunk.subsection_number == "3"

    # 3. Verify enacted text sets no 'real-time' or 'real time' requirement
    enacted_text = s60_chunk.content_english
    assert "real time" not in enacted_text.lower()
    assert "real-time" not in enacted_text.lower()

    # 4. Verify transmission timing is conditional on Form EC8A signing
    assert "shall be done after the prescribed Form EC8A has been signed and stamped" in enacted_text

    # 5. Extract and print verbatim proviso from Gazette chunk
    proviso_start = enacted_text.index("Provided that")
    verbatim_proviso = enacted_text[proviso_start:]
    print("\n" + "="*80)
    print("VERBATIM PROVISO FROM GAZETTE CHUNK (EA2026-S60-SS3, Page 28-29):")
    print(verbatim_proviso)
    print("="*80 + "\n")

    # Assert proviso content
    assert "communication failure" in verbatim_proviso
    assert "Form EC8A shall at all times remain the primary source of collation" in verbatim_proviso

if __name__ == "__main__":
    test_spot_check_result_transmission()
    test_spot_check_voter_accreditation()
    test_spot_check_natural_queries()
    print("Spot-check tests passed successfully.")

