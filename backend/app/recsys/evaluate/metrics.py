import math
import numpy as np


def recall_at_k(recommended_ids: list[int], target_ids: set[int], k: int) -> float:
    """Computes Recall@K for a single user recommendation list."""
    if not target_ids or k <= 0:
        return 0.0
    recs_at_k = set(recommended_ids[:k])
    hits = len(recs_at_k & target_ids)
    return hits / float(len(target_ids))


def precision_at_k(recommended_ids: list[int], target_ids: set[int], k: int) -> float:
    """Computes Precision@K for a single user recommendation list."""
    if k <= 0:
        return 0.0
    recs_at_k = set(recommended_ids[:k])
    hits = len(recs_at_k & target_ids)
    return hits / float(k)


def ndcg_at_k(recommended_ids: list[int], target_ids: set[int], k: int) -> float:
    """Computes Normalized Discounted Cumulative Gain (NDCG@K)."""
    if not target_ids or k <= 0:
        return 0.0

    recs_at_k = recommended_ids[:k]
    dcg = 0.0
    for idx, item in enumerate(recs_at_k):
        if item in target_ids:
            dcg += 1.0 / math.log2(idx + 2)  # idx + 2 because rank 1 -> log2(2) = 1.0

    # Ideal DCG (best possible ordering where hits come first)
    ideal_hits = min(len(target_ids), k)
    idcg = sum(1.0 / math.log2(idx + 2) for idx in range(ideal_hits))

    if idcg == 0.0:
        return 0.0
    return dcg / idcg


def catalogue_coverage(all_recommendations: list[list[int]], total_items: int) -> float:
    """Computes the fraction of total items present across all user recommendation lists."""
    if total_items <= 0:
        return 0.0
    unique_recommended = set()
    for rec_list in all_recommendations:
        unique_recommended.update(rec_list)
    return len(unique_recommended) / float(total_items)


def intra_list_diversity(recommended_indices: list[int], embedding_matrix: np.ndarray) -> float:
    """Computes average pairwise cosine dissimilarity (1 - cosine) within a recommendation list."""
    n = len(recommended_indices)
    if n <= 1:
        return 0.0

    vectors = embedding_matrix[recommended_indices]  # (n, dim)
    # L2 normalize vectors
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    norm_vectors = vectors / norms

    # Pairwise cosine similarities
    cos_sim = norm_vectors @ norm_vectors.T  # (n, n)
    dissim = 1.0 - cos_sim
    np.fill_diagonal(dissim, 0.0)

    # Average distance (1 - cosine similarity) over off-diagonal pairs
    total_pairs = n * (n - 1)
    return float(np.sum(dissim) / total_pairs)
