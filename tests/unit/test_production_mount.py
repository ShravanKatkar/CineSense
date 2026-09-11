import pytest
from httpx import ASGITransport, AsyncClient
from app.core.paths import MOVIES_PARQUET, PROCESSED_DIR, ROOT_DIR
from app.main import app


@pytest.mark.asyncio
async def test_api_health_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_api_routes_isolated_from_spa():
    """Ensure API endpoints always return JSON and never HTML SPA catch-all."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/non_existent_endpoint")
    assert res.status_code == 404
    # Content type should be json
    assert "application/json" in res.headers.get("content-type", "")


def test_processed_data_paths_resolution():
    """Ensure paths.py resolves directory hierarchy correctly."""
    assert ROOT_DIR.exists()
    assert PROCESSED_DIR.exists()
    assert MOVIES_PARQUET.exists()


def test_docker_compose_valid_yaml():
    """Verify docker-compose.yml syntax and service configurations."""
    import yaml
    compose_file = ROOT_DIR / "docker-compose.yml"
    assert compose_file.exists()
    with open(compose_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    assert "services" in data
    assert "db" in data["services"]
    assert "redis" in data["services"]
    assert "backend" in data["services"]
    assert "pgdata" in data.get("volumes", {})
    assert "redisdata" in data.get("volumes", {})
    assert "cinesense-net" in data.get("networks", {})


def test_dockerfile_structure():
    """Verify Dockerfile contains multi-stage build, healthcheck, and entrypoint."""
    dockerfile = ROOT_DIR / "Dockerfile"
    assert dockerfile.exists()
    content = dockerfile.read_text(encoding="utf-8")
    assert "FROM node:20-alpine AS frontend-builder" in content
    assert "FROM python:3.12-slim AS backend-runtime" in content
    assert "HEALTHCHECK" in content
    assert "docker-entrypoint.sh" in content


def test_dockerignore_and_cloud_blueprints():
    """Verify production .dockerignore and turnkey cloud deployment blueprints exist."""
    import json
    import yaml

    # 1. .dockerignore
    dockerignore = ROOT_DIR / ".dockerignore"
    assert dockerignore.exists()
    di_content = dockerignore.read_text(encoding="utf-8")
    assert "node_modules" in di_content
    assert ".venv" in di_content

    # 2. Render Blueprint
    render_yaml = ROOT_DIR / "render.yaml"
    assert render_yaml.exists()
    with open(render_yaml, "r", encoding="utf-8") as f:
        render_data = yaml.safe_load(f)
    assert "services" in render_data
    assert "databases" in render_data

    # 3. Railway Configuration
    railway_json = ROOT_DIR / "railway.json"
    assert railway_json.exists()
    with open(railway_json, "r", encoding="utf-8") as f:
        railway_data = json.load(f)
    assert "build" in railway_data
    assert "deploy" in railway_data

    # 4. Fly.io Configuration
    fly_toml = ROOT_DIR / "fly.toml"
    assert fly_toml.exists()

    # 5. One-Click Launchers
    assert (ROOT_DIR / "docker-start.bat").exists()
    assert (ROOT_DIR / "docker-start.sh").exists()


