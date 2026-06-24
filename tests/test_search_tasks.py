#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "asana-search-tasks" / "scripts" / "search_tasks.py"
SPEC = importlib.util.spec_from_file_location("search_tasks", SCRIPT)
assert SPEC and SPEC.loader
search_tasks = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = search_tasks
SPEC.loader.exec_module(search_tasks)


class FakeClient:
    def __init__(self, premium_error: bool = False) -> None:
        self.calls: list[tuple[str, str, dict]] = []
        self.premium_error = premium_error

    def request(self, method, path, params=None, data=None, wrap=True, full=False):
        self.calls.append((method, path, dict(params or {})))
        if self.premium_error:
            raise search_tasks.AsanaApiError("premium_required", "Asana API HTTP 402: payment required")
        return [
            {
                "gid": "1200000000000000",
                "name": "Fixture task",
                "completed": False,
                "permalink_url": "https://app.asana.com/0/1200000000000001/1200000000000000",
                "memberships": [{"section": {"name": "Doing"}}],
            },
        ]

    def get_all(self, path, params=None, page_size=100):
        self.calls.append(("GET", path, dict(params or {})))
        return []


class SearchTasksTest(unittest.TestCase):
    def test_search_passes_text_and_workspace(self) -> None:
        client = FakeClient()
        tasks = search_tasks.search_tasks(
            client,
            workspace="1200000000000000",
            text="billing",
            project=None,
            limit=20,
            fields=None,
        )
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]["gid"], "1200000000000000")
        method, path, params = client.calls[0]
        self.assertEqual(method, "GET")
        self.assertEqual(path, "/workspaces/1200000000000000/tasks/search")
        self.assertEqual(params["text"], "billing")
        self.assertEqual(params["limit"], 20)
        self.assertNotIn("projects.any", params)
        self.assertEqual(params["opt_fields"], search_tasks.DEFAULT_FIELDS)

    def test_project_sets_projects_any(self) -> None:
        client = FakeClient()
        search_tasks.search_tasks(
            client,
            workspace="1200000000000000",
            text="release",
            project="1200000000000001",
            limit=50,
            fields=None,
        )
        _, _, params = client.calls[0]
        self.assertEqual(params["projects.any"], "1200000000000001")
        self.assertEqual(params["limit"], 50)

    def test_search_is_read_only(self) -> None:
        client = FakeClient()
        search_tasks.search_tasks(
            client,
            workspace="1200000000000000",
            text="review",
            project=None,
            limit=20,
            fields=None,
        )
        self.assertTrue(all(method == "GET" for method, _, _ in client.calls))

    def test_premium_required_surfaces(self) -> None:
        client = FakeClient(premium_error=True)
        with self.assertRaises(search_tasks.AsanaApiError) as error:
            search_tasks.search_tasks(
                client,
                workspace="1200000000000000",
                text="billing",
                project=None,
                limit=20,
                fields=None,
            )
        self.assertEqual(error.exception.category, "premium_required")


if __name__ == "__main__":
    unittest.main()
