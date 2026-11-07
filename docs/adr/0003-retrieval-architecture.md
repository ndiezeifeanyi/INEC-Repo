# ADR 0003: Multilingual Retrieval Architecture Selection

- **Status**: Accepted
- **Date**: 2026-11-07
- **Context**: Low-resource multilingual retrieval in Hausa, Yoruba, and Igbo against English statutory legal texts.

## Candidates

### Path A: Direct Cross-Lingual Dense Retrieval
- **Models**: `castorini/afrie5-large-instruct` and `BAAI/bge-m3`.
- **Workflow**: English legal chunks are indexed into vector space. User queries in Hausa, Yoruba, or Igbo are embedded directly and retrieved using cosine similarity.
- **Advantage**: Single-stage pipeline, no intermediate machine translation latency or translation error cascade.
- **Risk**: African language embedding quality can suffer on complex legal terminology without extensive domain fine-tuning.

### Path B: Query Translation + Hybrid English Retrieval
- **Models**: `facebook/nllb-200-distilled-600M` or frontier translation API -> English Dense (`BAAI/bge-m3`) + Sparse (`rank-bm25`).
- **Workflow**: Native query is translated to English -> queries run across both Dense and BM25 -> fused with Reciprocal Rank Fusion (RRF).
- **Advantage**: BM25 excels at exact statutory terms (e.g., "Section 47", "BVAS", "Form EC8A").
- **Risk**: Machine translation errors can distort voter intent before retrieval begins.

## Decision Protocol

We implement both pipelines behind a unified `BaseRetriever` interface. The winning path will be selected based on measured results on our 40-item multilingual test benchmark (`tests/eval_retrieval.py`), targeting:
- Recall@5 >= 0.85
- MRR >= 0.75
Metrics are logged in the Evaluation Report before freezing the default deployment pipeline.
