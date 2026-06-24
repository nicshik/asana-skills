#!/usr/bin/env python3
"""Search Asana tasks in a workspace through the direct REST API."""

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


DEFAULT_FIELDS = "name,permalink_url,completed,memberships.section.name"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Search Asana tasks in a workspace by text (premium feature).")
    parser.add_argument("--workspace", required=True, help="Workspace gid to search within.")
    parser.add_argument("--text", required=True, help="Full-text query to match against tasks.")
    parser.add_argument("--project", help="Limit results to tasks in this project gid (sets projects.any).")
    parser.add_argument("--limit", type=int, default=20, help="Maximum number of tasks to return (default 20).")
    parser.add_argument("--fields", help="opt_fields override (comma-separated).")
    parser.add_argument("--env-file", help="Path to a .env file containing ASANA_ACCESS_TOKEN.")
    parser.add_argument("--json", action="store_true", help="Emit structured JSON.")
    return parser.parse_args()


def search_tasks(
    client: AsanaClient,
    workspace: str,
    text: str,
    project: str | None,
    limit: int,
    fields: str | None,
) -> list[dict[str, Any]]:
    params: dict[str, Any] = {
        "text": text,
        "limit": limit,
        "opt_fields": fields or DEFAULT_FIELDS,
    }
    if project:
        params["projects.any"] = project
    tasks = client.request("GET", f"/workspaces/{workspace}/tasks/search", params=params)
    return tasks or []


def emit_text_result(result: dict[str, Any]) -> None:
    print(f"count={result['count']}")
    for task in result["tasks"]:
        memberships = task.get("memberships") or []
        section = (memberships[0].get("section") if memberships else None) or {}
        completed = str(task.get("completed")).lower()
        print(
            f"task={task.get('gid')} completed={completed} "
            f"section={section.get('name') or '-'} name={task.get('name')}"
        )


def main() -> int:
    args = parse_args()
    try:
        client = AsanaClient(resolve_token(args.env_file))
        tasks = search_tasks(
            client,
            workspace=args.workspace,
            text=args.text,
            project=args.project,
            limit=args.limit,
            fields=args.fields,
        )
    except AsanaApiError as exc:
        payload = {
            "schema_version": "asana-search-tasks.error.v1",
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
        "schema_version": "asana-search-tasks.v1",
        "fetched_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "count": len(tasks),
        "tasks": tasks,
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        emit_text_result(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
