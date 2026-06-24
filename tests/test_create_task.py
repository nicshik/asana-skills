#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import sys
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "asana-create-task" / "scripts" / "create_task.py"
SPEC = importlib.util.spec_from_file_location("create_task", SCRIPT)
assert SPEC and SPEC.loader
create_task = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = create_task
SPEC.loader.exec_module(create_task)


class FakeClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict, object]] = []

    def request(self, method, path, params=None, data=None, wrap=True, full=False):
        self.calls.append((method, path, params or {}, data))
        return {
            "gid": "1200000000000000",
            "name": data.get("name") if isinstance(data, dict) else "Example task",
            "permalink_url": "https://app.asana.com/0/1200000000000001/1200000000000000",
        }


def make_args(**overrides) -> argparse.Namespace:
    base = dict(
        name="Example task",
        project=None,
        workspace=None,
        notes=None,
        notes_file=None,
        html_notes_file=None,
        section=None,
        parent=None,
        assignee=None,
        tags=None,
        due_on=None,
        due_at=None,
        dry_run=False,
        env_file=None,
        json=False,
    )
    base.update(overrides)
    return argparse.Namespace(**base)


class CreateTaskTest(unittest.TestCase):
    def test_build_payload_project_and_memberships_and_tags(self) -> None:
        args = make_args(
            project="1200000000000000",
            section="1200000000000001",
            tags="1200000000000000, 1200000000000001",
            notes="Body text",
            assignee="1200000000000000",
            due_on="2026-07-01",
        )
        payload = create_task.build_payload(args)
        self.assertEqual(payload["name"], "Example task")
        self.assertEqual(payload["projects"], ["1200000000000000"])
        self.assertEqual(
            payload["memberships"],
            [{"project": "1200000000000000", "section": "1200000000000001"}],
        )
        self.assertEqual(payload["tags"], ["1200000000000000", "1200000000000001"])
        self.assertEqual(payload["notes"], "Body text")
        self.assertEqual(payload["assignee"], "1200000000000000")
        self.assertEqual(payload["due_on"], "2026-07-01")
        self.assertNotIn("workspace", payload)

    def test_build_payload_workspace_only(self) -> None:
        args = make_args(workspace="1200000000000001")
        payload = create_task.build_payload(args)
        self.assertEqual(payload["workspace"], "1200000000000001")
        self.assertNotIn("projects", payload)

    def test_dry_run_redacts_notes_and_makes_no_call(self) -> None:
        client = FakeClient()
        args = make_args(project="1200000000000000", notes="Body text", dry_run=True)
        result = create_task.create_task(client, args)
        self.assertEqual(result["action"], "dry_run")
        self.assertEqual(result["payload"]["notes"], "<9 chars>")
        self.assertEqual(result["payload"]["projects"], ["1200000000000000"])
        self.assertEqual(client.calls, [])

    def test_dry_run_redacts_html_notes(self) -> None:
        client = FakeClient()
        args = make_args(workspace="1200000000000001", dry_run=True)
        args.html_notes = None
        # Simulate html notes content via build_payload path.
        payload = create_task.build_payload(args)
        payload["html_notes"] = "<body>hi</body>"
        redacted = create_task.redact_notes(payload)
        self.assertEqual(redacted["html_notes"], "<15 chars>")

    def test_create_task_posts_and_returns_created(self) -> None:
        client = FakeClient()
        args = make_args(project="1200000000000000")
        result = create_task.create_task(client, args)
        self.assertEqual(result["action"], "created")
        self.assertEqual(result["gid"], "1200000000000000")
        self.assertEqual(result["name"], "Example task")
        self.assertEqual(
            result["permalink_url"],
            "https://app.asana.com/0/1200000000000001/1200000000000000",
        )
        method, path, params, data = client.calls[0]
        self.assertEqual(method, "POST")
        self.assertEqual(path, "/tasks")
        self.assertEqual(params, {"opt_fields": "name,permalink_url"})
        self.assertEqual(data["projects"], ["1200000000000000"])


if __name__ == "__main__":
    unittest.main()
