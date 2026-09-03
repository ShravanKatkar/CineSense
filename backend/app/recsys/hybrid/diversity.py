import numpy as np


def maximal_marginal_relevance(
    candidate_ids: list[int],
    rel_scores: dict[int, float],
    movie_id_to_idx: dict[int, int],
    embedding_matrix: np.ndarray,
    k: int = 12,
    lam: float = 0.7,
) -> list[int]:
    """Greedy Maximal Marginal Relevance (MMR) diversification.

    balances relevance (lam) and novelty (1 - lam).
    """
    if len(candidate_ids) <= k:
        return candidate_ids

    # Extract valid candidates present in embedding matrix
    valid_cands = [m for m in candidate_ids if m in movie_id_to_idx]
    if not valid_cands:
        return candidate_ids[:k]

    chosen: list[int] = []
    pool = list(valid_cands)

    # Normalize embeddings for cosine comparison
    indices = [movie_id_to_idx[m] for m in pool]
    vecs = embedding_matrix[indices]
    norms = np.linalg.norm(vecs, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    norm_vecs = vecs / norms

    cand_to_norm_vec = {m: norm_vecs[i] for i, m in enumerate(pool)}

    while len(chosen) < k and pool:
        best_item = None
        best_val = -1e9

        for m in pool:
            m_vec = cand_to_norm_vec[m]
            if not chosen:
                penalty = 0.0
            else:
                chosen_vecs = np.array([cand_to_norm_vec[c] for c in chosen])
                sims = chosen_vecs @ m_vec
                penalty = float(np.max(sims))

            val = lam * rel_scores.get(m, 0.0) - (1.0 - lam) * penalty
            if val > best_val:
                best_val = val
                best_item = m

        if best_item is not None:
            chosen.append(best_item)
            pool.remove(best_item)
        else:
            break

    return chosen
