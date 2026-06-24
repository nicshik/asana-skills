#!/usr/bin/env python3
"""Update one Asana task through the direct REST API."""

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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Update one Asana task by gid or task URL.")
    parser.add_argument("task", help="Asana task gid or task URL.")
    parser.add_argument("--name", help="New task name.")
    notes = parser.add_mutually_exclusive_group()
    notes.add_argument("--notes", help="New plain-text notes.")
    notes.add_argument("--notes-file", help="Path to a file with plain-text notes.")
    notes.add_argument("--html-notes-file", help="Path to a file with HTML notes (html_notes).")
    completed = parser.add_mutually_exclusive_group()
    completed.add_argument("--completed", action="store_true", help="Mark the task completed.")
    completed.add_argument("--incomplete", action="store_true", help="Mark the task incomplete.")
    parser.add_argument("--due-on", help="Due date (YYYY-MM-DD).")
    parser.add_argument("--due-at", help="Due timestamp (ISO 8601).")
    parser.add_argument("--assignee", help="Assignee gid, email, or 'me'.")
    parser.add_argument("--add-tag", action="append", default=[], metavar="GID", help="Tag gid to add (repeatable).")
    parser.add_argument(
        "--remove-tag", action="append", default=[], metavar="GID", help="Tag gid to remove (repeatable)."
    )
    parser.add_argument("--to-section", metavar="GID", help="Section gid to move the task into.")
    parser.add_argument("--data-file", help="Path to a JSON file whose object is merged into the update data.")
    parser.add_argument("--dry-run", action="store_true", help="Plan the update without calling the API.")
    parser.add_argument("--env-file", help="Path to a .env file containing ASANA_ACCESS_TOKEN.")
    parser.add_argument("--json", action="store_true", help="Emit structured JSON.")
    return parser.parse_args()


def _read_text_file(path: str) -> str:
    try:
        return Path(path).expanduser().read_text(encoding="utf-8")
    except OSError as exc:
        raise AsanaApiError("bad_argument", f"Could not read file '{path}': {exc}") from exc


def _load_data_file(path: str) -> dict[str, Any]:
    try:
        raw = Path(path).expanduser().read_text(encoding="utf-8")
    except OSError as exc:
        raise AsanaApiError("bad_argument", f"Could not read --data-file '{path}': {exc}") from exc
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AsanaApiError("bad_argument", f"--data-file '{path}' is not valid JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise AsanaApiError("bad_argument", f"--data-file '{path}' must contain a JSON object.")
    return parsed


def build_data(args: argparse.Namespace) -> dict[str, Any]:
    data: dict[str, Any] = {}
    if args.name is not None:
        data["name"] = args.name
    if args.notes is not None:
        data["notes"] = args.notes
    elif args.notes_file is not None:
        data["notes"] = _read_text_file(args.notes_file)
    elif args.html_notes_file is not None:
        data["html_notes"] = _read_text_file(args.html_notes_file)
    if args.completed:
        data["completed"] = True
    elif args.incomplete:
        data["completed"] = False
    if args.due_on is not None:
        data["due_on"] = args.due_on
    if args.due_at is not None:
        data["due_at"] = args.due_at
    if args.assignee is not None:
        data["assignee"] = args.assignee
    if args.data_file is not None:
        data.update(_load_data_file(args.data_file))
    return data


def update_task(client: AsanaClient, args: argparse.Namespace) -> dict[str, Any]:
    reference = parse_task_reference(args.task)
    if reference.input_kind in ("empty", "raw", "url_without_gid"):
        raise AsanaApiError(
            "not_found",
            f"Task reference '{args.task}' does not contain a numeric task gid.",
            task_not_found_details(reference),
        )

    data = build_data(args)
    add_tags = list(args.add_tag)
    remove_tags = list(args.remove_tag)
    to_section = args.to_section

    if not data and not add_tags and not remove_tags and not to_section:
        raise AsanaApiError(
            "bad_argument",
            "No changes requested. Provide a field flag, a tag operation, or --to-section.",
        )

    applied: dict[str, Any] = {
        "fields": data,
        "add_tags": add_tags,
        "remove_tags": remove_tags,
        "to_section": to_section,
    }

    if args.dry_run:
        return {"action": "dry_run", "gid": reference.lookup, "name": data.get("name"), "applied": applied}

    task: dict[str, Any] = {}
    try:
        if data:
            task = client.request(
                "PUT",
                f"/tasks/{reference.lookup}",
                params={"opt_fields": "name,completed"},
                data=data,
            )
        for tag in add_tags:
            client.request("POST", f"/tasks/{reference.lookup}/addTag", data={"tag": tag})
        for tag in remove_tags:
            client.request("POST", f"/tasks/{reference.lookup}/removeTag", data={"tag": tag})
        if to_section:
            client.request("POST", f"/sections/{to_section}/addTask", data={"task": reference.lookup})
    except AsanaApiError as exc:
        if exc.category == "not_found" or is_task_entity_not_found_message(exc.message):
            raise AsanaApiError(
                "not_found",
                f"Task '{reference.lookup}' was not found.",
                task_not_found_details(reference),
            ) from exc
        raise

    name = (task or {}).get("name") or data.get("name")
    return {"action": "updated", "gid": reference.lookup, "name": name, "applied": applied}


def emit_text_result(result: dict[str, Any]) -> None:
    applied = result.get("applied") or {}
    fields = applied.get("fields") or {}
    print(f"action={result.get('action')} gid={result.get('gid')}")
    print(f"name={result.get('name') or '-'}")
    print(f"fields={', '.join(sorted(fields)) or '-'}")
    print(f"add_tags={', '.join(applied.get('add_tags') or []) or '-'}")
    print(f"remove_tags={', '.join(applied.get('remove_tags') or []) or '-'}")
    print(f"to_section={applied.get('to_section') or '-'}")


def main() -> int:
    args = parse_args()
    try:
        client = AsanaClient(resolve_token(args.env_file))
        result = update_task(client, args)
    except AsanaApiError as exc:
        payload = {
            "schema_version": "asana-update-task.error.v1",
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
        "schema_version": "asana-update-task.v1",
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
