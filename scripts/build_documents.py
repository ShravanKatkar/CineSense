hashlib_import = False
import hashlib
from pathlib import Path
import pandas as pd

PROCESSED_DIR = Path("data/processed")


def sanitize_token(text: str) -> str:
    if not text or not isinstance(text, str):
        return ""
    return text.lower().strip().replace(" ", "_")


def build_tfidf_document(row: pd.Series) -> str:
    title = str(row["title"])
    overview = str(row["overview"]) if pd.notna(row["overview"]) else ""
    tagline = str(row["tagline"]) if pd.notna(row["tagline"]) else ""

    genres = [sanitize_token(g) for g in row.get("genre_names", []) if g]
    keywords = [sanitize_token(k) for k in row.get("keyword_names", []) if k]
    directors = [sanitize_token(d) for d in row.get("director_names", []) if d]
    cast = [sanitize_token(c) for c in row.get("cast_names", [])[:5] if c]

    doc_parts = [
        (title + " ") * 2,
        overview,
        tagline,
        (" ".join(genres) + " ") * 3,
        " ".join(keywords),
        (" ".join(directors) + " ") * 2,
        " ".join(cast),
    ]

    return " ".join([p for p in doc_parts if p]).strip()


def build_embedding_document(row: pd.Series) -> str:
    parts: list[str] = []
    title = str(row["title"])

    rel_date = row.get("release_date")
    year = str(rel_date)[:4] if pd.notna(rel_date) and str(rel_date)[:4].isdigit() else None

    if year:
        parts.append(f"{title} ({year}).")
    else:
        parts.append(f"{title}.")

    if pd.notna(row.get("tagline")) and row["tagline"]:
        parts.append(str(row["tagline"]).strip().rstrip(".") + ".")

    if pd.notna(row.get("overview")) and row["overview"]:
        parts.append(str(row["overview"]).strip())

    genres = row.get("genre_names", [])
    if isinstance(genres, (list, tuple)) and genres:
        parts.append("Genres: " + ", ".join(genres) + ".")

    directors = row.get("director_names", [])
    if isinstance(directors, (list, tuple)) and directors:
        parts.append("Directed by " + ", ".join(directors) + ".")

    cast = row.get("cast_names", [])
    if isinstance(cast, (list, tuple)) and cast:
        parts.append("Starring " + ", ".join(cast[:5]) + ".")

    keywords = row.get("keyword_names", [])
    if isinstance(keywords, (list, tuple)) and keywords:
        parts.append("Themes: " + ", ".join(keywords[:15]) + ".")

    if pd.notna(row.get("certification")) and row["certification"]:
        parts.append(f"Rated {row['certification']}.")

    return " ".join(parts).strip()


def compute_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def process_documents() -> None:
    parquet_path = PROCESSED_DIR / "movies.parquet"
    if not parquet_path.exists():
        print(f"Error: {parquet_path} does not exist. Run build_movies_table.py first.")
        return

    df = pd.read_parquet(parquet_path)
    print(f"Building TF-IDF and embedding documents for {len(df)} movies...")

    df["document"] = df.apply(build_tfidf_document, axis=1)
    df["embedding_document"] = df.apply(build_embedding_document, axis=1)
    df["document_sha256"] = df["embedding_document"].apply(compute_sha256)

    df.to_parquet(parquet_path, index=False)
    print(f"Updated {parquet_path} with document, embedding_document, and document_sha256.")


if __name__ == "__main__":
    process_documents()
