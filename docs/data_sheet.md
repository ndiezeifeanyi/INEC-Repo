# Data Sheet for Datasets

## 1. Motivation
- **Purpose**: Provide clean, verified, statutory legal chunks and certified multilingual civic glossaries for voter FAQ retrieval and claim verification for the 2026/2027 Nigerian electoral cycle.
- **Creator**: Civic Tech Team (#AI4Elections Hackathon).

## 2. Composition
### Statutory Corpus (`data/processed/`)
- **Electoral Act 2026**:
  - Source: National Assembly Official Gazette (`nass.gov.ng/documents/download/11248`), signed 18 Feb 2026.
  - Granularity: Section-by-section and subsection-by-subsection.
  - Checksum: SHA-256 verified upon ingestion.
- **INEC Regulations and Guidelines for the Conduct of Elections (2026)**:
  - Source: Official INEC Portal (`inecnigeria.org/elections/guidelines`).
  - Sections: Registration, BVAS accreditation, electronic transmission, collation procedures.
- **Official Public Notices & Press Bulletins**:
  - Ingested directly from official INEC public releases (2024–2026).

### Certified Bilingual Civic Glossaries (`data/glossaries/`)
- Languages: Hausa (`hausa.json`), Yoruba (`yoruba.json`), Igbo (`igbo.json`).
- Coverage: Essential electoral concepts (e.g. voter registration, polling unit, presiding officer, collation center, accreditation, BVAS, ballot box, rejected ballot).
- Attribution & Review: Seeded from academic corpora (Masakhane / BBC News electoral guidelines) and tagged with `reviewed_by` status metadata.

## 3. Collection Process
- Documents were fetched directly from authoritative government portals via automated script with SHA-256 checksum hashing.
- No copyrighted third-party news articles or proprietary private datasets were scraped.
- No live voter personal data or confidential voter rolls were accessed.

## 4. Maintenance
- Data files are immutable with revision stamps.
- Any amendment (e.g. formal gazetting of Section 29A) triggers an automatic hash update and re-indexing.
