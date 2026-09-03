import numpy as np
import pytest
from app.recsys.evaluate.metrics import (
    catalogue_coverage,
    intra_list_diversity,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
)


def test_recall_at_k():
    recs = [10, 20, 30, 40, 50]
    targets = {20, 40, 60}

    # At K=5, 2 hits (20, 40) out of 3 targets -> 2/3 = 0.6667
    assert pytest.approx(recall_at_k(recs, targets, k=5), 0.001) == 2.0 / 3.0

    # At K=2, 1 hit (20) out of 3 targets -> 1/3 = 0.3333
    assert pytest.approx(recall_at_k(recs, targets, k=2), 0.001) == 1.0 / 3.0

    # Zero hits
    assert recall_at_k(recs, {99, 100}, k=5) == 0.0


def test_precision_at_k():
    recs = [10, 20, 30, 40, 50]
    targets = {20, 40, 60}

    # At K=5, 2 hits out of K=5 -> 2/5 = 0.4
    assert precision_at_k(recs, targets, k=5) == 0.4

    # At K=2, 1 hit out of K=2 -> 1/2 = 0.5
    assert precision_at_k(recs, targets, k=2) == 0.5


def test_ndcg_at_k():
    recs = [10, 20, 30]  # hit at rank 2 (index 1)
    targets = {20}

    # DCG = 1.0 / log2(1 + 2) = 1.0 / log2(3) = 0.6309
    # IDCG = 1.0 / log2(0 + 2) = 1.0 / log2(2) = 1.0
    # NDCG = 0.6309 / 1.0 = 0.6309
    expected_ndcg = 1.0 / np.log2(3)
    assert pytest.approx(ndcg_at_k(recs, targets, k=3), 0.001) == expected_ndcg

    # Perfect ranking: hit at rank 1 -> NDCG = 1.0
    assert ndcg_at_k([20, 10, 30], targets, k=3) == 1.0


def test_catalogue_coverage():
    all_recs = [[1, 2, 3], [2, 3, 4], [5]]
    # Unique recommended = {1, 2, 3, 4, 5} (5 items out of 10 total)
    assert catalogue_coverage(all_recs, total_items=10) == 0.5


def test_intra_list_diversity():
    # 2 orthogonal vectors: (1, 0) and (0, 1)
    emb_matrix = np.array([
        [1.0, 0.0],
        [0.0, 1.0],
    ])
    # Pairwise cosine dissimilarity between orthogonal vectors = 1.0
    diversity = intra_list_diversity([0, 1], emb_matrix)
    assert pytest.approx(diversity, 0.001) == 1.0
