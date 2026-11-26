import json

from moto import mock_aws

from conftest import create_table
from handlers import create_player, get_leaderboard


def _reset_clients():
    create_player._table = None
    get_leaderboard._table = None


def _add_player(username, region, mmr):
    resp = create_player.lambda_handler(
        {"body": json.dumps({"username": username, "region": region, "mmr": mmr})}, None
    )
    assert resp["statusCode"] == 201
    return json.loads(resp["body"])


def _get(params):
    resp = get_leaderboard.lambda_handler({"queryStringParameters": params}, None)
    return resp["statusCode"], json.loads(resp["body"])


@mock_aws
def test_leaderboard_orders_by_mmr_descending():
    create_table()
    _reset_clients()
    _add_player("Low", "NA", 500)
    _add_player("Top", "NA", 3500)
    _add_player("Mid", "NA", 1800)

    status, body = _get({"region": "NA"})

    assert status == 200
    assert body["region"] == "NA"
    assert body["count"] == 3
    assert [p["username"] for p in body["leaderboard"]] == ["Top", "Mid", "Low"]
    assert [p["rank"] for p in body["leaderboard"]] == [1, 2, 3]
    assert [p["mmr"] for p in body["leaderboard"]] == [3500, 1800, 500]
    assert body["leaderboard"][0]["rankTier"] == "Radiant"


@mock_aws
def test_leaderboard_region_isolation():
    create_table()
    _reset_clients()
    _add_player("NaPlayer", "NA", 1000)
    _add_player("EuPlayer1", "EU", 3000)
    _add_player("EuPlayer2", "EU", 2000)

    status, body = _get({"region": "NA"})

    assert status == 200
    assert body["count"] == 1
    assert [p["username"] for p in body["leaderboard"]] == ["NaPlayer"]


@mock_aws
def test_leaderboard_limit_enforced():
    create_table()
    _reset_clients()
    for i in range(10):
        _add_player(f"P{i}", "AP", 100 * i)

    status, body = _get({"region": "AP", "limit": "3"})

    assert status == 200
    assert body["count"] == 3
    assert [p["mmr"] for p in body["leaderboard"]] == [900, 800, 700]


@mock_aws
def test_leaderboard_default_limit_is_20():
    create_table()
    _reset_clients()
    for i in range(25):
        _add_player(f"P{i}", "NA", i)

    status, body = _get({"region": "NA"})

    assert status == 200
    assert body["count"] == 20
    assert body["leaderboard"][0]["mmr"] == 24


@mock_aws
def test_leaderboard_limit_capped_at_100():
    create_table()
    _reset_clients()
    for i in range(105):
        _add_player(f"P{i}", "EU", i)

    status, body = _get({"region": "EU", "limit": "500"})

    assert status == 200
    assert body["count"] == 100


@mock_aws
def test_leaderboard_empty_region():
    create_table()
    _reset_clients()

    status, body = _get({"region": "EU"})

    assert status == 200
    assert body == {"region": "EU", "count": 0, "leaderboard": []}


@mock_aws
def test_leaderboard_invalid_params_return_400():
    create_table()
    _reset_clients()

    for params in [None, {}, {"region": "SA"}, {"region": "NA", "limit": "abc"}, {"region": "NA", "limit": "0"}]:
        status, body = _get(params)
        assert status == 400, params
        assert "error" in body


@mock_aws
def test_leaderboard_uses_query_not_scan(monkeypatch):
    table = create_table()
    _reset_clients()
    _add_player("A", "NA", 100)

    calls = []
    real_table = get_leaderboard._get_table()
    monkeypatch.setattr(real_table, "scan", lambda *a, **k: calls.append("scan"))
    original_query = real_table.query

    def spy_query(**kwargs):
        calls.append(kwargs)
        return original_query(**kwargs)

    monkeypatch.setattr(real_table, "query", spy_query)

    status, _ = _get({"region": "NA"})

    assert status == 200
    assert "scan" not in calls
    assert calls[0]["IndexName"] == "LeaderboardIndex"
    assert calls[0]["ScanIndexForward"] is False
    assert calls[0]["Limit"] == 20
