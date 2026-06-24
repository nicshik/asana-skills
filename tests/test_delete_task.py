#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "asana-delete-task" / "scripts" / "delete_task.py"
SPEC = importlib.util.spec_from_file_location("delete_task", SCRIPT)
assert SPEC and SPEC.loader
delete_task = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = delete_task
SPEC.loader.exec_module(delete_task)


class FakeClient:
    def __init__(self, task_exists: bool = True) -> None:
        self.calls: list[tuple[str, str]] = []
        self.task_exists = task_exists
        self.deleted = False

    def request(self, method, path, params=None, data=None, wrap=True, full=False):
        self.calls.append((method, path))
        if method == "DELETE":
            self.deleted = True
            return {}
        # GET
        if self.deleted or not self.task_exists:
            raise delete_task.AsanaApiError("not_found", "Asana API HTTP 404: Not Found")
        return {
            "gid": "1200000000000000",
            "name": "Fixture task",
            "completed": False,
            "permalink_url": "https://app.asana.com/0/1200000000000001/1200000000000000",
        }

    def get_all(self, path, params=None, page_size=100):
        self.calls.append(("GET", path))
        return []


class DeleteTaskTest(unittest.TestCase):
    def test_confirm_mismatch_raises_not_confirmed_and_does_not_delete(self) -> None:
        client = FakeClient()
        with self.assertRaises(delete_task.AsanaApiError) as error:
            delete_task.delete_task(client, "1200000000000000", confirm="1200000000000099", dry_run=False)
        self.assertEqual(error.exception.category, "not_confirmed")
        self.assertEqual(error.exception.details["gid"], "1200000000000000")
        self.assertFalse(client.deleted)
        self.assertNotIn(("DELETE", "/tasks/1200000000000000"), client.calls)

    def test_dry_run_reads_but_does_not_delete(self) -> None:
        client = FakeClient()
        outcome = delete_task.delete_task(client, "1200000000000000", confirm=None, dry_run=True)
        self.assertEqual(outcome["action"], "dry_run")
        self.assertEqual(outcome["verification_status"], "dry_run")
        self.assertEqual(outcome["before"]["gid"], "1200000000000000")
        self.assertFalse(client.deleted)
        self.assertTrue(all(method == "GET" for method, _ in client.calls))

    def test_live_delete_then_read_back_is_not_found_after_delete(self) -> None:
        client = FakeClient()
        outcome = delete_task.delete_task(client, "1200000000000000", confirm="1200000000000000", dry_run=False)
        self.assertEqual(outcome["action"], "deleted")
        self.assertEqual(outcome["verification_status"], "not_found_after_delete")
        self.assertTrue(client.deleted)
        self.assertIn(("DELETE", "/tasks/1200000000000000"), client.calls)

    def test_reference_without_gid_is_not_found(self) -> None:
        client = FakeClient()
        with self.assertRaises(delete_task.AsanaApiError) as error:
            delete_task.delete_task(client, "https://app.asana.com/home", confirm=None, dry_run=True)
        self.assertEqual(error.exception.category, "not_found")
        self.assertEqual(error.exception.details["error_code"], "task_not_found")
        self.assertEqual(error.exception.details["input_kind"], "url_without_gid")
        self.assertEqual(client.calls, [])

    def test_api_not_found_maps_to_task_not_found(self) -> None:
        client = FakeClient(task_exists=False)
        with self.assertRaises(delete_task.AsanaApiError) as error:
            delete_task.delete_task(client, "1200000000000000", confirm=None, dry_run=True)
        self.assertEqual(error.exception.category, "not_found")
        self.assertEqual(error.exception.details["error_code"], "task_not_found")
        self.assertEqual(error.exception.details["input_kind"], "gid")


if __name__ == "__main__":
    unittest.main()
