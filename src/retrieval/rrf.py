from typing import List, Dict, Tuple
from src.models.chunk import LegalChunk

def reciprocal_rank_fusion(
    ranked_lists: List[List[Tuple[LegalChunk, float]]],
    k: int = 60
) -> List[Tuple[LegalChunk, float]]:
    """
    Combines multiple ranked lists using Reciprocal Rank Fusion (RRF).
    RRF_score(d) = sum(1 / (k + rank_m(d)))
    """
    scores: Dict[str, float] = {}
    chunk_map: Dict[str, LegalChunk] = {}

    for r_list in ranked_lists:
        for rank, (chunk, _) in enumerate(r_list, start=1):
            cid = chunk.chunk_id
            chunk_map[cid] = chunk
            scores[cid] = scores.get(cid, 0.0) + (1.0 / (k + rank))

    # Sort descending by fused score
    sorted_items = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [(chunk_map[cid], score) for cid, score in sorted_items]

