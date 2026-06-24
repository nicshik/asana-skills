#!/usr/bin/env python3
"""Generic passthrough to the Asana REST API for arbitrary method/path calls."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from asana_common.rest import AsanaApiError, AsanaClient, resolve_token


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Call an arbitrary Asana REST API endpoint by HTTP method and path.",
    )
    parser.add_argument("method", help="HTTP method: GET, POST, PUT, or DELETE.")
    parser.add_argument("path", help="API path, e.g. /tasks/1200000000000000 or projects/1200000000000001.")
    parser.add_argument(
        "--query",
        action="append",
        default=[],
        metavar="k=v",
        help="Query parameter as key=value (repeatable).",
    )
    parser.add_argument(
        "--field",
        action="append",
        default=[],
        metavar="k=v",
        help="Body field as key=value (repeatable); each value is sent as a string.",
    )
    parser.add_argument("--data-file", help="Path to a JSON file used as the request body.")
    parser.add_argument("--opt-fields", help="opt_fields query parameter (comma-separated).")
    parser.add_argument("--all", action="store_true", help="GET only: follow pagination and return all rows.")
    parser.add_argument("--env-file", help="Path to a .env file containing ASANA_ACCESS_TOKEN.")
    parser.add_argument("--json", action="store_true", help="Emit structured JSON.")
    return parser.parse_args()


def split_kv(item: str) -> tuple[str, str]:
    if "=" not in item:
        raise AsanaApiError(
            "bad_argument",
            f"Expected key=value but got '{item}'.",
            {"error_code": "bad_argument", "value": item},
        )
    key, value = item.split("=", 1)
    return key.strip(), value


def build_params(query: list[str], opt_fields: str | None) -> dict[str, Any]:
    params: dict[str, Any] = {}
    for item in query:
        key, value = split_kv(item)
        params[key] = value
    if opt_fields:
        params["opt_fields"] = opt_fields
    return params


def load_data(data_file: str | None, fields: list[str]) -> tuple[Any, bool]:
    """Return (data, wrap). --data-file wins over --field when both are given."""
    if data_file:
        try:
            text = Path(data_file).expanduser().read_text(encoding="utf-8")
        except OSError as exc:
            raise AsanaApiError(
                "bad_argument",
                f"Could not read --data-file '{data_file}': {exc}.",
                {"error_code": "bad_argument", "data_file": data_file},
            ) from exc
        try:
            loaded = json.loads(text) if text.strip() else None
        except json.JSONDecodeError as exc:
            raise AsanaApiError(
                "bad_argument",
                f"--data-file '{data_file}' is not valid JSON: {exc}.",
                {"error_code": "bad_argument", "data_file": data_file},
            ) from exc
        if isinstance(loaded, dict) and "data" in loaded:
            return loaded, False
        return loaded, True

    if fields:
        data: dict[str, str] = {}
        for item in fields:
            key, value = split_kv(item)
            data[key] = value
        return data, True

    return None, True


def call_api(client: AsanaClient, args: argparse.Namespace) -> dict[str, Any]:
    method = args.method.upper()
    params = build_params(args.query, args.opt_fields)
    data, wrap = load_data(args.data_file, args.field)

    if args.all and method == "GET":
        return {"data": client.get_all(args.path, params=params)}

    return {"data": client.request(method, args.path, params=params, data=data, wrap=wrap)}


def emit_text_result(result: dict[str, Any]) -> None:
    data = result["data"]
    if isinstance(data, list):
        print(f"rows={len(data)}")
    elif isinstance(data, dict):
        print(f"gid={data.get('gid') or '-'}")
        if data.get("name") is not None:
            print(f"name={data.get('name')}")
    else:
        print(f"data={data}")


def main() -> int:
    args = parse_args()
    try:
        client = AsanaClient(resolve_token(args.env_file))
        result = call_api(client, args)
    except AsanaApiError as exc:
        payload = {
            "schema_version": "asana-api.error.v1",
            "error_category": exc.category,
            "error": exc.message,
        }
        payload.update(exc.details)
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2), file=sys.stderr)
        else:
            print(f"error_category={exc.category}", file=sys.stderr)
            print(exc.message, file=sys.stderr)
        return 1

    result = {
        "schema_version": "asana-api.v1",
        "fetched_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        **result,
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        emit_text_result(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
