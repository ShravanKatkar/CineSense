import zipfile
from pathlib import Path
import httpx

URL = "https://files.grouplens.org/datasets/movielens/ml-latest-small.zip"
DEST = Path("data/raw")


def download_movielens() -> None:
    target_dir = DEST / "ml-latest-small"
    if (target_dir / "ratings.csv").exists() and (target_dir / "movies.csv").exists():
        print("MovieLens ml-latest-small dataset is already present on disk.")
        return

    DEST.mkdir(parents=True, exist_ok=True)
    zip_path = DEST / "ml-latest-small.zip"
    print(f"Downloading {URL}...")

    with httpx.stream("GET", URL, follow_redirects=True, timeout=60.0, verify=False) as response:
        response.raise_for_status()
        with zip_path.open("wb") as f:
            for chunk in response.iter_bytes(chunk_size=8192):
                f.write(chunk)

    print("Extracting archive...")
    with zipfile.ZipFile(zip_path) as zip_ref:
        zip_ref.extractall(DEST)

    zip_path.unlink()
    print("MovieLens dataset successfully downloaded and extracted to data/raw/ml-latest-small/")


if __name__ == "__main__":
    download_movielens()
