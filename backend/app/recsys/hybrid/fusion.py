from collections import defaultdict


def reciprocal_rank_fusion(
    ranked_lists: dict[str, list[int]],
    weights: dict[str, float] | None = None,
    k_constant: int = 60,
) -> tuple[list[tuple[int, float]], dict[int, dict[str, int]]]:
    """Combines multiple ranked lists of movie IDs using Reciprocal Rank Fusion (RRF).

    Formula: score(m) = sum_{s in S} (w_s / (k_constant + rank_s(m)))
    Returns:
      - Sorted list of (movie_id, rrf_score) tuples
      - Dictionary mapping movie_id -> per-source rank dict, e.g. {"als": 3, "embedding": 11}
    """
    weights = weights or {}
    scores: dict[int, float] = defaultdict(float)
    sources: dict[int, dict[str, int]] = defaultdict(dict)

    for source_name, item_ids in ranked_lists.items():
        w = weights.get(source_name, 1.0)
        for rank, mid in enumerate(item_ids, start=1):
            scores[mid] += w / float(k_constant + rank)
            sources[mid][source_name] = rank

    sorted_scores = sorted(scores.items(), key=lambda kv: -kv[1])
    return sorted_scores, dict(sources)
