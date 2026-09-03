from pathlib import Path
import sys

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.recsys.collaborative.item_cf import build_item_cf_matrix
from app.recsys.collaborative.als import train_als_model


def main() -> None:
    print("Building Item-Item Collaborative Filtering similarity matrix...")
    S = build_item_cf_matrix(min_co_raters=5, top_k=50)
    print(f"Item-CF matrix built successfully: shape {S.shape}, {S.nnz} non-zero entries.")

    print("\nTraining ALS Matrix Factorization model...")
    u_factors, i_factors = train_als_model(factors=64, regularization=0.05, iterations=15, random_state=42)
    print(f"ALS training complete: user_factors {u_factors.shape}, item_factors {i_factors.shape}.")


if __name__ == "__main__":
    main()
