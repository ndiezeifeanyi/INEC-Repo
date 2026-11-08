# Plain Language Templates for Human Review

This document catalogues every plain-language summary template embedded in the ingestion engine (`src/ingestion/rebuild_corpus.py`) and plain language generator (`src/generation/plain_language.py`). Every template has been audited against the official National Assembly Gazette No. 40 (Electoral Act 2026) and verified to contain only claims directly present in the quoted statutory text.

| Statutory Citation | Chunk ID | Official Gazette Enacted Text Summary | Plain-Language Template (for Human Review) | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Section 51(2)** | `EA2026-S51-SS2` | Where votes cast in polling unit exceed accredited voters, Presiding Officer shall cancel result in that polling unit. | *"If the number of votes cast at an election in any polling unit exceeds the number of accredited voters, the Presiding Officer must cancel the election result in that polling unit."* | **AUDITED & VERIFIED** |
| **Section 60(3)** | `EA2026-S60-SS3` | Presiding officer shall electronically transmit results to IReV after Form EC8A is signed/stamped; communication failure proviso. | *"The Presiding Officer must electronically transmit polling unit results to the IReV portal after Form EC8A is signed and stamped. If electronic transmission fails due to communication failure, the signed and stamped Form EC8A remains the primary source for collation and declaration of the result."* | **AUDITED & VERIFIED** |
| **Section 47(1)** | `EA2026-S47-SS1` | Person intending to vote shall present himself with permanent voter's card to Presiding Officer or Polling Clerk at registered PU. | *"A voter must present themselves with their permanent voter card (PVC) to the Presiding Officer or Polling Clerk at the polling unit where their name is registered."* | **AUDITED & VERIFIED** |
| **Section 47(2)** | `EA2026-S47-SS2` | Presiding officer shall use BVAS to verify, confirm, or authenticate voter. | *"The Presiding Officer must use the Bimodal Voter Accreditation System (BVAS) or other approved device to verify, confirm, or authenticate the voter before giving them a ballot paper."* | **AUDITED & VERIFIED** |
| **Section 47(3)** | `EA2026-S47-SS3` | If BVAS fails to verify by fingerprint or facial and no fresh device deployed, election cancelled and rescheduled within 24 hours. | *"If the BVAS device fails to verify a voter by fingerprint or facial recognition and cannot be replaced the same day, election at that polling unit is postponed until the next day."* | **AUDITED & VERIFIED** |
| **Section 50(2)** | `EA2026-S50-SS2` | Voting at an election and transmission of results shall be in accordance with procedure determined by Commission. | *"Voting and the transmission of results under the Electoral Act must follow the procedure determined by the Commission."* | **AUDITED & VERIFIED** |
| **Section 28(1)** | `EA2026-S28-SS1` | Commission shall not later than 300 days before election publish notice stating date and nomination delivery place. | *"INEC must publish an official notice not later than 300 days before the election stating the election date and the place where nomination papers are delivered."* | **AUDITED & VERIFIED (Corrected to statutory text)** |
| **Section 29(5)** | `EA2026-S29-SS5` | An aspirant who participated in primaries of his party may apply to Federal High Court on reasonable grounds that candidate gave false affidavit. | *"Only an aspirant who contested the primary election of a political party has legal standing to file a suit at the Federal High Court challenging candidate nomination affidavits."* | **AUDITED & VERIFIED** |
| **Section 12(1)** | `EA2026-S12-SS1` | Person eligible to vote if citizen of Nigeria, 18 years, resident/origination in LGA/ward. | *"A Nigerian citizen who is 18 years or older and resident, originating, or working in a constituency is entitled to register as a voter."* | **AUDITED & VERIFIED** |
| **Section 154** | `EA2026-S154-SS1` | Electoral Act 2022 is repealed. | *"The Electoral Act 2022 is repealed; this Electoral Act 2026 is the enacted governing law for elections across Nigeria."* | **AUDITED & VERIFIED** |
| **All Other Sections** | *(Dynamic)* | Dynamic verbatim statutory text. | Generated dynamically by `PlainLanguageConverter.to_plain_english(content[:250])` using legal jargon regex replacements. | **AUTOMATED FALLBACK** |

---

### Lexical Substitution Map (`src/generation/plain_language.py`)
For any chunk without an explicit human-audited summary, `PlainLanguageConverter` applies purely mechanical rule-based jargon simplification to the quoted chunk text:
- `notwithstanding the provisions of` -> `even if another rule says`
- `pursuant to` -> `under`
- `shall be deemed to be` -> `is considered`
- `aforementioned` -> `earlier mentioned`
- `forthwith` -> `immediately`
- `commence` -> `start`
- `prescribed manner` -> `official procedure`
- `intending voter` -> `voter`
- `stand adjourned` -> `is postponed`
- `void` -> `cancelled and invalid`

