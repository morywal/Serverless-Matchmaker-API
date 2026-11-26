# Serverless-Matchmaker-API
A matchmaker AWS project based on Valorant's ranking system.

Phase 1: a serverless player + leaderboard API (Python 3.12, AWS SAM, HTTP API, Lambda, DynamoDB).

## Endpoints

| Method | Path | Description |
| --- | --- | --- |
| POST | `/players` | Create a player. Body: `{"username": "TenZ", "region": "NA", "mmr": 1000}` (`mmr` optional, default 1000). Returns 201. |
| GET | `/leaderboard?region=NA&limit=20` | Top players in a region by MMR, highest first. `region` is required (NA, EU, AP); `limit` defaults to 20 and is capped at 100. |

Invalid input returns 400 with `{"error": "..."}`.

## Rank tiers

| MMR | Tier |
| --- | --- |
| 0–399 | Iron |
| 400–799 | Bronze |
| 800–1199 | Silver |
| 1200–1599 | Gold |
| 1600–1999 | Platinum |
| 2000–2399 | Diamond |
| 2400–2799 | Ascendant |
| 2800–3199 | Immortal |
| 3200+ | Radiant |

Thresholds live in `src/common/ranks.py`.

## Data model

Single DynamoDB table (`MatchmakerTable`, on-demand):

- Player profile: `PK = PLAYER#<playerId>`, `SK = PROFILE`, plus `username`, `region`, `mmr`, `rankTier`, `createdAtUtc`.
- `LeaderboardIndex` GSI: `region` (HASH) + `mmr` (RANGE, Number), projection ALL. The leaderboard is a descending query on this index, never a scan.

## Run the tests

Tests use moto to fake DynamoDB in memory, so no AWS account or credentials are needed.

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
pytest
```

## Deploy

```bash
sam build
sam deploy --guided
```

Stack outputs: `HttpApiUrl` and `MatchmakerTableName`.
