#!/usr/bin/env python3
"""Preflight check for Asana REST access: identify the token's user and workspaces."""

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


ME_FIELDS = "name,email,workspaces.name,workspaces.gid"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify Asana REST access and list the token's user and workspaces."
    )
    parser.add_argument("--env-file", help="Path to a .env file containing ASANA_ACCESS_TOKEN.")
    parser.add_argument("--json", action="store_true", help="Emit structured JSON.")
    return parser.parse_args()


def preflight(client: AsanaClient) -> dict[str, Any]:
    me = client.request("GET", "/users/me", params={"opt_fields": ME_FIELDS})
    workspaces = [
        {"gid": ws.get("gid"), "name": ws.get("name")}
        for ws in (me.get("workspaces") or [])
    ]
    return {
        "user": me.get("name"),
        "email": me.get("email"),
        "workspaces": workspaces,
    }


def emit_text_result(result: dict[str, Any]) -> None:
    workspaces = result.get("workspaces") or []
    print(f"user={result.get('user') or '-'}")
    print(f"email={result.get('email') or '-'}")
    print(f"workspaces={len(workspaces)}")
    for ws in workspaces:
        print(f"  {ws.get('gid')} {ws.get('name')}")


def main() -> int:
    args = parse_args()
    try:
        client = AsanaClient(resolve_token(args.env_file))
        info = preflight(client)
    except AsanaApiError as exc:
        payload = {
            "schema_version": "asana-preflight.error.v1",
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
        "schema_version": "asana-preflight.v1",
        "fetched_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "user": info["user"],
        "email": info["email"],
        "workspaces": info["workspaces"],
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        emit_text_result(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
