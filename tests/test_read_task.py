#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "asana-read-task" / "scripts" / "read_task.py"
SPEC = importlib.util.spec_from_file_location("read_task", SCRIPT)
assert SPEC and SPEC.loader
read_task = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = read_task
SPEC.loader.exec_module(read_task)


class FakeClient:
    def __init__(self, task_exists: bool = True, entity_error: bool = False) -> None:
        self.calls: list[tuple[str, str]] = []
        self.task_exists = task_exists
        self.entity_error = entity_error

    def request(self, method, path, params=None, data=None, wrap=True, full=False):
        self.calls.append((method, path))
        if self.entity_error:
            raise read_task.AsanaApiError("not_found", "Asana API HTTP 404: Not Found: task")
        if not self.task_exists:
            raise read_task.AsanaApiError("not_found", "Asana API HTTP 404: Not Found")
        return {
            "gid": "1200000000000000",
            "name": "Fixture task",
            "completed": False,
            "assignee": {"name": "Example User"},
            "memberships": [{"project": {"name": "Example Project"}, "section": {"name": "Doing"}}],
            "tags": [{"name": "Example"}],
            "due_on": "2026-07-01",
        }

    def get_all(self, path, params=None, page_size=100):
        self.calls.append(("GET", path))
        return []


class ReadTaskTest(unittest.TestCase):
    def test_url_lookup_extracts_gid(self) -> None:
        task = read_task.parse_task_reference("https://app.asana.com/0/1200000000000001/1200000000000000")
        self.assertEqual(task.lookup, "1200000000000000")
        self.assertEqual(task.input_kind, "url_with_gid")

    def test_read_task_returns_payload_and_no_write(self) -> None:
        client = FakeClient()
        task = read_task.read_task(client, "1200000000000000", include_stories=True, fields=None)
        self.assertEqual(task["gid"], "1200000000000000")
        self.assertEqual(task["stories"], [])
        self.assertTrue(all(method == "GET" for method, _ in client.calls))

    def test_reference_without_gid_is_not_found(self) -> None:
        client = FakeClient()
        with self.assertRaises(read_task.AsanaApiError) as error:
            read_task.read_task(client, "https://app.asana.com/home", include_stories=False, fields=None)
        self.assertEqual(error.exception.category, "not_found")
        self.assertEqual(error.exception.details["error_code"], "task_not_found")
        self.assertEqual(error.exception.details["input_kind"], "url_without_gid")
        self.assertEqual(client.calls, [])

    def test_api_not_found_maps_to_task_not_found(self) -> None:
        client = FakeClient(task_exists=False)
        with self.assertRaises(read_task.AsanaApiError) as error:
            read_task.read_task(client, "1200000000000000", include_stories=False, fields=None)
        self.assertEqual(error.exception.category, "not_found")
        self.assertEqual(error.exception.details["error_code"], "task_not_found")
        self.assertEqual(error.exception.details["input_kind"], "gid")


if __name__ == "__main__":
    unittest.main()
