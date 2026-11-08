import json

with open("data/cache/heldout_audit6_results.json", "r", encoding="utf-8") as f:
    data = json.load(f)

for key, val in data.items():
    print(f"### {val['set_label']}")
    print(f"- Total Samples: {val['n_samples']}")
    print(f"- Hits@3: {val['hits_at_3']}")
    print(f"- Recall@3: {val['recall@3']}")
    print(f"- Wilson 95% CI: {val['recall@3_wilson_95ci']}")
    print(f"- MRR: {val['mrr']}\n")
    print("| ID | Lang | Query | Translated to EN | Target | Top-3 Retrieved | Hit@3 | Rank |")
    print("|---|---|---|---|---|---|:---:|:---:|")
    for d in val["details"]:
        ret_str = ", ".join(d["top3_retrieved"])
        rank_str = str(d["rank"]) if d["rank"] is not None else "None (>5)"
        hit_str = "HIT" if d["hit@3"] else "MISS"
        print(f"| {d['id']} | {d['lang']} | {d['query']} | {d['translated_to_en']} | {d['target']} | {ret_str} | {hit_str} | {rank_str} |")
    print("\n" + "="*80 + "\n")
