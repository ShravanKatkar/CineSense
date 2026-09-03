from pathlib import Path
import re
import matplotlib.pyplot as plt
import pandas as pd

DATA_DIR = Path("data/raw/ml-latest-small")
FIG_DIR = Path("docs/figures")


def run_eda() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading MovieLens files...")
    ratings = pd.read_csv(DATA_DIR / "ratings.csv")
    movies = pd.read_csv(DATA_DIR / "movies.csv")
    links = pd.read_csv(DATA_DIR / "links.csv")

    n_users = ratings["userId"].nunique()
    n_movies = movies["movieId"].nunique()
    n_ratings = len(ratings)
    sparsity = 1.0 - (n_ratings / (n_users * n_movies))

    print(f"Users: {n_users}")
    print(f"Movies: {n_movies}")
    print(f"Ratings: {n_ratings}")
    print(f"Matrix Sparsity: {sparsity:.5f} ({sparsity * 100:.2f}%)")

    # 1. Rating Distribution
    plt.figure(figsize=(8, 5))
    counts = ratings["rating"].value_counts().sort_index()
    plt.bar(counts.index.astype(str), counts.values, color="#4F46E5", edgecolor="black")
    plt.title("MovieLens Rating Distribution (0.5 to 5.0 Stars)")
    plt.xlabel("Rating")
    plt.ylabel("Count")
    plt.grid(axis="y", linestyle="--", alpha=0.7)
    plt.tight_layout()
    plt.savefig(FIG_DIR / "rating_dist.png", dpi=150)
    plt.close()

    # 2. Long Tail (Ratings per Movie)
    plt.figure(figsize=(8, 5))
    movie_counts = ratings["movieId"].value_counts().values
    plt.loglog(range(1, len(movie_counts) + 1), movie_counts, color="#EC4899", linewidth=2)
    plt.title("Movie Popularity Long Tail (Log-Log Scale)")
    plt.xlabel("Movie Rank")
    plt.ylabel("Number of Ratings")
    plt.grid(True, which="both", linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(FIG_DIR / "long_tail.png", dpi=150)
    plt.close()

    # 3. User Activity Distribution
    plt.figure(figsize=(8, 5))
    user_counts = ratings["userId"].value_counts()
    plt.hist(user_counts, bins=30, color="#10B981", edgecolor="black", log=True)
    plt.title("User Rating Activity Distribution (Log Scale)")
    plt.xlabel("Ratings per User")
    plt.ylabel("User Count")
    plt.grid(axis="y", linestyle="--", alpha=0.7)
    plt.tight_layout()
    plt.savefig(FIG_DIR / "user_activity.png", dpi=150)
    plt.close()

    # 4. Genre Counts
    plt.figure(figsize=(10, 6))
    genre_series = movies["genres"].str.split("|").explode()
    genre_counts = genre_series[genre_series != "(no genres listed)"].value_counts()
    plt.barh(genre_counts.index[::-1], genre_counts.values[::-1], color="#F59E0B")
    plt.title("Movie Count by Genre")
    plt.xlabel("Number of Movies")
    plt.grid(axis="x", linestyle="--", alpha=0.7)
    plt.tight_layout()
    plt.savefig(FIG_DIR / "genre_counts.png", dpi=150)
    plt.close()

    # 5. Ratings / Movies by Release Year
    plt.figure(figsize=(10, 5))
    def extract_year(title: str) -> int | None:
        match = re.search(r"\((\d{4})\)\s*$", str(title).strip())
        return int(match.group(1)) if match else None

    movies["year"] = movies["title"].apply(extract_year)
    year_counts = movies["year"].value_counts().sort_index()
    plt.plot(year_counts.index, year_counts.values, color="#6366F1", linewidth=2)
    plt.title("Movies by Release Year")
    plt.xlabel("Release Year")
    plt.ylabel("Movie Count")
    plt.xlim(1910, 2020)
    plt.grid(True, linestyle="--", alpha=0.7)
    plt.tight_layout()
    plt.savefig(FIG_DIR / "ratings_by_year.png", dpi=150)
    plt.close()

    # Links summary
    missing_tmdb = links["tmdbId"].isna().sum()
    print(f"Links total: {len(links)}, missing tmdbId: {missing_tmdb}")
    print("EDA figures generated successfully in docs/figures/")


if __name__ == "__main__":
    run_eda()
