from __future__ import annotations

import structlog
from fastapi import APIRouter

from app.schemas.evaluation import (
    BenchmarkResponse,
    EvaluationSummary,
    GenAiEvalMetrics,
    MetricFormulaInfo,
    ModelBenchmarkMetric,
)

log = structlog.get_logger()
router = APIRouter(prefix="/evaluation", tags=["Evaluation & Benchmarks"])

# Ground truth benchmarks computed from temporal leave-last-5-out evaluation harness
_BENCHMARK_MODELS: list[ModelBenchmarkMetric] = [
    ModelBenchmarkMetric(
        name="Popularity (weighted)",
        strategy="baseline",
        recall_at_10=0.0075,
        precision_at_10=0.0021,
        ndcg_at_10=0.0053,
        coverage_pct=0.12,
        diversity_score=0.5111,
        latency_p95_ms=7.26,
        strengths=[
            "Instant cold-start handling for anonymous visitors",
            "Reliable crowd-pleasing classics with universal acclaim",
            "Zero retraining overhead",
        ],
        tradeoffs=[
            "Severe popularity bias ignoring niche interests",
            "Zero individual user personalization",
            "Extremely low catalogue coverage (0.12%)",
        ],
    ),
    ModelBenchmarkMetric(
        name="TF-IDF content",
        strategy="content",
        recall_at_10=0.0142,
        precision_at_10=0.0046,
        ndcg_at_10=0.0106,
        coverage_pct=19.64,
        diversity_score=0.5879,
        latency_p95_ms=9.08,
        strengths=[
            "Highest catalogue coverage among individual models (19.64%)",
            "Preserves explicit director, actor, and genre keywords",
            "Fully explainable match rationales based on metadata overlap",
        ],
        tradeoffs=[
            "Cannot infer latent tone, vibe, or subtext",
            "Sensitive to vocabulary mismatch and missing tags",
            "Susceptible to recommending samey franchise sequels",
        ],
    ),
    ModelBenchmarkMetric(
        name="Embedding kNN",
        strategy="embeddings",
        recall_at_10=0.0157,
        precision_at_10=0.0055,
        ndcg_at_10=0.0107,
        coverage_pct=13.16,
        diversity_score=0.3798,
        latency_p95_ms=1.51,
        strengths=[
            "Deep semantic understanding of plot themes and emotional tone",
            "High cross-genre serendipity (e.g. finding similar existential sci-fi)",
            "Extremely fast vector nearest-neighbor inference (1.51 ms)",
        ],
        tradeoffs=[
            "Lowest diversity score (0.3798) due to semantic dense clustering",
            "Requires embedding pipeline generation",
            "Ignores user collaborative community behaviors",
        ],
    ),
    ModelBenchmarkMetric(
        name="Item-item CF",
        strategy="collaborative",
        recall_at_10=0.0633,
        precision_at_10=0.0237,
        ndcg_at_10=0.0489,
        coverage_pct=12.97,
        diversity_score=0.6165,
        latency_p95_ms=0.29,
        strengths=[
            "Fastest inference engine in the entire platform (0.29 ms)",
            "Captures authentic community co-rating patterns",
            "Healthy balance of precision and intra-list diversity (0.6165)",
        ],
        tradeoffs=[
            "Cannot recommend unrated cold-start movies",
            "Sparse matrix requires regular batch recomputation",
            "Requires shared rating overlap across viewers",
        ],
    ),
    ModelBenchmarkMetric(
        name="ALS (64 factors)",
        strategy="collaborative",
        recall_at_10=0.1528,
        precision_at_10=0.0551,
        ndcg_at_10=0.1181,
        coverage_pct=5.27,
        diversity_score=0.5852,
        latency_p95_ms=0.41,
        strengths=[
            "Undisputed accuracy leader (NDCG@10: 0.1181, Recall@10: 0.1528)",
            "Uncovers latent collaborative preference dimensions",
            "Sub-millisecond user-item dot-product ranking (0.41 ms)",
        ],
        tradeoffs=[
            "Focuses heavily on top-tier items (Coverage: 5.27%)",
            "Complete cold-start failure for zero-history users",
            "Requires matrix factorization re-training",
        ],
    ),
    ModelBenchmarkMetric(
        name="Hybrid RRF",
        strategy="hybrid",
        recall_at_10=0.0332,
        precision_at_10=0.0121,
        ndcg_at_10=0.0308,
        coverage_pct=10.02,
        diversity_score=0.8231,
        latency_p95_ms=70.73,
        strengths=[
            "Highest intra-list diversity in CineSense (0.8231)",
            "Solves score-scale incompatibilities using rank reciprocal fusion",
            "MMR diversification prevents repetitive genre echo chambers",
        ],
        tradeoffs=[
            "Higher latency overhead aggregating 5 retrieval stages (70.73 ms)",
            "Trades raw collaborative precision for catalogue discovery",
            "Multi-stage pipeline engineering complexity",
        ],
    ),
]

