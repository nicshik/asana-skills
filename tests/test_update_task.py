#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import sys
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "asana-update-task" / "scripts" / "update_task.py"
SPEC = importlib.util.spec_from_file_location("update_task", SCRIPT)
assert SPEC and SPEC.loader
update_task = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = update_task
SPEC.loader.exec_module(update_task)


def make_args(**overrides) -> argparse.Namespace:
    base = dict(
        task="1200000000000000",
        name=None,
        notes=None,
        notes_file=None,
        html_notes_file=None,
        completed=False,
        incomplete=False,
        due_on=None,
        due_at=None,
        assignee=None,
        add_tag=[],
        remove_tag=[],
        to_section=None,
        data_file=None,
        dry_run=False,
        env_file=None,
        json=False,
    )
    base.update(overrides)
    return argparse.Namespace(**base)


class FakeClient:
    def __init__(self, task_exists: bool = True, entity_error: bool = False) -> None:
        self.calls: list[tuple[str, str, dict]] = []
        self.task_exists = task_exists
        self.entity_error = entity_error

    def request(self, method, path, params=None, data=None, wrap=True, full=False):
        self.calls.append((method, path, data or {}))
        if self.entity_error:
            raise update_task.AsanaApiError("api_error", "Not Found: task")
        if not self.task_exists:
            raise update_task.AsanaApiError("not_found", "Asana API HTTP 404: Not Found")
        return {"gid": "1200000000000000", "name": data.get("name", "Fixture task"), "completed": True}


class UpdateTaskTest(unittest.TestCase):
    def test_url_lookup_extracts_gid(self) -> None:
        ref = update_task.parse_task_reference("https://app.asana.com/0/1200000000000001/1200000000000000")
        self.assertEqual(ref.lookup, "1200000000000000")
        self.assertEqual(ref.input_kind, "url_with_gid")

    def test_dry_run_makes_no_api_calls(self) -> None:
        client = FakeClient()
        result = update_task.update_task(client, make_args(name="New title", add_tag=["1200000000000002"], dry_run=True))
        self.assertEqual(result["action"], "dry_run")
        self.assertEqual(result["gid"], "1200000000000000")
        self.assertEqual(result["applied"]["fields"], {"name": "New title"})
        self.assertEqual(result["applied"]["add_tags"], ["1200000000000002"])
        self.assertEqual(client.calls, [])

    def test_no_changes_is_bad_argument(self) -> None:
        client = FakeClient()
        with self.assertRaises(update_task.AsanaApiError) as error:
            update_task.update_task(client, make_args())
        self.assertEqual(error.exception.category, "bad_argument")
        self.assertEqual(client.calls, [])

    def test_completed_sets_flag_via_put(self) -> None:
        client = FakeClient()
        result = update_task.update_task(client, make_args(completed=True))
        self.assertEqual(result["action"], "updated")
        self.assertEqual(result["applied"]["fields"], {"completed": True})
        self.assertEqual(client.calls[0][0], "PUT")
        self.assertEqual(client.calls[0][1], "/tasks/1200000000000000")
        self.assertTrue(client.calls[0][2]["completed"])

    def test_tag_and_section_ops_use_expected_endpoints(self) -> None:
        client = FakeClient()
        result = update_task.update_task(
            client,
            make_args(
                add_tag=["1200000000000002"],
                remove_tag=["1200000000000004"],
                to_section="1200000000000003",
            ),
        )
        self.assertEqual(result["action"], "updated")
        paths = [(method, path) for method, path, _ in client.calls]
        self.assertIn(("POST", "/tasks/1200000000000000/addTag"), paths)
        self.assertIn(("POST", "/tasks/1200000000000000/removeTag"), paths)
        self.assertIn(("POST", "/sections/1200000000000003/addTask"), paths)
        # No field PUT when only tag/section ops are requested.
        self.assertNotIn("PUT", [method for method, _ in paths])

    def test_reference_without_gid_is_not_found(self) -> None:
        client = FakeClient()
        with self.assertRaises(update_task.AsanaApiError) as error:
            update_task.update_task(client, make_args(task="https://app.asana.com/home", name="x"))
        self.assertEqual(error.exception.category, "not_found")
        self.assertEqual(error.exception.details["error_code"], "task_not_found")
        self.assertEqual(error.exception.details["input_kind"], "url_without_gid")
        self.assertEqual(client.calls, [])

    def test_api_not_found_maps_to_task_not_found(self) -> None:
        client = FakeClient(task_exists=False)
        with self.assertRaises(update_task.AsanaApiError) as error:
            update_task.update_task(client, make_args(name="New title"))
        self.assertEqual(error.exception.category, "not_found")
        self.assertEqual(error.exception.details["error_code"], "task_not_found")
        self.assertEqual(error.exception.details["input_kind"], "gid")

    def test_entity_error_message_maps_to_task_not_found(self) -> None:
        client = FakeClient(entity_error=True)
        with self.assertRaises(update_task.AsanaApiError) as error:
            update_task.update_task(client, make_args(name="New title"))
        self.assertEqual(error.exception.category, "not_found")
        self.assertEqual(error.exception.details["error_code"], "task_not_found")


if __name__ == "__main__":
    unittest.main()
