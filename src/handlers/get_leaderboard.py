"""GET /leaderboard: top players in a region, highest MMR first."""

import logging
import os

import boto3
from boto3.dynamodb.conditions import Key

from common.constants import VALID_REGIONS
from common.responses import bad_request, ok, server_error

logger = logging.getLogger()
logger.setLevel(logging.INFO)

DEFAULT_LIMIT = 20
MAX_LIMIT = 100
INDEX_NAME = "LeaderboardIndex"

_table = None


def _get_table():
    global _table
    if _table is None:
        _table = boto3.resource("dynamodb").Table(os.environ["TABLE_NAME"])
    return _table


def _parse_params(event: dict):
    params = event.get("queryStringParameters") or {}

    region = params.get("region")
    if region not in VALID_REGIONS:
        raise ValueError(f"region query parameter is required and must be one of {list(VALID_REGIONS)}")

    raw_limit = params.get("limit")
    if raw_limit is None or raw_limit == "":
        limit = DEFAULT_LIMIT
    else:
        try:
            limit = int(raw_limit)
        except ValueError:
            raise ValueError("limit must be a positive integer")
        if limit < 1:
            raise ValueError("limit must be a positive integer")
        # Values above the cap are clamped rather than rejected.
        limit = min(limit, MAX_LIMIT)

    return region, limit


def lambda_handler(event, context):
    try:
        region, limit = _parse_params(event)
    except ValueError as exc:
        return bad_request(str(exc))

    try:
        result = _get_table().query(
            IndexName=INDEX_NAME,
            KeyConditionExpression=Key("region").eq(region),
            ScanIndexForward=False,
            Limit=limit,
        )
    except Exception:
        logger.exception("Leaderboard query failed for region %s", region)
        return server_error("Could not load leaderboard")

    leaderboard = [
        {
            "rank": position,
            "playerId": item.get("playerId"),
            "username": item.get("username"),
            "mmr": item.get("mmr"),
            "rankTier": item.get("rankTier"),
        }
        for position, item in enumerate(result.get("Items", []), start=1)
    ]

    return ok({"region": region, "count": len(leaderboard), "leaderboard": leaderboard})
