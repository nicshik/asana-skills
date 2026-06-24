#!/usr/bin/env python3
"""List the tags in an Asana workspace through the direct REST API."""

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


DEFAULT_FIELDS = "name,color"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="List the tags in an Asana workspace.")
    parser.add_argument("--workspace", required=True, help="Workspace gid whose tags are listed.")
    parser.add_argument("--fields", help="opt_fields override (comma-separated).")
    parser.add_argument("--env-file", help="Path to a .env file containing ASANA_ACCESS_TOKEN.")
    parser.add_argument("--json", action="store_true", help="Emit structured JSON.")
    return parser.parse_args()


def list_tags(client: AsanaClient, workspace: str, fields: str | None) -> list[dict[str, Any]]:
    return client.get_all(
        f"/workspaces/{workspace}/tags",
        params={"opt_fields": fields or DEFAULT_FIELDS},
    )


def emit_text_result(result: dict[str, Any]) -> None:
    print(f"tags={result['count']}")
    for tag in result["tags"]:
        print(f"{tag.get('gid')} {tag.get('name') or '-'} color={tag.get('color') or '-'}")


def main() -> int:
    args = parse_args()
    try:
        client = AsanaClient(resolve_token(args.env_file))
        tags = list_tags(client, args.workspace, fields=args.fields)
    except AsanaApiError as exc:
        payload = {
            "schema_version": "asana-list-tags.error.v1",
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
        "schema_version": "asana-list-tags.v1",
        "fetched_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "count": len(tags),
        "tags": tags,
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        emit_text_result(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
