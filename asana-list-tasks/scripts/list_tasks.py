#!/usr/bin/env python3
"""List Asana tasks for a project, section, tag, or assignee through the direct REST API."""

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


DEFAULT_FIELDS = "name,completed,permalink_url,assignee.name,due_on,memberships.section.name"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="List Asana tasks by project, section, tag, or assignee.")
    parser.add_argument("--project", help="List tasks in this project gid.")
    parser.add_argument("--section", help="List tasks in this section gid.")
    parser.add_argument("--tag", help="List tasks with this tag gid.")
    parser.add_argument("--assignee", help="List tasks assigned to this user (gid, email, or 'me'); requires --workspace.")
    parser.add_argument("--workspace", help="Workspace gid (required with --assignee).")
    parser.add_argument("--completed-since", help="Only return tasks completed since this ISO timestamp (with --assignee).")
    parser.add_argument("--fields", help="opt_fields override (comma-separated).")
    parser.add_argument("--limit", type=int, default=50, help="Maximum number of tasks to fetch (default 50).")
    parser.add_argument("--all", action="store_true", help="Fetch every page instead of a single limited page.")
    parser.add_argument("--env-file", help="Path to a .env file containing ASANA_ACCESS_TOKEN.")
    parser.add_argument("--json", action="store_true", help="Emit structured JSON.")
    return parser.parse_args()


def resolve_route(args: argparse.Namespace) -> tuple[str, dict[str, Any]]:
    selectors = [
        bool(args.project),
        bool(args.section),
        bool(args.tag),
        bool(args.assignee),
    ]
    chosen = sum(selectors)
    if chosen == 0:
        raise AsanaApiError(
            "bad_argument",
            "No selector provided. Pass exactly one of --project, --section, --tag, or --assignee.",
        )
    if chosen > 1:
        raise AsanaApiError(
            "bad_argument",
            "Multiple selectors provided. Pass exactly one of --project, --section, --tag, or --assignee.",
        )

    if args.project:
        return f"/projects/{args.project}/tasks", {}
    if args.section:
        return f"/sections/{args.section}/tasks", {}
    if args.tag:
        return f"/tags/{args.tag}/tasks", {}

    if not args.workspace:
        raise AsanaApiError(
            "bad_argument",
            "--assignee requires --workspace.",
        )
    params: dict[str, Any] = {"assignee": args.assignee, "workspace": args.workspace}
    if args.completed_since:
        params["completed_since"] = args.completed_since
    return "/tasks", params


def list_tasks(client: AsanaClient, args: argparse.Namespace) -> list[dict[str, Any]]:
    path, params = resolve_route(args)
    params = dict(params)
    params["opt_fields"] = args.fields or DEFAULT_FIELDS
    if args.all:
        return client.get_all(path, params=params)
    params["limit"] = args.limit
    return client.request("GET", path, params=params)


def emit_text_result(result: dict[str, Any]) -> None:
    print(f"count={result['count']}")
    for task in result["tasks"]:
        memberships = task.get("memberships") or []
        section = (memberships[0].get("section") if memberships else None) or {}
        assignee = (task.get("assignee") or {}).get("name") or "-"
        print(
            f"task={task.get('gid')} completed={str(task.get('completed')).lower()} "
            f"section={section.get('name') or '-'} assignee={assignee} "
            f"due_on={task.get('due_on') or '-'} name={task.get('name')}"
        )


def main() -> int:
    args = parse_args()
    try:
        client = AsanaClient(resolve_token(args.env_file))
        tasks = list_tasks(client, args)
    except AsanaApiError as exc:
        payload = {
            "schema_version": "asana-list-tasks.error.v1",
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
        "schema_version": "asana-list-tasks.v1",
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
