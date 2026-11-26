import json
import uuid

import pytest
from moto import mock_aws

from conftest import create_table
from common.ranks import get_rank_tier
from handlers import create_player


def _event(body):
    return {"body": json.dumps(body) if not isinstance(body, str) else body}


@mock_aws
def test_create_player_valid():
    table = create_table()
    create_player._table = None

    resp = create_player.lambda_handler(_event({"username": "TenZ", "region": "NA", "mmr": 2500}), None)

    assert resp["statusCode"] == 201
    body = json.loads(resp["body"])
    assert body["username"] == "TenZ"
    assert body["region"] == "NA"
    assert body["mmr"] == 2500
    assert body["rankTier"] == "Ascendant"
    assert body["createdAtUtc"].endswith("Z")
    uuid.UUID(body["playerId"])  # raises if not a UUID

    item = table.get_item(Key={"PK": f"PLAYER#{body['playerId']}", "SK": "PROFILE"})["Item"]
    assert item["username"] == "TenZ"
    assert item["region"] == "NA"
    assert item["mmr"] == 2500
    assert item["rankTier"] == "Ascendant"
    assert item["createdAtUtc"] == body["createdAtUtc"]


@mock_aws
def test_create_player_defaults_mmr_to_1000():
    create_table()
    create_player._table = None

    resp = create_player.lambda_handler(_event({"username": "Aspas", "region": "EU"}), None)

    assert resp["statusCode"] == 201
    body = json.loads(resp["body"])
    assert body["mmr"] == 1000
    assert body["rankTier"] == get_rank_tier(1000)


@pytest.mark.parametrize(
    "payload, expected_fragment",
    [
        ({"username": "TenZ", "region": "SA", "mmr": 1000}, "region"),
        ({"username": "TenZ", "mmr": 1000}, "region"),
        ({"region": "NA", "mmr": 1000}, "username"),
        ({"username": "", "region": "NA"}, "username"),
        ({"username": "   ", "region": "NA"}, "username"),
        ({"username": "TenZ", "region": "NA", "mmr": -1}, "mmr"),
        ({"username": "TenZ", "region": "NA", "mmr": "1000"}, "mmr"),
        ({"username": "TenZ", "region": "NA", "mmr": 10.5}, "mmr"),
        ({"username": "TenZ", "region": "NA", "mmr": True}, "mmr"),
    ],
)
@mock_aws
def test_create_player_invalid_input_returns_400(payload, expected_fragment):
    table = create_table()
    create_player._table = None

    resp = create_player.lambda_handler(_event(payload), None)

    assert resp["statusCode"] == 400
    assert expected_fragment in json.loads(resp["body"])["error"]
    assert table.scan()["Count"] == 0  # nothing written


@pytest.mark.parametrize("raw", [None, "", "not json", "[1, 2]"])
@mock_aws
def test_create_player_bad_body_returns_400(raw):
    create_table()
    create_player._table = None

    resp = create_player.lambda_handler({"body": raw}, None)

    assert resp["statusCode"] == 400
    assert "error" in json.loads(resp["body"])


@pytest.mark.parametrize(
    "mmr, tier",
    [
        (0, "Iron"),
        (399, "Iron"),
        (400, "Bronze"),
        (800, "Silver"),
        (1200, "Gold"),
        (1600, "Platinum"),
        (2000, "Diamond"),
        (2400, "Ascendant"),
        (2800, "Immortal"),
        (3200, "Radiant"),
        (9999, "Radiant"),
    ],
)
def test_rank_tiers(mmr, tier):
    assert get_rank_tier(mmr) == tier