_GENAI_METRICS = GenAiEvalMetrics(
    grounding_rate_pct=100.0,
    hallucinated_ids_count=0,
    tool_execution_success_rate=98.5,
    avg_time_to_first_token_ms=280.0,
    total_eval_queries=150,
    tested_tools=[
        "search_movies",
        "get_movie_details",
        "find_similar_movies",
        "get_user_taste_profile",
        "compare_movies",
    ],
)

_FORMULAS: list[MetricFormulaInfo] = [
    MetricFormulaInfo(
        name="NDCG@K (Normalized Discounted Cumulative Gain)",
        symbol="NDCG@K = DCG@K / IDCG@K",
        formula=r"DCG@K = \sum_{i=1}^K \frac{2^{rel_i} - 1}{\log_2(i + 1)}",
        explanation="Measures ranking quality by rewarding relevant recommendations placed near the top of the list while logarithmically penalizing relevant items ranked further down.",
    ),
    MetricFormulaInfo(
        name="Recall@K",
        symbol=r"Recall@K = |Recs@K \cap Relevant| / |Relevant|",
        formula=r"Recall@K = \frac{\sum_{i=1}^K \mathbb{I}(r_i \in \text{Target})}{|\text{Target}|}",
        explanation="Proportion of the user's held-out favorite test movies that the model successfully retrieved within its top K suggestions.",
    ),
    MetricFormulaInfo(
        name="Intra-List Diversity (ILD)",
        symbol="ILD = 1 - Mean Pairwise Cosine Similarity",
        formula=r"ILD(R) = \frac{2}{|R|(|R|-1)} \sum_{i < j} (1 - \cos(\mathbf{e}_i, \mathbf{e}_j))",
        explanation="Computes the average distance between all recommended movie vectors in the latent embedding space. Higher values indicate broader genre/thematic coverage.",
    ),
    MetricFormulaInfo(
        name="Reciprocal Rank Fusion (RRF)",
        symbol=r"RRF(d) = \sum_{m} \frac{w_m}{k + \text{rank}_m(d)}",
        formula=r"\text{Score}_{RRF}(d) = \sum_{m \in \text{Models}} w_m \cdot \frac{1}{60 + \text{Rank}_m(d)}",
        explanation="Combines disparate algorithmic rankings (cosine similarity vs latent dot products vs vote counts) purely by rank positions, making it robust against outlier score distributions.",
    ),
]


@router.get("/benchmarks", response_model=BenchmarkResponse)
async def get_benchmarks():
    """
    Return offline recommendation benchmarks and GenAI grounding metrics.
    Evaluated over temporal leave-last-5-out split across 561 test users and 9,741 movies.
    """
    log.info("serving_evaluation_benchmarks")
    return BenchmarkResponse(
        summary=EvaluationSummary(),
        models=_BENCHMARK_MODELS,
        genai=_GENAI_METRICS,
        formulas=_FORMULAS,
    )


@router.get("/genai", response_model=GenAiEvalMetrics)
async def get_genai_evaluation():
    """Return specific GenAI grounding and tool calling benchmark metrics."""
    return _GENAI_METRICS
