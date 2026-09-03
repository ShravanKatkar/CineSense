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
- **Machine Learning:** NumPy, pandas, scikit-learn, SciPy sparse, `implicit` (ALS)
- **Embeddings:** Voyage AI `voyage-4-lite` (512-dim) / `sentence-transformers` for local benchmarks
- **LLM / GenAI:** Anthropic SDK (`claude-opus-5`), Pydantic structured outputs, prompt caching
- **Frontend:** React 19, Vite, TypeScript, Tailwind CSS, shadcn/ui, TanStack Query

## Quick Start

### One-Click Launch (Windows)
Double-click `start.bat` or run in terminal:
```cmd
.\start.bat
```
This automatically launches both the FastAPI backend (`http://localhost:8000`) and the React Vite frontend (`http://localhost:5173`) in separate windows.

### Manual Launch
1. **Backend:**
   ```powershell
   C:\Users\shara\.local\bin\uv.exe run --project backend fastapi dev backend/app/main.py --port 8000
   ```
2. **Frontend:**
   ```powershell
   cd frontend
   npm run dev
   ```

## TMDB Attribution
This product uses the TMDB API but is not endorsed or certified by TMDB.

## Citation
Harper, F. M., & Konstan, J. A. (2015). *The MovieLens Datasets: History and Context.* ACM Transactions on Interactive Intelligent Systems (TiiS), 5(4), 19.
