#!/usr/bin/env python3
"""List Asana projects in a workspace or team through the direct REST API."""

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


DEFAULT_FIELDS = "name,archived,permalink_url"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="List Asana projects in a workspace or team.")
    scope = parser.add_mutually_exclusive_group(required=True)
    scope.add_argument("--workspace", help="Workspace gid to list projects from.")
    scope.add_argument("--team", help="Team gid to list projects from.")
    parser.add_argument(
        "--archived",
        choices=("true", "false"),
        help="Filter by archived state (true or false).",
    )
    parser.add_argument("--fields", help="opt_fields override (comma-separated).")
    parser.add_argument("--env-file", help="Path to a .env file containing ASANA_ACCESS_TOKEN.")
    parser.add_argument("--json", action="store_true", help="Emit structured JSON.")
    return parser.parse_args()


def list_projects(
    client: AsanaClient,
    workspace: str | None,
    team: str | None,
    archived: str | None,
    fields: str | None,
) -> list[dict[str, Any]]:
    params: dict[str, Any] = {"opt_fields": fields or DEFAULT_FIELDS}
    if archived is not None:
        params["archived"] = archived
    if team:
        path = f"/teams/{team}/projects"
    else:
        path = f"/workspaces/{workspace}/projects"
    return client.get_all(path, params=params)


def emit_text_result(result: dict[str, Any]) -> None:
    print(f"count={result['count']}")
    for project in result["projects"]:
        archived = str(project.get("archived")).lower()
        print(f"project={project.get('gid')} archived={archived} name={project.get('name')}")


def main() -> int:
    args = parse_args()
    try:
        client = AsanaClient(resolve_token(args.env_file))
        projects = list_projects(client, args.workspace, args.team, args.archived, args.fields)
    except AsanaApiError as exc:
        payload = {
            "schema_version": "asana-list-projects.error.v1",
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
        "schema_version": "asana-list-projects.v1",
        "fetched_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "count": len(projects),
        "projects": projects,
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        emit_text_result(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
