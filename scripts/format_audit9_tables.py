import json
from pathlib import Path

base_dir = Path(__file__).resolve().parent.parent
results_file = base_dir / "data" / "cache" / "heldout_audit9_results.json"
api_dir = base_dir / "data" / "cache" / "api_outputs"

with open(results_file, "r", encoding="utf-8") as f:
    data = json.load(f)

print("# AUDIT 9 BENCHMARK EVALUATION RESULTS (GENERATED FROM DATA/CACHE/HELDOUT_AUDIT9_RESULTS.JSON)\n")

print("## Summary Table across All Evaluation Sets\n")
print("| Benchmark Set | Retrieval Mode | n | Top-1 Accuracy | Top-1 Wilson 95% CI | Hit@3 (Recall@3) | Hit@3 Wilson 95% CI | MRR |")
print("|---|---|:---:|:---:|:---:|:---:|:---:|:---:|")

for key, val in data.items():
    lbl = val["set_label"]
    n = val["n_samples"]
    r1 = val["recall@1"]
    ci1 = val["recall@1_wilson_95ci"]
    r3 = val["recall@3"]
    ci3 = val["recall@3_wilson_95ci"]
    mrr = val["mrr"]
    print(f"| **{lbl}** | {lbl.split('(')[-1].replace(')', '') if '(' in lbl else 'English'} | {n} | **{r1}** | {ci1} | **{r3}** | {ci3} | {mrr} |")

print("\n" + "="*100 + "\n")

for key, val in data.items():
    print(f"### Detailed Breakdown: {val['set_label']}")
    print(f"- Total Samples (n): {val['n_samples']}")
    print(f"- Top-1 Hits: {val['hits_at_1']} -> Top-1 Accuracy: {val['recall@1']} (Wilson 95% CI: {val['recall@1_wilson_95ci']})")
    print(f"- Hit@3 Hits: {val['hits_at_3']} -> Hit@3 (Recall@3): {val['recall@3']} (Wilson 95% CI: {val['recall@3_wilson_95ci']})")
    print(f"- Mean Reciprocal Rank (MRR): {val['mrr']}\n")

    print("| ID | Lang | Query | Target | Top-3 Retrieved | BM25 Top-1 | Dense Top-1 | Disagree? | Hit@1 | Hit@3 | Rank |")
    print("|---|:---:|---|:---:|---|:---:|:---:|:---:|:---:|:---:|:---:|")
    for d in val["details"]:
        ret_str = ", ".join(d["top3_retrieved"])
        b1 = d.get("bm25_top1", "N/A")
        d1 = d.get("dense_top1", "N/A")
        dis = "YES" if d.get("bm25_dense_disagree") else "NO"
        h1 = "HIT" if d.get("hit@1") else "MISS"
        h3 = "HIT" if d.get("hit@3") else "MISS"
        rnk = str(d["rank"]) if d["rank"] is not None else ">5"
        print(f"| {d['id']} | {d['lang']} | {d['query']} | {d['target']} | {ret_str} | {b1} | {d1} | {dis} | {h1} | {h3} | {rnk} |")
    print("\n" + "="*100 + "\n")

print("## API OUTPUT VERIFICATION (LOADED DIRECTLY FROM DATA/CACHE/API_OUTPUTS/*.JSON)\n")
api_files = [
    "natural_01_over_voting.json",
    "natural_02_election_notice.json",
    "natural_03_primary_challenge.json",
    "natural_04_transmission.json",
    "natural_05_voter_card.json",
    "spot_check_real_time_upload.json",
    "section_29a_query.json",
    "heldout_002_ha.json",
    "heldout_003_yo.json",
    "heldout_004_ig.json"
]

for fname in api_files:
    fpath = api_dir / fname
    if fpath.exists():
        with open(fpath, "r", encoding="utf-8") as af:
            apidata = json.load(af)
        print(f"### API Output: `{fname}`")
        print(f"- **Question**: {apidata.get('question')}")
        print(f"- **Language**: {apidata.get('language')}")
        print(f"- **Confidence Flags**: {apidata.get('confidence_flags')}")
        print(f"- **Plain Summary (`answer_plain`)**: {apidata.get('answer_plain')}")
        print(f"- **Retrieved Chunk IDs**: {apidata.get('retrieved_chunk_ids')}")
        print("- **Full Answer Text (`answer_text`)**:")
        print("```")
        print(apidata.get("answer_text"))
        print("```\n")
