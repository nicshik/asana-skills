#!/usr/bin/env python3
"""Delete one Asana task through the direct REST API, with a confirm guard."""

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


BEFORE_FIELDS = "name,completed,permalink_url"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Delete one Asana task by gid or task URL.")
    parser.add_argument("task", help="Asana task gid or task URL.")
    parser.add_argument("--confirm", help="Resolved task gid; must match for a live delete.")
    parser.add_argument("--dry-run", action="store_true", help="Read the task and report what would be deleted without deleting.")
    parser.add_argument("--env-file", help="Path to a .env file containing ASANA_ACCESS_TOKEN.")
    parser.add_argument("--json", action="store_true", help="Emit structured JSON.")
    return parser.parse_args()


def delete_task(client: AsanaClient, task_ref: str, confirm: str | None, dry_run: bool) -> dict[str, Any]:
    reference = parse_task_reference(task_ref)
    if reference.input_kind in ("empty", "raw", "url_without_gid"):
        raise AsanaApiError(
            "not_found",
            f"Task reference '{task_ref}' does not contain a numeric task gid.",
            task_not_found_details(reference),
        )

    gid = reference.lookup
    try:
        before = client.request("GET", f"/tasks/{gid}", params={"opt_fields": BEFORE_FIELDS})
    except AsanaApiError as exc:
        if exc.category == "not_found" or is_task_entity_not_found_message(exc.message):
            raise AsanaApiError(
                "not_found",
                f"Task '{gid}' was not found.",
                task_not_found_details(reference),
            ) from exc
        raise

    if dry_run:
        return {"action": "dry_run", "before": before, "verification_status": "dry_run"}

    if confirm != gid:
        raise AsanaApiError(
            "not_confirmed",
            f"delete requires --confirm {gid}",
            {"gid": gid},
        )

    client.request("DELETE", f"/tasks/{gid}")

    verification_status = "read_back"
    try:
        client.request("GET", f"/tasks/{gid}", params={"opt_fields": BEFORE_FIELDS})
    except AsanaApiError as exc:
        if exc.category == "not_found" or is_task_entity_not_found_message(exc.message):
            verification_status = "not_found_after_delete"
        else:
            raise

    return {"action": "deleted", "before": before, "verification_status": verification_status}


def emit_text_result(result: dict[str, Any]) -> None:
    task = result["before"]
    print(f"action={result['action']} verification_status={result['verification_status']}")
    print(f"task={task.get('gid')} completed={str(task.get('completed')).lower()}")
    print(f"name={task.get('name')}")
    if task.get("permalink_url"):
        print(f"permalink_url={task.get('permalink_url')}")


def main() -> int:
    args = parse_args()
    try:
        client = AsanaClient(resolve_token(args.env_file))
        outcome = delete_task(client, args.task, confirm=args.confirm, dry_run=args.dry_run)
    except AsanaApiError as exc:
        payload = {
            "schema_version": "asana-delete-task.error.v1",
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
        "schema_version": "asana-delete-task.v1",
        "fetched_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "action": outcome["action"],
        "before": outcome["before"],
        "verification_status": outcome["verification_status"],
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        emit_text_result(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
