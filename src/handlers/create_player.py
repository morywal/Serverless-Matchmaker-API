"""POST /players: create a player profile."""

import json
import logging
import os
import uuid
from datetime import datetime, timezone

import boto3

from common.constants import VALID_REGIONS
from common.ranks import get_rank_tier
from common.responses import bad_request, created, server_error

logger = logging.getLogger()
logger.setLevel(logging.INFO)

DEFAULT_MMR = 1000

_table = None


def _get_table():
    global _table
    if _table is None:
        _table = boto3.resource("dynamodb").Table(os.environ["TABLE_NAME"])
    return _table


def _parse_body(event: dict):
    raw = event.get("body")
    if raw is None or raw == "":
        raise ValueError("Request body is required")
    if event.get("isBase64Encoded"):
        import base64

        raw = base64.b64decode(raw).decode("utf-8")
    try:
        body = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        raise ValueError("Request body must be valid JSON")
    if not isinstance(body, dict):
        raise ValueError("Request body must be a JSON object")
    return body


def _validate(body: dict):
    username = body.get("username")
    if not isinstance(username, str) or not username.strip():
        raise ValueError("username is required and must be a non-empty string")

    region = body.get("region")
    if region not in VALID_REGIONS:
        raise ValueError(f"region must be one of {list(VALID_REGIONS)}")

    mmr = body.get("mmr", DEFAULT_MMR)
    # bool is a subclass of int in Python, so reject it explicitly.
    if isinstance(mmr, bool) or not isinstance(mmr, int) or mmr < 0:
        raise ValueError("mmr must be an integer >= 0")

    return username.strip(), region, mmr


def lambda_handler(event, context):
    try:
        username, region, mmr = _validate(_parse_body(event))
    except ValueError as exc:
        return bad_request(str(exc))

    player_id = str(uuid.uuid4())
    player = {
        "playerId": player_id,
        "username": username,
        "region": region,
        "mmr": mmr,
        "rankTier": get_rank_tier(mmr),
        "createdAtUtc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
    }

    try:
        _get_table().put_item(
            Item={"PK": f"PLAYER#{player_id}", "SK": "PROFILE", **player},
            ConditionExpression="attribute_not_exists(PK)",
        )
    except Exception:
        logger.exception("Failed to write player %s", player_id)
        return server_error("Could not create player")

    return created(player)
