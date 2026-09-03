from pathlib import Path
import sys
import time
import pandas as pd
import structlog

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.recsys.baseline.popularity import PopularityRecommender
from app.recsys.collaborative.als import ALSRecommender
from app.recsys.collaborative.item_cf import ItemCFRecommender
from app.recsys.content.tfidf import TfidfRecommender
from app.recsys.embeddings.search import EmbeddingRecommender
from app.recsys.evaluate.metrics import (
    catalogue_coverage,
    intra_list_diversity,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
)
from app.recsys.evaluate.split import get_temporal_eval_split
from app.recsys.hybrid.recommender import HybridRecommender

log = structlog.get_logger()
DOCS_DIR = Path("docs")
EVAL_MD = DOCS_DIR / "evaluation-results.md"


def run_benchmark() -> None:
    print("Loading temporal leave-last-k-out evaluation dataset...")
    eval_data = get_temporal_eval_split(test_k=5, min_ratings=10)
    print(f"Eval split: {len(eval_data.test_user_items)} test users, {eval_data.n_movies} movies total.")

    print("\nInitializing model instances...")
    pop_model = PopularityRecommender()
    tfidf_model = TfidfRecommender()
    emb_model = EmbeddingRecommender()
    item_cf_model = ItemCFRecommender()
    als_model = ALSRecommender()
    hybrid_model = HybridRecommender()

    models = [
        ("Popularity (weighted)", pop_model),
        ("TF-IDF content", tfidf_model),
        ("Embedding kNN", emb_model),
        ("Item-item CF", item_cf_model),
        ("ALS (64 factors)", als_model),
        ("Hybrid RRF", hybrid_model),
    ]

    results_rows: list[dict] = []

    # Get user seed history from train split
    user_train_history: dict[int, list[int]] = {}
    for uid, group in eval_data.train_ratings.groupby("userId"):
        # Sort by rating DESC, then timestamp DESC
        sorted_mids = group.sort_values(by=["rating", "timestamp"], ascending=[False, False])["movieId"].astype(int).tolist()
        user_train_history[uid] = sorted_mids

    for model_name, model in models:
        print(f"\nEvaluating {model_name}...")
        recalls, precisions, ndcgs = [], [], []
        all_recs: list[list[int]] = []
        latencies_ms: list[float] = []

        for uid, target_mids in eval_data.test_user_items.items():
            seed_ids = user_train_history.get(uid, [])[:5]

            start_t = time.perf_counter()
            if model_name == "Popularity (weighted)":
                scored_recs = model.recommend(seed_ids=seed_ids, k=10)
            elif model_name in ("ALS (64 factors)", "Hybrid RRF"):
                scored_recs = model.recommend(user_id=uid, seed_ids=seed_ids, k=10)
            else:
                scored_recs = model.recommend(seed_ids=seed_ids, k=10)

            elapsed_ms = (time.perf_counter() - start_t) * 1000.0
            latencies_ms.append(elapsed_ms)

            rec_ids = [r.movie_id for r in scored_recs]
            all_recs.append(rec_ids)

            recalls.append(recall_at_k(rec_ids, target_mids, k=10))
            precisions.append(precision_at_k(rec_ids, target_mids, k=10))
            ndcgs.append(ndcg_at_k(rec_ids, target_mids, k=10))

        mean_recall = float(pd.Series(recalls).mean())
        mean_prec = float(pd.Series(precisions).mean())
        mean_ndcg = float(pd.Series(ndcgs).mean())
        coverage = catalogue_coverage(all_recs, eval_data.n_movies)

        # Compute average intra-list diversity using embedding matrix
        div_scores = [intra_list_diversity([emb_model.movie_id_to_idx[m] for m in r if m in emb_model.movie_id_to_idx], emb_model.embeddings) for r in all_recs]
        mean_div = float(pd.Series(div_scores).mean())
        p95_lat = float(pd.Series(latencies_ms).quantile(0.95))

        results_rows.append({
            "Recommender": model_name,
            "Recall@10": f"{mean_recall:.4f}",
            "Precision@10": f"{mean_prec:.4f}",
            "NDCG@10": f"{mean_ndcg:.4f}",
            "Coverage": f"{coverage * 100:.2f}%",
            "Diversity": f"{mean_div:.4f}",
            "Latency p95": f"{p95_lat:.2f} ms",
        })

    df_res = pd.DataFrame(results_rows)
    print("\n--- Evaluation Benchmark Results ---")
    print(df_res.to_string(index=False))

    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    md_content = f"# CineSense Offline Recommender Evaluation Results\n\n"
    md_content += f"Evaluated against temporal leave-last-5-out split across {len(eval_data.test_user_items)} test users over {eval_data.n_movies} movies.\n\n"
    md_content += df_res.to_markdown(index=False)
    md_content += "\n\n"
    EVAL_MD.write_text(md_content, encoding="utf-8")
    print(f"\nSaved evaluation comparison table to {EVAL_MD}")


if __name__ == "__main__":
    run_benchmark()
