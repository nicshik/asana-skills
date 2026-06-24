#!/usr/bin/env python3
"""Read one Asana task through the direct REST API."""

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
from asana_common.refs import is_task_entity_not_found_message, parse_task_reference, task_not_found_details


DEFAULT_FIELDS = (
    "name,notes,permalink_url,completed,assignee.name,memberships.project.name,"
    "memberships.section.name,tags.name,due_on,created_at,modified_at,parent.name"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Read one Asana task by gid or task URL.")
    parser.add_argument("task", help="Asana task gid or task URL.")
    parser.add_argument("--env-file", help="Path to a .env file containing ASANA_ACCESS_TOKEN.")
    parser.add_argument("--fields", help="opt_fields override (comma-separated).")
    parser.add_argument("--include-stories", action="store_true", help="Include the task's stories (comments/history).")
    parser.add_argument("--json", action="store_true", help="Emit structured JSON.")
    return parser.parse_args()


def read_task(client: AsanaClient, task_ref: str, include_stories: bool, fields: str | None) -> dict[str, Any]:
    reference = parse_task_reference(task_ref)
    if reference.input_kind in ("empty", "raw", "url_without_gid"):
        raise AsanaApiError(
            "not_found",
            f"Task reference '{task_ref}' does not contain a numeric task gid.",
            task_not_found_details(reference),
        )

    try:
        task = client.request("GET", f"/tasks/{reference.lookup}", params={"opt_fields": fields or DEFAULT_FIELDS})
    except AsanaApiError as exc:
        if exc.category == "not_found" or is_task_entity_not_found_message(exc.message):
            raise AsanaApiError(
                "not_found",
                f"Task '{reference.lookup}' was not found.",
                task_not_found_details(reference),
            ) from exc
        raise

    if include_stories:
        task["stories"] = client.get_all(
            f"/tasks/{reference.lookup}/stories",
            params={"opt_fields": "text,created_at,created_by.name,type,resource_subtype"},
        )
    return task


def emit_text_result(result: dict[str, Any]) -> None:
    task = result["task"]
    memberships = task.get("memberships") or []
    project = (memberships[0].get("project") if memberships else None) or {}
    section = (memberships[0].get("section") if memberships else None) or {}
    tags = ", ".join(t.get("name") for t in (task.get("tags") or []) if t.get("name")) or "-"
    assignee = (task.get("assignee") or {}).get("name") or "-"
    print(f"task={task.get('gid')} completed={str(task.get('completed')).lower()}")
    print(f"name={task.get('name')}")
    print(f"project={project.get('name') or '-'} section={section.get('name') or '-'}")
    print(f"assignee={assignee} due_on={task.get('due_on') or '-'}")
    print(f"tags={tags}")
    if "stories" in task:
        print(f"stories={len(task['stories'])}")


def main() -> int:
    args = parse_args()
    try:
        client = AsanaClient(resolve_token(args.env_file))
        task = read_task(client, args.task, include_stories=args.include_stories, fields=args.fields)
    except AsanaApiError as exc:
        payload = {
            "schema_version": "asana-read-task.error.v1",
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
        "schema_version": "asana-read-task.v1",
        "fetched_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "task": task,
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        emit_text_result(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
