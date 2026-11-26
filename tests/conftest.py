import os
import sys
from pathlib import Path

import boto3
import pytest

# Lambda runs with src/ as the code root, so mirror that for imports.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

TABLE_NAME = "MatchmakerTable-test"


@pytest.fixture(autouse=True)
def aws_env(monkeypatch):
    """Fake credentials so nothing can ever reach a real AWS account."""
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_SECURITY_TOKEN", "testing")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    monkeypatch.setenv("TABLE_NAME", TABLE_NAME)


def create_table():
    """Create the table and LeaderboardIndex exactly as template.yaml defines them."""
    dynamodb = boto3.resource("dynamodb")
    return dynamodb.create_table(
        TableName=TABLE_NAME,
        BillingMode="PAY_PER_REQUEST",
        AttributeDefinitions=[
            {"AttributeName": "PK", "AttributeType": "S"},
            {"AttributeName": "SK", "AttributeType": "S"},
            {"AttributeName": "region", "AttributeType": "S"},
            {"AttributeName": "mmr", "AttributeType": "N"},
        ],
        KeySchema=[
            {"AttributeName": "PK", "KeyType": "HASH"},
            {"AttributeName": "SK", "KeyType": "RANGE"},
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "LeaderboardIndex",
                "KeySchema": [
                    {"AttributeName": "region", "KeyType": "HASH"},
                    {"AttributeName": "mmr", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            }
        ],
    )

