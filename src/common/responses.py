"""JSON response helpers for API Gateway HTTP API (payload v2.0) Lambda handlers."""

import json
from decimal import Decimal
from typing import Any


class DecimalEncoder(json.JSONEncoder):
    """Serialize DynamoDB Decimal values as int when whole, otherwise float."""

    def default(self, o: Any) -> Any:
        if isinstance(o, Decimal):
            return int(o) if o == o.to_integral_value() else float(o)
        return super().default(o)


def build_response(status_code: int, body: Any) -> dict:
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body, cls=DecimalEncoder),
    }


def ok(body: Any) -> dict:
    return build_response(200, body)


def created(body: Any) -> dict:
    return build_response(201, body)


def bad_request(message: str) -> dict:
    return build_response(400, {"error": message})


def server_error(message: str = "Internal server error") -> dict:
    return build_response(500, {"error": message})
