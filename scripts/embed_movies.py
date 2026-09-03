import json
from pathlib import Path
import sys
import numpy as np
import pandas as pd
import structlog

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.core.config import get_settings

log = structlog.get_logger()
PROCESSED_DIR = Path("data/processed")
EMBEDDINGS_NPY = PROCESSED_DIR / "movie_embeddings.npy"
EMBEDDINGS_MAP = PROCESSED_DIR / "movie_embeddings_map.json"


def generate_embeddings() -> None:
    movies_path = PROCESSED_DIR / "movies.parquet"
    if not movies_path.exists():
        log.error("movies_parquet_missing", path=str(movies_path))
        return

    df = pd.read_parquet(movies_path)
    df["movie_id"] = df["movielens_id"].dropna().astype(int)
    movie_ids = df["movie_id"].tolist()
    documents = df["embedding_document"].fillna(df["title"]).tolist()

    settings = get_settings()
    voyage_key = settings.voyage_api_key.get_secret_value()

    embeddings: np.ndarray | None = None
    dim = 512

    if voyage_key and voyage_key != "your_voyage_api_key_here":
        try:
            log.info("generating_voyage_embeddings", count=len(documents))
            import voyageai

            client = voyageai.Client(api_key=voyage_key)
            batch_size = 128
            all_vectors: list[list[float]] = []

            for i in range(0, len(documents), batch_size):
                batch_docs = documents[i : i + batch_size]
                res = client.embed(
                    texts=batch_docs,
                    model="voyage-4-lite",
                    input_type="document",
                    output_dimension=dim,
                )
                all_vectors.extend(res.embeddings)

            embeddings = np.array(all_vectors, dtype=np.float32)
            log.info("voyage_embeddings_generated", shape=embeddings.shape)
        except Exception as exc:
            log.warning("voyage_embedding_failed", error=str(exc))

    if embeddings is None:
        log.info("generating_local_minilm_embeddings", count=len(documents))
        from sentence_transformers import SentenceTransformer

        model = SentenceTransformer("all-MiniLM-L6-v2")
        raw_vecs = model.encode(documents, show_progress_bar=True, normalize_embeddings=True)

        # Pad 384-dim to 512-dim for schema uniformity if needed, or keep 384
        if raw_vecs.shape[1] < dim:
            padding = np.zeros((raw_vecs.shape[0], dim - raw_vecs.shape[1]), dtype=np.float32)
            embeddings = np.hstack([raw_vecs, padding])
        else:
            embeddings = raw_vecs.astype(np.float32)

        log.info("local_embeddings_generated", shape=embeddings.shape)

    # Save to disk
    np.save(EMBEDDINGS_NPY, embeddings)
    id_map = {mid: idx for idx, mid in enumerate(movie_ids)}
    EMBEDDINGS_MAP.write_text(json.dumps(id_map), encoding="utf-8")
    log.info("saved_embedding_artifacts", npy=str(EMBEDDINGS_NPY), json=str(EMBEDDINGS_MAP))


if __name__ == "__main__":
    generate_embeddings()
