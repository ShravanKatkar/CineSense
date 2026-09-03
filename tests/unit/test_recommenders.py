import pytest
from app.recsys.base import MovieFilters, ScoredMovie
from app.recsys.baseline.popularity import PopularityRecommender
from app.recsys.collaborative.als import ALSRecommender
from app.recsys.collaborative.item_cf import ItemCFRecommender
from app.recsys.content.tfidf import TfidfRecommender
from app.recsys.embeddings.search import EmbeddingRecommender
from app.recsys.hybrid.recommender import HybridRecommender


def test_popularity_recommender():
    rec = PopularityRecommender()
    results = rec.recommend(k=10)
    assert len(results) == 10
    assert all(isinstance(r, ScoredMovie) for r in results)
    assert results[0].score >= results[-1].score


def test_tfidf_recommender():
    rec = TfidfRecommender()
    # Seed with Toy Story (movielens_id = 1)
    results = rec.recommend(seed_ids=[1], k=10)
    assert len(results) > 0
    assert all(isinstance(r, ScoredMovie) for r in results)
    assert not any(r.movie_id == 1 for r in results)


def test_embedding_recommender():
    rec = EmbeddingRecommender()
    results = rec.recommend(seed_ids=[1], k=10)
    assert len(results) > 0
    assert all(isinstance(r, ScoredMovie) for r in results)


def test_item_cf_recommender():
    rec = ItemCFRecommender()
    results = rec.recommend(seed_ids=[1], k=10)
    assert len(results) > 0
    assert all(isinstance(r, ScoredMovie) for r in results)


def test_als_recommender():
    rec = ALSRecommender()
    results = rec.recommend(user_id=1, k=10)
    assert len(results) == 10
    assert all(isinstance(r, ScoredMovie) for r in results)


def test_hybrid_recommender():
    rec = HybridRecommender()
    filters = MovieFilters(genres_include=["Action"], year_min=2000)
    results = rec.recommend(user_id=1, seed_ids=[1], filters=filters, k=10)
    assert len(results) <= 10
    assert all(isinstance(r, ScoredMovie) for r in results)
