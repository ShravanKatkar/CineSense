# CineSense — Production Deployment & Cloud Hosting Guide

This guide covers deployment strategies for **CineSense**, from local Docker Compose containerization to production cloud deployment (Render, Railway, Fly.io, or AWS).

---

## 1. Local Production Launch with Docker Compose

CineSense includes a multi-stage production Docker setup orchestrating:
1. **PostgreSQL 16 + `pgvector`**: Stores users, ratings, favorites, history, and 512-dim movie embeddings.
2. **Unified CineSense Application**: Multi-stage container compiling the React 19 Vite SPA into static assets and serving both the REST API (`/api/v1/...`) and the web client (`/`) with automated database migrations via `docker-entrypoint.sh`.

### Quick Start (One-Click Launchers)
- **Windows**: Double click `docker-start.bat` (automatically detects Docker Desktop, launches daemon if needed, and starts all containers).
- **Linux / macOS**: Run `./docker-start.sh`.

Or run manually via Docker CLI:
```bash
# 1. Build and start PostgreSQL + pgvector, Redis, and CineSense
docker compose up --build -d

# 2. View unified container logs
docker compose logs -f backend
```

Once started:
- **Web Platform & REST API**: `http://localhost:8000`
- **Interactive Swagger Docs**: `http://localhost:8000/docs`
- **System Health Endpoint**: `http://localhost:8000/api/v1/health`
- **Cache & Worker Diagnostics**: `http://localhost:8000/api/v1/system/status`
- **PostgreSQL Database**: `localhost:5432`
- **Redis Cache**: `localhost:6379`

To shut down:
```bash
docker compose down
```

---

## 2. Cloud Deployment: Railway (Recommended — 5 Minutes)

Railway provides native support for multi-container architectures with PostgreSQL + `pgvector`.

### Step-by-step:
1. **Create a Railway Project**:
   - Go to [railway.app](https://railway.app) and create a new project from your GitHub repository.
2. **Add a PostgreSQL Database**:
   - In your project canvas, click **+ New** $\to$ **Database** $\to$ **Add PostgreSQL**.
   - Under the database **Settings** $\to$ **Connect**, enable the `vector` extension:
     ```sql
     CREATE EXTENSION IF NOT EXISTS vector;
     ```
3. **Deploy CineSense App**:
   - Click **+ New** $\to$ **GitHub Repo** $\to$ Select your CineSense repository.
   - Railway will automatically detect the root `Dockerfile`.
4. **Configure Environment Variables**:
   In the CineSense Service $\to$ **Variables**, add:
   | Variable | Description |
   | :--- | :--- |
   | `DATABASE_URL` | Reference Railway's connection: `${{Postgres.DATABASE_URL}}` |
   | `JWT_SECRET_KEY` | Generate a 64-char random hex string (`openssl rand -hex 32`) |
   | `GROQ_API_KEY` | Your Groq Cloud API key (for Llama-3.3 AI Assistant) |
   | `TMDB_API_KEY` | Your TMDB API read token or key (for dynamic poster enrichment) |
   | `ENVIRONMENT` | `production` |
5. **Set Public Networking Domain**:
   - Go to **Networking** $\to$ **Generate Domain** (e.g. `cinesense-production.up.railway.app`).
   - The app will automatically run Alembic migrations on startup and serve the complete platform!

---

## 3. Cloud Deployment: Render (One-Click Blueprint via `render.yaml`)

CineSense includes a preconfigured Infrastructure-as-Code blueprint in [`render.yaml`](file:///c:/Users/shara/OneDrive/Desktop/projects/Movie%20recoomedation%20system/render.yaml).

### Turnkey 1-Click Deployment:
1. Push this repository to your GitHub account.
2. Log in to [render.com](https://render.com) and click **New** $\to$ **Blueprint**.
3. Connect your repository. Render will automatically read `render.yaml` and provision:
   - **`cinesense-app`**: Unified Docker web service with automatic health checks.
   - **`cinesense-db`**: PostgreSQL 16 database with vector extension.
   - **`cinesense-redis`**: Managed Redis cache.
4. Input your `TMDB_API_KEY` and `GROQ_API_KEY` in the Render dashboard prompt, and click **Apply**.
5. Once built, your app is live on your custom `onrender.com` URL with SSL enabled!

---

## 4. Cloud Deployment: Fly.io

CineSense includes a native [`fly.toml`](file:///c:/Users/shara/OneDrive/Desktop/projects/Movie%20recoomedation%20system/fly.toml) configuration.

```bash
# 1. Install Flyctl CLI and authenticate
fly auth login

# 2. Launch application
fly launch

# 3. Set secrets
fly secrets set TMDB_API_KEY="your_tmdb_key" GROQ_API_KEY="your_groq_key" JWT_SECRET_KEY="your_64_char_hex"

# 4. Deploy
fly deploy
```

---

## 5. CI/CD Automation: GitHub Actions

CineSense includes automated continuous integration via [`.github/workflows/ci-cd.yml`](file:///c:/Users/shara/OneDrive/Desktop/projects/Movie%20recoomedation%20system/.github/workflows/ci-cd.yml).
On every push or pull request to `main`:
1. **Automated Testing**: Spins up PostgreSQL + pgvector and Redis service containers, installs dependencies with `uv`, and executes the complete backend unit test suite.
2. **Frontend Compilation**: Builds and minifies the Vite React bundle.
3. **Docker Build Verification**: Validates that the multi-stage `Dockerfile` compiles cleanly into a production container image.

---

## 6. Environment Variables Reference

| Variable | Type | Default | Purpose |
| :--- | :--- | :--- | :--- |
| `DATABASE_URL` | String | `sqlite+aiosqlite:///./cinesense.db` | Async database connection string. |
| `JWT_SECRET_KEY` | String | `0123456789...` | 256-bit secret key used to sign JWT tokens. |
| `JWT_ALGORITHM` | String | `HS256` | Cryptographic algorithm for authentication. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Integer | `60` | User session duration. |
| `GROQ_API_KEY` | String | `""` | Powers the ReAct AI Agent and movie comparisons. |
| `TMDB_API_KEY` | String | `""` | Dynamic movie metadata and real TMDB posters. |
| `ENVIRONMENT` | String | `development` | `production` enables strict error logging & CORS. |
| `CORS_ORIGINS` | JSON List | `["*"]` | Allowed origins for browser fetch requests. |

---

## 5. Production Health & Monitoring

CineSense includes automatic health check and metric endpoints:
- **System Health**: `GET /api/v1/health`
  - Returns `{"status": "ok", "app_version": "1.0.0", "environment": "production"}`.
- **Model Evaluation Benchmarks**: `GET /api/v1/evaluation/benchmarks`
  - Provides empirical performance benchmarks for offline inspection.
- **OpenAPI Schema**: `GET /openapi.json`
