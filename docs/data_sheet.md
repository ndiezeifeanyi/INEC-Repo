# Data Sheet for Datasets

## 1. Motivation
- **Purpose**: Provide clean, verified, statutory legal chunks and certified multilingual civic glossaries for voter FAQ retrieval and claim verification for the 2026/2027 Nigerian electoral cycle.
- **Creator**: Civic Tech Team (#AI4Elections Hackathon).

## 2. Composition
### Statutory Corpus (`data/processed/`)
- **Electoral Act 2026** (`electoral_act_2026.jsonl`):
  - Source: National Assembly Official Gazette (`https://nass.gov.ng/documents/download/11248`), signed 18 Feb 2026.
  - Granularity: Section-by-section and subsection-by-subsection. Total 510 statutory chunks.
  - Coverage:
    - Main statutory body: Sections 1–156 (Gazette Pages 9–74) -> 455 chunks (`EA2026-S1-SS1` to `EA2026-S156-SS1`).
    - First Schedule (Rules of Procedure for Election Petitions): Paragraphs 1–55 and Standard Petitions Forms (Gazette Pages 75–113) -> 55 chunks (`EA2026-SCH1-P1` to `EA2026-SCH1-P55`).
  - **Excluded Gazette Pages**:
    - **Pages 3–8**: Table of Contents / Arrangement of Sections. Excluded because it contains only chapter titles and statutory headings without operative legal rules or enforceable statutory text. Ingesting TOC causes duplicate heading retrievals that degrade citation precision.
    - **Pages 114–121**: Statutory Schedules and Legislative Attestations.
      - *Page 114 (Second Schedule)*: Prescribed template oath / affirmation of neutrality for electoral officers under Section 26(1).
      - *Pages 115–119 (Third Schedule)*: Blank administrative voter registration notice forms (Form EC.1, EC.2, EC.3, EC.3A).
      - *Page 120*: National Assembly Clerk attestation certificate (Acts Authentication Act, Cap. A2) and general Explanatory Memorandum.
      - *Page 121*: National Assembly Schedule to the Electoral Bill 2026, recording Senate passage date, House of Representatives passage date, and Presidential Assent by President Bola Ahmed Tinubu on 18th February 2026.
      - *Rationale for Exclusion from QA Index*: Pages 114–121 consist of blank administrative form layouts and legislative authentication signatures rather than civic election rules. Ingesting blank forms would introduce non-actionable boilerplate into civic retrieval results. All substantive statutory rules governing voter registration, accreditation, voting, and election petitions are fully captured in Sections 1–156 and the First Schedule.
  - Checksum: SHA-256 verified upon ingestion (`4c8e7ef9e29f345ebc534e70ffeb3a958cfb042c162f43bb2327715f3ecda84b`).
- **INEC Electronic Transmission & Collation Procedure** (`inec_transmission_procedure.jsonl`):
  - Source: Official INEC procedure document (4 pages, `data/raw/inec_electronic_transmission_procedure.pdf`).
  - Granularity: Page-by-page chunks (`INEC2026-ET-PAGE1` to `PAGE4`).
  - SHA-256: `64a7da0b91e98bb4f2f0980f74a0da7d9ecceee9e6c92d5c317f223fe9b8ea01`.
- **Official Public Notices & Bulletins** (`inec_bulletins.jsonl`):
  - Strictly audited against live INEC endpoints. Any URL or bulletin that cannot be verified on the live website has been purged. Check mode defaults to "Can't tell" for unverified claims.

### Civic Terminology & Refusals (`data/glossaries/`)
- Languages: Hausa (`hausa.json`), Yoruba (`yoruba.json`), Igbo (`igbo.json`).
- Status: **UNREVIEWED**. All term pairs and non-English refusal/amendment strings are developer-draft templates and must be audited and certified by qualified native speakers before production deployment.
- Refusals & Amendment Notices: Detailed in `data/glossaries/refusals_unreviewed.json`.

## 3. Collection Process
- Documents were fetched directly from authoritative government portals via automated script with SHA-256 checksum hashing.
- No copyrighted third-party news articles or proprietary private datasets were scraped.
- No live voter personal data or confidential voter rolls were accessed.

## 4. Maintenance
- Data files are immutable with revision stamps.
- Any amendment (e.g. formal gazetting of Section 29A) triggers an automatic hash update and re-indexing.

