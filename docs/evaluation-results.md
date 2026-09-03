# CineSense Offline Recommender Evaluation Results

Evaluated against temporal leave-last-5-out split across 561 test users over 9741 movies.

| Recommender           |   Recall@10 |   Precision@10 |   NDCG@10 | Coverage   |   Diversity | Latency p95   |
|:----------------------|------------:|---------------:|----------:|:-----------|------------:|:--------------|
| Popularity (weighted) |      0.0075 |         0.0021 |    0.0053 | 0.12%      |      0.5111 | 7.26 ms       |
| TF-IDF content        |      0.0142 |         0.0046 |    0.0106 | 19.64%     |      0.5879 | 9.08 ms       |
| Embedding kNN         |      0.0157 |         0.0055 |    0.0107 | 13.16%     |      0.3798 | 1.51 ms       |
| Item-item CF          |      0.0633 |         0.0237 |    0.0489 | 12.97%     |      0.6165 | 0.29 ms       |
| ALS (64 factors)      |      0.1528 |         0.0551 |    0.1181 | 5.27%      |      0.5852 | 0.41 ms       |
| Hybrid RRF            |      0.0332 |         0.0121 |    0.0308 | 10.02%     |      0.8231 | 70.73 ms      |

