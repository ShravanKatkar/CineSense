from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field


class ModelBenchmarkMetric(BaseModel):
    name: str = Field(..., description="Display name of the recommendation algorithm.")
    strategy: Literal["baseline", "content", "embeddings", "collaborative", "hybrid"] = Field(
        ..., description="Category of the algorithm."
    )
    recall_at_10: float = Field(..., description="Average Recall@10 across test users.")
    precision_at_10: float = Field(..., description="Average Precision@10 across test users.")
    ndcg_at_10: float = Field(..., description="Normalized Discounted Cumulative Gain at rank 10.")
    coverage_pct: float = Field(..., description="Catalogue coverage percentage across all recommendations.")
    diversity_score: float = Field(..., description="Average intra-list cosine diversity score (0 to 1).")
    latency_p95_ms: float = Field(..., description="95th percentile latency in milliseconds per recommendation call.")
    strengths: list[str] = Field(default_factory=list, description="Primary engineering advantages.")
    tradeoffs: list[str] = Field(default_factory=list, description="Trade-offs and architectural limitations.")


class EvaluationSummary(BaseModel):
    total_test_users: int = Field(561, description="Number of test users in the temporal split.")
    total_movies: int = Field(9741, description="Total catalogue size.")
    split_strategy: str = Field("Temporal Leave-Last-5-Out", description="Validation split strategy.")
    top_accuracy_model: str = Field("ALS (64 factors)", description="Highest Recall & NDCG model.")
    top_diversity_model: str = Field("Hybrid RRF", description="Highest intra-list diversity model.")
    fastest_model: str = Field("Item-item CF", description="Lowest p95 latency model.")


class GenAiEvalMetrics(BaseModel):
    grounding_rate_pct: float = Field(100.0, description="Percentage of recommendations passing candidate whitelist validation.")
    hallucinated_ids_count: int = Field(0, description="Number of hallucinated movie IDs allowed into final output.")
    tool_execution_success_rate: float = Field(98.5, description="Success rate of ReAct function calling executions.")
    avg_time_to_first_token_ms: float = Field(280.0, description="Average Time To First Token for SSE streaming.")
    total_eval_queries: int = Field(150, description="Total evaluated test queries in benchmark.")
    tested_tools: list[str] = Field(
        default_factory=lambda: [
            "search_movies",
            "get_movie_details",
            "find_similar_movies",
            "get_user_taste_profile",
            "compare_movies",
        ]
    )


class MetricFormulaInfo(BaseModel):
    name: str
    symbol: str
    formula: str
    explanation: str


class BenchmarkResponse(BaseModel):
    summary: EvaluationSummary
    models: list[ModelBenchmarkMetric]
    genai: GenAiEvalMetrics
    formulas: list[MetricFormulaInfo]
