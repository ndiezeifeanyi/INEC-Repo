import json
from pathlib import Path

def main():
    base_dir = Path(__file__).resolve().parent.parent

    # Load corpus chunks
    corpus = {}
    with open(base_dir / "data" / "processed" / "electoral_act_2026.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                c = json.loads(line)
                corpus[c["chunk_id"]] = c

    # Load FAQ library
    with open(base_dir / "data" / "processed" / "reviewed_faq_library.json", "r", encoding="utf-8") as f:
        faq_data = json.load(f)

    md = []
    md.append("# Civic FAQ Library Statutory Verification Table\n")
    md.append("> **Auditable Statutory Grounding**: Each pre-reviewed FAQ entry presented side-by-side with its official statutory chunk from the Federal Republic of Nigeria Official Gazette No. 15, Vol. 113 (Electoral Act 2026).\n")
    md.append("> **Review Status Policy**: All English entries are categorized as `DEVELOPER_DRAFT_PENDING_HUMAN_VERIFICATION`. Indigenous language entries (Hausa, Yoruba, Igbo) are categorized as `UNREVIEWED_DEVELOPER_DRAFT` and displayed alongside the verbatim English statutory text.\n\n")

    md.append("| FAQ ID | Statutory Section | Chunk ID | Verbatim Gazette Chunk Text | FAQ Plain Explanation | Review Status |")
    md.append("|---|---|---|---|---|---|")

    for item in faq_data["faqs"]:
        fid = item["id"]
        sec = item["statutory_section"]
        cid = item["chunk_id"]
        chunk = corpus.get(cid, {})
        gazette_text = chunk.get("content_english", "CHUNK NOT FOUND").replace("\n", " ").strip()
        faq_expl = item["english"]["short_explanation"].replace("\n", " ").strip()
        status = item["english"]["review_status"]

        # Escape pipes
        gazette_text_esc = gazette_text.replace("|", "\\|")
        faq_expl_esc = faq_expl.replace("|", "\\|")

        md.append(f"| `{fid}` | {sec} | `{cid}` | \"{gazette_text_esc}\" | {faq_expl_esc} | `{status}` |")

    md.append("\n## Fast-Path Matching & Safeguard Routing Architecture\n")
    md.append("1. **Negative Exclusion Filters**: Any query referencing offences (bribes, vote buying, forging documents, penalties, fines, imprisonment) or election petition tribunals is instantly blocked from matching the FAQ fast-path.\n")
    md.append("2. **Safeguard Routing Priority**:\n")
    md.append("   - **Stage 1 (Refusal Guard)**: Checks for candidate comparisons, partisan preferences, and election result predictions.\n")
    md.append("   - **Stage 2 (Unconfirmed Amendments Guard)**: Detects proposed amendments (e.g. Section 29A) and enforces `STATUS_UNCONFIRMED_CHECK_GAZETTE`.\n")
    md.append("   - **Stage 3 (FAQ Fast-Path Lookup)**: Matches verified civic administrative topics with strict token overlap and negative exclusion.\n")
    md.append("   - **Stage 4 (Neural/Lexical Hybrid Retrieval)**: Falls through for general statutory provisions with score-gap abstention.\n")

    out_path = base_dir / "docs" / "faq_verification.md"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")

    print(f"Generated {out_path} with {len(faq_data['faqs'])} entries.")

if __name__ == "__main__":
    main()
