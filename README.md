# CineSense — AI Engineering Movie Recommendation & RAG System

> **CineSense** is a production-grade movie recommendation and natural language search system built over ~9,700 movies (MovieLens `ml-latest-small` joined with TMDB metadata).

![Architecture](docs/figures/architecture.png)

## Overview
CineSense implements a two-stage hybrid recommendation engine and a RAG-grounded natural language search and conversational assistant layer:
1. **Deterministic Recommendation Engine:** 5 levels of recommenders (Weighted Popularity baseline, TF-IDF Content, Embedding kNN, Item-Item Collaborative Filtering, and ALS Matrix Factorization), combined via Reciprocal Rank Fusion (RRF) and Maximal Marginal Relevance (MMR) diversification.
2. **GenAI Layer:** Structured intent parsing using Claude Opus 5, vector retrieval over PostgreSQL `pgvector`, and grounded explanation generation with strict output validation (`movie_id ∈ candidate_ids`) ensuring **0% hallucinated movie IDs**.

## Tech Stack
- **Language & Runtime:** Python 3.12, managed with `uv`
- **Backend:** FastAPI, Uvicorn, Pydantic v2, structlog
- **Database & Vectors:** PostgreSQL 16 + `pgvector` (HNSW index) via SQLAlchemy 2.0 async & Alembic
- **Caching Tier:** Redis 7 with automatic fallback to in-memory TTL caching (`cachetools`)
- **Machine Learning:** NumPy, pandas, scikit-learn, SciPy sparse, `implicit` (ALS Matrix Factorization)
- **Embeddings:** Voyage AI (512-dim) / `sentence-transformers` for offline evaluation benchmarks
- **LLM / GenAI:** Groq Llama-3.3-70B ReAct Agent, Candidate Whitelist Grounding (0% Hallucination Guarantee)
- **Frontend:** React 19, Vite, Lucide Icons, Recharts, Custom Matinee Vintage Cinema Design System
- **Containerization & CI/CD:** Multi-stage Docker, Docker Compose, GitHub Actions, Render & Railway Blueprints

## Quick Start

### 1. One-Click Production Launch with Docker
```bash
# Windows
.\docker-start.bat

# Linux / macOS
./docker-start.sh
```
Or directly via Docker Compose:
```bash
docker compose up --build -d
```
- **Web Platform & REST API:** `http://localhost:8000`
- **Interactive Swagger Docs:** `http://localhost:8000/docs`
- **System Health:** `http://localhost:8000/api/v1/health`
- **Cache & Worker Diagnostics:** `http://localhost:8000/api/v1/system/status`

### 2. Local Development Launch
Double-click `start.bat` or run:
```cmd
.\start.bat
```
This automatically launches both the FastAPI backend (`http://localhost:8000`) and the Vite React frontend (`http://localhost:5173`).

## Cloud Deployment
- **Render:** One-click deployment using [`render.yaml`](render.yaml)
- **Railway:** One-click deployment using [`railway.json`](railway.json)
- **Fly.io:** Native deployment using [`fly.toml`](fly.toml)
See [`docs/deployment-guide.md`](docs/deployment-guide.md) for full cloud hosting walkthroughs.

## TMDB Attribution
This product uses the TMDB API but is not endorsed or certified by TMDB.

## Citation
Harper, F. M., & Konstan, J. A. (2015). *The MovieLens Datasets: History and Context.* ACM Transactions on Interactive Intelligent Systems (TiiS), 5(4), 19.
