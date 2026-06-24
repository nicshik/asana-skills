#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "asana-comment-task" / "scripts" / "comment_task.py"
SPEC = importlib.util.spec_from_file_location("comment_task", SCRIPT)
assert SPEC and SPEC.loader
comment_task = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = comment_task
SPEC.loader.exec_module(comment_task)


class FakeClient:
    def __init__(self, task_exists: bool = True, entity_error: bool = False) -> None:
        self.calls: list[tuple[str, str]] = []
        self.task_exists = task_exists
        self.entity_error = entity_error

    def request(self, method, path, params=None, data=None, wrap=True, full=False):
        self.calls.append((method, path))
        if self.entity_error:
            raise comment_task.AsanaApiError("not_found", "Asana API HTTP 404: Not Found: task")
        if not self.task_exists:
            raise comment_task.AsanaApiError("not_found", "Asana API HTTP 404: Not Found")
        return {"gid": "1200000000000099"}

    def get_all(self, path, params=None, page_size=100):
        self.calls.append(("GET", path))
        return []


class CommentTaskTest(unittest.TestCase):
    def test_commented_posts_story_and_returns_gid(self) -> None:
        client = FakeClient()
        result = comment_task.comment_task(client, "1200000000000000", "Hello", dry_run=False)
        self.assertEqual(result["action"], "commented")
        self.assertEqual(result["task"], "1200000000000000")
        self.assertEqual(result["story_gid"], "1200000000000099")
        self.assertEqual(client.calls, [("POST", "/tasks/1200000000000000/stories")])

    def test_dry_run_makes_no_api_call(self) -> None:
        client = FakeClient()
        result = comment_task.comment_task(client, "1200000000000000", "Hello", dry_run=True)
        self.assertEqual(result["action"], "dry_run")
        self.assertEqual(result["task"], "1200000000000000")
        self.assertEqual(result["text_length"], 5)
        self.assertEqual(client.calls, [])

    def test_reference_without_gid_is_not_found(self) -> None:
        client = FakeClient()
        with self.assertRaises(comment_task.AsanaApiError) as error:
            comment_task.comment_task(client, "https://app.asana.com/home", "Hello", dry_run=False)
        self.assertEqual(error.exception.category, "not_found")
        self.assertEqual(error.exception.details["error_code"], "task_not_found")
        self.assertEqual(error.exception.details["input_kind"], "url_without_gid")
        self.assertEqual(client.calls, [])

    def test_api_not_found_maps_to_task_not_found(self) -> None:
        client = FakeClient(task_exists=False)
        with self.assertRaises(comment_task.AsanaApiError) as error:
            comment_task.comment_task(client, "1200000000000000", "Hello", dry_run=False)
        self.assertEqual(error.exception.category, "not_found")
        self.assertEqual(error.exception.details["error_code"], "task_not_found")
        self.assertEqual(error.exception.details["input_kind"], "gid")

    def test_entity_not_found_message_maps_to_task_not_found(self) -> None:
        client = FakeClient(entity_error=True)
        with self.assertRaises(comment_task.AsanaApiError) as error:
            comment_task.comment_task(client, "1200000000000000", "Hello", dry_run=False)
        self.assertEqual(error.exception.category, "not_found")
        self.assertEqual(error.exception.details["error_code"], "task_not_found")


if __name__ == "__main__":
    unittest.main()
