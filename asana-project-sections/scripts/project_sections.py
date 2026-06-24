#!/usr/bin/env python3
"""List or create Asana project sections through the direct REST API."""

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
    parser = argparse.ArgumentParser(description="List Asana project sections, or create one.")
    parser.add_argument("--project", required=True, help="Asana project gid.")
    parser.add_argument("--create", metavar="NAME", help="Create a section with this name instead of listing.")
    parser.add_argument("--dry-run", action="store_true", help="With --create, do not write; report the planned section.")
    parser.add_argument("--env-file", help="Path to a .env file containing ASANA_ACCESS_TOKEN.")
    parser.add_argument("--json", action="store_true", help="Emit structured JSON.")
    return parser.parse_args()


def list_sections(client: AsanaClient, project: str) -> dict[str, Any]:
    sections = client.get_all(
        f"/projects/{project}/sections",
        params={"opt_fields": "name,created_at"},
    )
    return {"action": "list", "count": len(sections), "sections": sections}


def create_section(client: AsanaClient, project: str, name: str, dry_run: bool) -> dict[str, Any]:
    if dry_run:
        return {"action": "dry_run", "name": name}
    section = client.request("POST", f"/projects/{project}/sections", data={"name": name})
    return {"action": "created", "gid": section.get("gid"), "name": section.get("name")}


def emit_text_result(result: dict[str, Any]) -> None:
    action = result["action"]
    if action == "list":
        print(f"action=list count={result['count']}")
        for section in result["sections"]:
            print(f"section={section.get('gid')} name={section.get('name')}")
    elif action == "dry_run":
        print(f"action=dry_run name={result['name']}")
    else:
        print(f"action=created section={result.get('gid')} name={result.get('name')}")


def main() -> int:
    args = parse_args()
    try:
        client = AsanaClient(resolve_token(args.env_file))
        if args.create is not None:
            result = create_section(client, args.project, args.create, dry_run=args.dry_run)
        else:
            result = list_sections(client, args.project)
    except AsanaApiError as exc:
        payload = {
            "schema_version": "asana-project-sections.error.v1",
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
        "schema_version": "asana-project-sections.v1",
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
