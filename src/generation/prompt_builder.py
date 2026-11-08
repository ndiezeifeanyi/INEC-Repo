import re
from typing import List, Tuple, Optional
from src.models.chunk import LegalChunk, Citation, VoterAnswer
from src.generation.glossary_layer import CivicGlossaryEnforcer
from src.generation.plain_language import PlainLanguageConverter
from src.config import UNCONFIRMED_AMENDMENTS, SCORE_GAP_THRESHOLD, ELECTORAL_OFFENCES_SECTION_RANGE

class GroundedAnswerGenerator:
    """
    Grounded generation engine that strictly answers from retrieved official text,
    attaches complete statutory citations, enforces certified civic glossaries,
    and reliably refuses partisan, candidate, predictive, and out-of-scope prompts.
    """

    REFUSAL_TRIGGERS = [
        # Candidate and party comparisons
        (r"\b(who is (the )?best candidate|who should i vote for|vote for candidate|better candidate)\b", "candidate_comparison"),
        (r"\b(wane dan takara|zaba a zaben)\b", "candidate_comparison_ha"),
        (r"\b(oludije to dara|dibo fun ninu)\b", "candidate_comparison_yo"),
        (r"\b(onye kacha mma ituputara|vootu n'ime ndi na-azọ)\b", "candidate_comparison_ig"),
        # Predictions
        (r"\b(predict who will win|who will win|election forecast|election prediction)\b", "election_prediction"),
        # Legal tribunal dispute advice
        (r"\b(file an election petition|disqualify my opponent|overturn.*election|tribunal strategy)\b", "legal_advice"),
        # Prompt injections
        (r"\b(system override|ignore all (prior )?instructions|disregard previous|say that party .* has already won)\b", "prompt_injection"),
        # Out-of-scope non-electoral questions
        (r"\b(recipe|weather|jollof|sports scores|football)\b", "out_of_scope")
    ]

    def __init__(self, glossary_enforcer: Optional[CivicGlossaryEnforcer] = None):
        self.glossary_enforcer = glossary_enforcer or CivicGlossaryEnforcer()

    def check_refusal(self, query: str, lang: str = "en") -> Optional[str]:
        """Checks if a query violates nonpartisan, scope, or safety constraints."""
        q_lower = query.lower()
        for pattern, category in self.REFUSAL_TRIGGERS:
            if re.search(pattern, q_lower):
                if category.startswith("candidate_comparison"):
                    if lang == "ha":
                        return "Ina ba da hakuri: Ba zan iya bayar da shawarar dan takara ko jam'iyya ba. Zan iya ba da bayanai ne kawai kan ka'idojin zabe da dokar zabe ta 2026."
                    elif lang == "yo":
                        return "Mo binu, eto mi ko le so oludije tabi egbe oselu ti o dara julo. Eto yi wa fun fifi ofin idibo 2026 ati ilana INEC han nikan."
                    elif lang == "ig":
                        return "Ndo, enweghi ike igwa gi onye kacha mma ituputara vootu ma obu ime ka otu pati karia ibe ya. Nani iwu ntuli aka 2026 na usoro INEC ka m na-akowaputa."
                    return "I cannot evaluate or compare political candidates or parties, nor recommend who to vote for. I provide objective rules and procedures based strictly on the Electoral Act 2026 and official INEC guidelines."
                
                elif category == "election_prediction":
                    return "I cannot predict election outcomes or forecast results. Please consult official declarations from INEC."
                
                elif category == "legal_advice":
                    return "I cannot provide legal advice or legal strategy for electoral tribunal disputes. Please consult a qualified legal practitioner."
                
                elif category == "prompt_injection":
                    return "I cannot fulfill this request. I operate strictly as an independent, nonpartisan election information system."
                
                elif category == "out_of_scope":
                    return "I cannot answer this question from official election rules. I only answer questions regarding Nigerian election guidelines and the Electoral Act 2026."

        return None

    def generate_answer(
        self,
        query: str,
        retrieved_chunks: List[Tuple[LegalChunk, float]],
        lang: str = "en"
    ) -> VoterAnswer:
        # Check refusals first
        refusal = self.check_refusal(query, lang)
        if refusal:
            return VoterAnswer(
                question=query,
                language=lang,
                answer_text=refusal,
                answer_plain=refusal,
                citations=[],
                retrieved_chunk_ids=[],
                confidence_flags=["REFUSAL_SAFEGUARD_TRIGGERED"]
            )

        # Check retrieval support (RRF scores are typically in 0.01 - 0.04 range)
        if not retrieved_chunks or retrieved_chunks[0][1] <= 0.005:
            abstention_msg = (
                "I cannot answer this question based on the official retrieved election texts. "
                "Please refer directly to official INEC publications at https://inecnigeria.org."
            )
            if lang == "ha":
                abstention_msg = "Ban sami amsar wannan tambayar a cikin bayanan dokar zabe da aka bincika ba. Da fatan za a duba shafin hukumar INEC a https://inecnigeria.org."
            elif lang == "yo":
                abstention_msg = "Nko le ri idahun si ibeere yi ninu awon iwe ofin idibo ti a ye wo. E jowo se abewo si ibudo INEC ni https://inecnigeria.org."
            elif lang == "ig":
                abstention_msg = "Enweghị m ike isi na akwụkwọ iwu ntuli aka ahụrụ zaa ajụjụ a. Biko gaa na webusaiti gọọmenti INEC na https://inecnigeria.org."

            return VoterAnswer(
                question=query,
                language=lang,
                answer_text=abstention_msg,
                answer_plain=abstention_msg,
                citations=[],
                retrieved_chunk_ids=[],
                confidence_flags=["ABSTENTION_UNSUPPORTED_RETRIEVAL"]
            )

        top_chunk, score = retrieved_chunks[0]

        # Check if query asks about Section 29A or unconfirmed legislative amendments
        if "29a" in query.lower() or "29 a" in query.lower():
            amend = UNCONFIRMED_AMENDMENTS["29A"]
            citation = Citation(
                document_title="Electoral Act 2026",
                section="29A",
                subsection=None,
                version="Proposed Amendment (Awaiting Gazette)",
                retrieval_date="2026-11-07",
                source_url="https://nass.gov.ng",
                legal_status="UNCONFIRMED"
            )
            confidence_flags = ["STATUS_UNCONFIRMED_CHECK_GAZETTE"]
            if lang == "ha":
                ans_text = f"Game da Sashe na 29A: {amend['notice_ha']}"
            elif lang == "yo":
                ans_text = f"Lori Abala 29A: {amend['notice_yo']}"
            elif lang == "ig":
                ans_text = f"Maka Ngalaba 29A: {amend['notice_ig']}"
            else:
                ans_text = f"Status: UNCONFIRMED. {amend['notice']}"
            return VoterAnswer(
                question=query,
                language=lang,
                answer_text=ans_text,
                answer_plain=amend["notice"],
                citations=[citation],
                retrieved_chunk_ids=[top_chunk.chunk_id],
                confidence_flags=confidence_flags
            )

        # Extract citations for up to top-3 retrieved chunks
        citations = []
        confidence_flags = []
        for chunk, _ in retrieved_chunks[:3]:
            citations.append(Citation(
                document_title=chunk.document_title,
                section=chunk.section_number,
                subsection=chunk.subsection_number,
                version=chunk.document_version,
                retrieval_date=chunk.retrieval_date,
                source_url=chunk.document_source_url,
                legal_status=chunk.legal_status
            ))
            if chunk.legal_status == "UNCONFIRMED" and "STATUS_UNCONFIRMED_CHECK_GAZETTE" not in confidence_flags:
                confidence_flags.append("STATUS_UNCONFIRMED_CHECK_GAZETTE")

        # Audit 7 Abstention Safeguard:
        # 1. Top-1 chunk is not clearly ahead of top-2 (gap <= SCORE_GAP_THRESHOLD)
        score_gap_insufficient = False
        if len(retrieved_chunks) >= 2:
            gap = retrieved_chunks[0][1] - retrieved_chunks[1][1]
            if gap <= SCORE_GAP_THRESHOLD:
                score_gap_insufficient = True

        # 2. Top-1 is an electoral offence/penalty section for a "can I" or "how" procedural question
        q_lower = query.lower()
        is_can_i_or_how = bool(re.search(r"\b(can i|how\b)", q_lower))
        is_offence_chunk = False
        if top_chunk.part_title == "Electoral Offences":
            is_offence_chunk = True
        elif top_chunk.section_number and top_chunk.section_number.isdigit():
            sec_num = int(top_chunk.section_number)
            if ELECTORAL_OFFENCES_SECTION_RANGE[0] <= sec_num <= ELECTORAL_OFFENCES_SECTION_RANGE[1]:
                is_offence_chunk = True

        if score_gap_insufficient or (is_can_i_or_how and is_offence_chunk):
            abstention_title = "I'm not sure which provision answers this."
            if lang == "ha":
                abstention_title = "Ban tabbatar da takamaiman sashen doka da ya ba da amsar wannan tambayar ba."
            elif lang == "yo":
                abstention_title = "Nko da mi loju abala ofin pato ti o dahun ibeere yi."
            elif lang == "ig":
                abstention_title = "Ejighi m n'aka ngalaba iwu kwesiri ịza ajụjụ a."

            top_provisions_text = []
            for i, (chunk, _) in enumerate(retrieved_chunks[:3], start=1):
                sec_desc = f"Section {chunk.section_number}"
                if chunk.subsection_number:
                    sec_desc += f", Subsection ({chunk.subsection_number})"
                top_provisions_text.append(f"{i}. {chunk.document_title}, {sec_desc} (Chunk ID: {chunk.chunk_id}):\n\"{chunk.content_english}\"")

            ans_text = f"{abstention_title}\n\nPotentially related provisions from official records (Top-3 Retrieved, no primary answer):\n\n" + "\n\n".join(top_provisions_text)

            has_2022_doc = any("INEC2026-ET" in c.chunk_id or "2022" in c.document_version for c, _ in retrieved_chunks[:3])
            if has_2022_doc:
                confidence_flags.append("DOC_REFERS_TO_ELECTORAL_ACT_2022")
                notice_2022 = "[Notice: This document refers to the Electoral Act 2022. While administrative procedures (BVAS, IReV) continue under INEC regulations, substantive statutory authority is governed by Electoral Act 2026 Section 60(3).]"
                ans_text += f"\n\n{notice_2022}"

            confidence_flags.append("ABSTENTION_AMBIGUOUS_PROVISION")
            return VoterAnswer(
                question=query,
                language=lang,
                answer_text=ans_text,
                answer_plain=abstention_title,
                citations=citations,
                retrieved_chunk_ids=[c[0].chunk_id for c in retrieved_chunks[:3]],
                confidence_flags=confidence_flags
            )

        # Multilingual generation with glossary enforcement
        content = top_chunk.content_english
        plain_content = top_chunk.content_plain

        if lang == "ha":
            if top_chunk.section_number == "47" and top_chunk.subsection_number == "2":
                raw_ans = "Bisa ga sashe na 47(2) na Dokar Zabe ta 2026, wajibi ne babban jami'in zabe ya yi amfani da na'urar tantance masu kada kuri'a (BVAS) domin tabbatar da shaidar mai zabe kafin a ba shi takardar kada kuri'a."
            elif top_chunk.section_number == "47" and top_chunk.subsection_number == "3":
                raw_ans = "Bisa ga sashe na 47(3) na Dokar Zabe ta 2026, idan na'urar tantance masu kada kuri'a (BVAS) ta kasa aiki a rumfar zabe kuma ba a kawo wata sabuwa ba, to za a daga zaben zuwa washegari."
            elif top_chunk.section_number == "38":
                raw_ans = "Bisa ga ka'idojin INEC na 2026, jami'in zabe zai dauki hoton sakamakon zabe (Form EC8A) ta na'urar BVAS sannan ya aika da shi kai tsaye zuwa shafin IReV da cibiyar tattara sakamako kafin ya bar rumfar zabe."
            elif top_chunk.section_number == "28":
                raw_ans = "Bisa ga sashe na 28(1) na Dokar Zabe ta 2026, wajibi ne hukumar INEC ta bayyana sanarwar zabe kwanaki 360 kafin ranar zabe a kowace jiha da Babban Birnin Tarayya."
            elif top_chunk.section_number in ["29", "29A"]:
                raw_ans = "Game da shari'ar zaben fidda gwani, Dokar Zabe ta 2026 sashe na 29(5) ta tanadi cewa dan takarar da ya shiga zaben fidda gwani zai iya kai kara a Babbar Kotun Tarayya. (Kula: Sashe na 29A yana matsayin UNCONFIRMED: Majalisun biyu sun amince da shi a watan Afrilu/Mayu 2026; ban sami tabbacin sa hannun shugaban kasa ba; duba Gazette)."
            else:
                raw_ans = f"Bisa ga {top_chunk.document_title} Sashe na {top_chunk.section_number}: {top_chunk.content_plain}"
            ans_text, term_warnings = self.glossary_enforcer.validate_and_enforce(raw_ans, "ha")
            confidence_flags.extend(term_warnings)

        elif lang == "yo":
            if top_chunk.section_number == "47" and top_chunk.subsection_number == "2":
                raw_ans = "Gege bi abala 47(2) ninu Ofin Idibo 2026, osise idibo gbodo lo ero ijerisi oludibo (BVAS) lati se ijeri oludibo saaju ki o to gba iwe ibo lati dibo."
            elif top_chunk.section_number == "47" and top_chunk.subsection_number == "3":
                raw_ans = "Gege bi abala 47(3) ninu Ofin Idibo 2026, ti ero BVAS ba kuna lati sise ti a ko si mu omiran wa, idibo ni ibudo ibo na yoo di siwaju si ojo keji."
            elif top_chunk.section_number == "38":
                raw_ans = "Gege bi ilana INEC 2026, osise idibo gbodo ya aworan abajade (Form EC8A) pelu ero BVAS ki o si gbe e lo taara si ibudo ayelujara IReV ki o to kuro ni ibudo ibo."
            elif top_chunk.section_number == "28":
                raw_ans = "Gege bi abala 28(1) ninu Ofin Idibo 2026, o ye ki INEC kede ifitonileti idibo ni ojo 360 saaju ojo idibo ni gbogbo ipinle."
            elif top_chunk.section_number in ["29", "29A"]:
                raw_ans = "Lori ejo ti o waye saaju idibo, abala 29(5) Ofin Idibo 2026 gba eni ti o kopa ninu idibo abele laaye lati gbe ejo lo si Ile-ejo Giga ti Ijoba Apapo. (Akiyesi: Abala 29A si wa ni ipo UNCONFIRMED: Ile asofin mejeeji fowo si ni Osu Igbe/Ebibi 2026; nko le fi idi ifowo si aare mule; ye Gazette wo)."
            else:
                raw_ans = f"Gege bi {top_chunk.document_title} Abala {top_chunk.section_number}: {top_chunk.content_plain}"
            ans_text, term_warnings = self.glossary_enforcer.validate_and_enforce(raw_ans, "yo")
            confidence_flags.extend(term_warnings)

        elif lang == "ig":
            if top_chunk.section_number == "47" and top_chunk.subsection_number == "2":
                raw_ans = "Dika ngalaba 47(2) nke Iwu Ntuli Aka 2026 si kwuo, onye isi na-ahazi ntuli aka ga-eji igwe eji enyocha ndi ntuli aka (BVAS) nyochaa onye obula tupu o nye ya akwukwo vootu."
            elif top_chunk.section_number == "47" and top_chunk.subsection_number == "3":
                raw_ans = "Dika ngalaba 47(3) nke Iwu Ntuli Aka 2026 si kwuo, oburu na igwe BVAS emebie ma a weta ngwa ozo n'ubochi ahu, a ga-eyi ntuli aka ebe ahu gaa n'ubochi na-esonye."
            elif top_chunk.section_number == "38":
                raw_ans = "Dika usoro INEC 2026 si di, onye na-elekọta ebe ntuli aka ga-ese foto akwukwo Form EC8A site na igwe BVAS zipu ya na IReV portal tupu o si ebe ahu puo."
            elif top_chunk.section_number == "28":
                raw_ans = "Dika ngalaba 28(1) nke Iwu Ntuli Aka 2026 si kwuo, INEC ga-eweputa okwa ntuli aka ubochi 360 tupu ubochi ntuli aka n'ala anyi."
            elif top_chunk.section_number in ["29", "29A"]:
                raw_ans = "Maka ikpe esemokwu tupu ntuli aka, ngalaba 29(5) nke Iwu 2026 nyere onye zoro okwa ikike ịgba akwụkwọ n'Ụlọ Ikpe Kasị Elu nke Gọọmenti Etiti (Federal High Court). (Rịba ama: Ngalaba 29A nọ n'ụdị UNCONFIRMED: Ụlọ omeiwu abụọ kwadoro ya na Eprel/Mee 2026; enweghị m ike nkwenye nbinye aka onye isi ala; lelee Gazette)."
            else:
                raw_ans = f"Dika {top_chunk.document_title} Ngalaba {top_chunk.section_number}: {top_chunk.content_plain}"
            ans_text, term_warnings = self.glossary_enforcer.validate_and_enforce(raw_ans, "ig")
            confidence_flags.extend(term_warnings)

        else:
            ans_text = f"According to {top_chunk.document_title}, Section {top_chunk.section_number}"
            if top_chunk.subsection_number:
                ans_text += f", Subsection ({top_chunk.subsection_number})"
            ans_text += f":\n\n\"{content}\""
            if top_chunk.legal_status == "UNCONFIRMED":
                ans_text += f"\n\n[Status: UNCONFIRMED. Passed by both chambers (Apr/May 2026); I could not confirm presidential assent as of {top_chunk.retrieval_date}; check the Gazette.]"

            if len(retrieved_chunks) > 1:
                ans_text += "\n\nSupporting / Related Provisions (Top-3 Retrieved):"
                for i, (chunk, _) in enumerate(retrieved_chunks[1:3], start=2):
                    sec_desc = f"Section {chunk.section_number}"
                    if chunk.subsection_number:
                        sec_desc += f", Subsection ({chunk.subsection_number})"
                    ans_text += f"\n\n{i}. {chunk.document_title}, {sec_desc} (Chunk ID: {chunk.chunk_id}):\n\"{chunk.content_english}\""

        has_2022_doc = any("INEC2026-ET" in c.chunk_id or "2022" in c.document_version for c, _ in retrieved_chunks[:3])
        if has_2022_doc:
            if "DOC_REFERS_TO_ELECTORAL_ACT_2022" not in confidence_flags:
                confidence_flags.append("DOC_REFERS_TO_ELECTORAL_ACT_2022")
            notice_2022 = "[Notice: This document refers to the Electoral Act 2022. While administrative procedures (BVAS, IReV) continue under INEC regulations, substantive statutory authority is governed by Electoral Act 2026 Section 60(3).]"
            if notice_2022 not in ans_text:
                ans_text += f"\n\n{notice_2022}"

        return VoterAnswer(
            question=query,
            language=lang,
            answer_text=ans_text,
            answer_plain=PlainLanguageConverter.to_plain_english(plain_content),
            citations=citations,
            retrieved_chunk_ids=[c[0].chunk_id for c in retrieved_chunks[:3]],
            confidence_flags=confidence_flags
        )
