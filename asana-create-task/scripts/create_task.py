#!/usr/bin/env python3
"""Create one Asana task through the direct REST API."""

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
    parser = argparse.ArgumentParser(description="Create one Asana task.")
    parser.add_argument("--name", required=True, help="Task name.")
    parser.add_argument("--project", help="Container project gid. Sets data.projects=[project].")
    parser.add_argument("--workspace", help="Container workspace gid. Used when no project is given.")
    parser.add_argument("--notes", help="Plain-text notes body.")
    parser.add_argument("--notes-file", help="Path to a UTF-8 file with plain-text notes.")
    parser.add_argument("--html-notes-file", help="Path to a UTF-8 file with HTML notes (html_notes).")
    parser.add_argument("--section", help="Section gid for placement. Requires --project.")
    parser.add_argument("--parent", help="Parent task gid.")
    parser.add_argument("--assignee", help="Assignee user gid.")
    parser.add_argument("--tags", help="Comma-separated tag gids, e.g. \"1200000000000000,1200000000000001\".")
    parser.add_argument("--due-on", help="Due date as YYYY-MM-DD.")
    parser.add_argument("--due-at", help="Due timestamp as ISO 8601.")
    parser.add_argument("--dry-run", action="store_true", help="Build the payload without calling the API.")
    parser.add_argument("--env-file", help="Path to a .env file containing ASANA_ACCESS_TOKEN.")
    parser.add_argument("--json", action="store_true", help="Emit structured JSON.")
    args = parser.parse_args()

    notes_sources = [args.notes is not None, bool(args.notes_file), bool(args.html_notes_file)]
    if sum(1 for present in notes_sources if present) > 1:
        parser.error("--notes, --notes-file, and --html-notes-file are mutually exclusive")
    if not args.project and not args.workspace:
        parser.error("at least one of --project or --workspace is required")
    if args.section and not args.project:
        parser.error("--section requires --project")
    return args


def read_text_file(path_value: str) -> str:
    path = Path(path_value).expanduser()
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise AsanaApiError("not_found", f"Notes file cannot be read: {path}") from exc


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    data: dict[str, Any] = {"name": args.name}

    if args.notes is not None:
        data["notes"] = args.notes
    elif args.notes_file:
        data["notes"] = read_text_file(args.notes_file)
    elif args.html_notes_file:
        data["html_notes"] = read_text_file(args.html_notes_file)

    if args.project:
        data["projects"] = [args.project]
    elif args.workspace:
        data["workspace"] = args.workspace

    if args.section:
        data["memberships"] = [{"project": args.project, "section": args.section}]

    if args.parent:
        data["parent"] = args.parent
    if args.assignee:
        data["assignee"] = args.assignee
    if args.tags:
        data["tags"] = [tag.strip() for tag in args.tags.split(",") if tag.strip()]
    if args.due_on:
        data["due_on"] = args.due_on
    if args.due_at:
        data["due_at"] = args.due_at

    return data


def redact_notes(data: dict[str, Any]) -> dict[str, Any]:
    redacted = dict(data)
    for key in ("notes", "html_notes"):
        if key in redacted:
            redacted[key] = f"<{len(redacted[key])} chars>"
    return redacted


def create_task(client: AsanaClient, args: argparse.Namespace) -> dict[str, Any]:
    data = build_payload(args)

    if args.dry_run:
        return {
            "action": "dry_run",
            "payload": redact_notes(data),
        }

    task = client.request(
        "POST",
        "/tasks",
        params={"opt_fields": "name,permalink_url"},
        data=data,
    )
    return {
        "action": "created",
        "gid": task.get("gid"),
        "name": task.get("name"),
        "permalink_url": task.get("permalink_url"),
    }


def emit_text_result(result: dict[str, Any]) -> None:
    if result["action"] == "dry_run":
        payload = result["payload"]
        container = payload.get("projects") or payload.get("workspace") or "-"
        print("action=dry_run")
        print(f"name={payload.get('name')}")
        print(f"container={container}")
        memberships = payload.get("memberships") or []
        if memberships:
            membership = memberships[0]
            print(f"section={membership.get('section')}")
        if payload.get("tags"):
            print(f"tags={','.join(payload['tags'])}")
        return
    print("action=created")
    print(f"gid={result.get('gid')}")
    print(f"name={result.get('name')}")
    print(f"permalink_url={result.get('permalink_url') or '-'}")


def main() -> int:
    args = parse_args()
    try:
        client = AsanaClient(resolve_token(args.env_file))
        result = create_task(client, args)
    except AsanaApiError as exc:
        payload = {
            "schema_version": "asana-create-task.error.v1",
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

    result["schema_version"] = "asana-create-task.v1"
    result["fetched_at"] = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        emit_text_result(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
