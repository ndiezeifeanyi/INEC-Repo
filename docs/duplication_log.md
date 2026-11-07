# Duplication Log: Comparative Analysis with Existing Nigerian Civic Tech

This log documents existing civic tech platforms in Nigeria, evaluates potential overlap, and establishes the unique engineering differentiators of this system.

---

## 1. Run-Am
- **Operator**: Rise Networks / MacArthur Foundation / CITAD.
- **Form Factor**: Native Mobile App (Android/iOS, ~35-40 MB download).
- **Core Function**: Fact-checking general social media claims, identifying deepfakes and manipulated images, alerting users to election rumors.
- **Limitations & Differences**:
  1. **Binary Truth Judgments**: Run-Am classifies claims as "True" or "False", which can attract partisan accusations of bias during heated electoral cycles. *Our system strictly avoids judging political claims as true/false; it only checks whether a text/link matches published official INEC records.*
  2. **No Statutory Grounding**: Run-Am searches news feeds and general web data rather than parsing statutory provisions of the Electoral Act 2026.
  3. **High Bandwidth Barrier**: A ~40 MB native app download excludes voters on low-memory devices or with limited mobile data. *Our system uses a <30 KB lightweight PWA web app.*

---

## 2. GovGuide Nigeria
- **Operator**: FMCIDE, NCAIR, NITDA, Publica AI, Meta.
- **Form Factor**: Web portal and WhatsApp chatbot.
- **Core Function**: Administrative civic navigator for public services (National ID - NIN, passport renewal, vehicle registration, business registration with CAC).
- **Limitations & Differences**:
  1. **Broad Governance Focus vs. Electoral Law**: GovGuide assists with everyday government administrative transactions. It is not designed for electoral rules, election dispute boundaries, or ballot transmission verification.
  2. **No Link/Message Cryptographic Verifier**: GovGuide does not provide privacy-preserving URL inspection or Safe Browsing hash checks for election phishing.

---

## 3. Naija Elections AI
- **Operator**: Kimpact Development Initiative (KDI).
- **Form Factor**: Web information portal.
- **Core Function**: AI-assisted conversational voter education on Nigerian electoral procedures.
- **Limitations & Differences**:
  1. **Monolingual-First with Unverified Terminology**: Primarily trained on English texts with post-hoc translation. Lacks an enforced bilingual civic glossary with certified terminology for Hausa, Yoruba, and Igbo.
  2. **No Tri-State Verification Guardrails**: Relies on conversational LLM responses without deterministic statutory section citations (e.g. citing document title, section, subsection, gazette version, retrieval date).
  3. **No Zero-Knowledge Safe Browsing**: Does not include a local SHA-256 hash-prefix engine to detect fraudulent voter registration sites (like `linksnapro.com/cvrreg`) without sending user URLs to third parties.

---

## 4. Distinct Value Proposition of this Prototype

| Feature | Run-Am | GovGuide | Naija Elections AI | Our System |
| :--- | :--- | :--- | :--- | :--- |
| **Grounding Corpus** | Web news / scrapers | Civil service docs | General voter FAQ | **Electoral Act 2026 & INEC Guidelines 2026 (Gazetted)** |
| **Claim Check Output** | True / False / Misleading | N/A | Conversational | **"Matches official source" / "Does not match" / "Can't tell"** |
| **Legal Citations** | None | Agency procedures | Partial | **Mandatory: Doc, Section, Subsection, Version, Date** |
| **Multilingual Strategy** | General translation | Llama 3 fine-tune | Standard API | **Dual retrieval benchmark (AfriE5/BGE-M3 vs NLLB-Hybrid) + Enforced Glossary** |
| **Link Phishing Defense** | News search | None | None | **Privacy-Preserving Safe Browsing Update API v4 + Typosquatting / CNAME filter** |
| **Payload Budget** | ~40 MB app | Web app | Standard web app | **< 30 KB low-bandwidth PWA (works on 2G/EDGE)** |
| **Political Refusal** | Evaluates claims | Out of scope | Partial filters | **Deterministic hard refusal on candidates/parties/predictions** |
| **License** | Proprietary | Proprietary | Proprietary | **Open Source (MIT)** |

