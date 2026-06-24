#!/usr/bin/env python3
"""Add a comment story to one Asana task through the direct REST API."""

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
    parser = argparse.ArgumentParser(description="Add a comment to one Asana task by gid or task URL.")
    parser.add_argument("task", help="Asana task gid or task URL.")
    parser.add_argument("--text", help="Comment text to post.")
    parser.add_argument("--text-file", help="Path to a file whose contents are posted as the comment text.")
    parser.add_argument("--dry-run", action="store_true", help="Validate inputs without calling the Asana API.")
    parser.add_argument("--env-file", help="Path to a .env file containing ASANA_ACCESS_TOKEN.")
    parser.add_argument("--json", action="store_true", help="Emit structured JSON.")
    args = parser.parse_args()
    if bool(args.text is not None) == bool(args.text_file is not None):
        parser.error("exactly one of --text or --text-file is required")
    return args


def resolve_text(args: argparse.Namespace) -> str:
    if args.text is not None:
        return args.text
    try:
        return Path(args.text_file).expanduser().read_text(encoding="utf-8")
    except OSError as exc:
        raise AsanaApiError("not_found", f"Comment text file cannot be read: {args.text_file}") from exc


def comment_task(client: AsanaClient, task_ref: str, text: str, dry_run: bool) -> dict[str, Any]:
    reference = parse_task_reference(task_ref)
    if reference.input_kind in ("empty", "raw", "url_without_gid"):
        raise AsanaApiError(
            "not_found",
            f"Task reference '{task_ref}' does not contain a numeric task gid.",
            task_not_found_details(reference),
        )

    if dry_run:
        return {"action": "dry_run", "task": reference.lookup, "text_length": len(text)}

    try:
        story = client.request("POST", f"/tasks/{reference.lookup}/stories", data={"text": text})
    except AsanaApiError as exc:
        if exc.category == "not_found" or is_task_entity_not_found_message(exc.message):
            raise AsanaApiError(
                "not_found",
                f"Task '{reference.lookup}' was not found.",
                task_not_found_details(reference),
            ) from exc
        raise

    return {"action": "commented", "task": reference.lookup, "story_gid": (story or {}).get("gid")}


def emit_text_result(result: dict[str, Any]) -> None:
    print(f"action={result['action']} task={result['task']}")
    if result["action"] == "dry_run":
        print(f"text_length={result['text_length']}")
    else:
        print(f"story_gid={result.get('story_gid') or '-'}")


def main() -> int:
    args = parse_args()
    try:
        client = AsanaClient(resolve_token(args.env_file))
        text = resolve_text(args)
        result = comment_task(client, args.task, text, dry_run=args.dry_run)
    except AsanaApiError as exc:
        payload = {
            "schema_version": "asana-comment-task.error.v1",
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

    result["schema_version"] = "asana-comment-task.v1"
    result["fetched_at"] = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        emit_text_result(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
