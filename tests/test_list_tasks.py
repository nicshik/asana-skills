#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import sys
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "asana-list-tasks" / "scripts" / "list_tasks.py"
SPEC = importlib.util.spec_from_file_location("list_tasks", SCRIPT)
assert SPEC and SPEC.loader
list_tasks = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = list_tasks
SPEC.loader.exec_module(list_tasks)


FIXTURE_TASKS = [
    {
        "gid": "1200000000000000",
        "name": "Fixture task",
        "completed": False,
        "assignee": {"name": "Example User"},
        "memberships": [{"section": {"name": "Doing"}}],
        "due_on": "2026-07-01",
        "permalink_url": "https://app.asana.com/0/1200000000000001/1200000000000000",
    },
    {
        "gid": "1200000000000002",
        "name": "Another fixture task",
        "completed": True,
        "assignee": None,
        "memberships": [],
        "due_on": None,
        "permalink_url": "https://app.asana.com/0/1200000000000001/1200000000000002",
    },
]


class FakeClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict | None]] = []

    def request(self, method, path, params=None, data=None, wrap=True, full=False):
        self.calls.append((method, path, params))
        return list(FIXTURE_TASKS)

    def get_all(self, path, params=None, page_size=100):
        self.calls.append(("GET", path, params))
        return list(FIXTURE_TASKS)


def make_args(**overrides) -> argparse.Namespace:
    base = {
        "project": None,
        "section": None,
        "tag": None,
        "assignee": None,
        "workspace": None,
        "completed_since": None,
        "fields": None,
        "limit": 50,
        "all": False,
        "env_file": None,
        "json": False,
    }
    base.update(overrides)
    return argparse.Namespace(**base)


class ListTasksTest(unittest.TestCase):
    def test_project_routes_to_project_tasks_and_no_write(self) -> None:
        client = FakeClient()
        tasks = list_tasks.list_tasks(client, make_args(project="1200000000000000"))
        self.assertEqual(len(tasks), 2)
        method, path, params = client.calls[0]
        self.assertEqual(method, "GET")
        self.assertEqual(path, "/projects/1200000000000000/tasks")
        self.assertEqual(params["limit"], 50)
        self.assertTrue(all(m == "GET" for m, _, _ in client.calls))

    def test_section_route(self) -> None:
        path, params = list_tasks.resolve_route(make_args(section="1200000000000001"))
        self.assertEqual(path, "/sections/1200000000000001/tasks")
        self.assertEqual(params, {})

    def test_tag_route(self) -> None:
        path, params = list_tasks.resolve_route(make_args(tag="1200000000000000"))
        self.assertEqual(path, "/tags/1200000000000000/tasks")
        self.assertEqual(params, {})

    def test_assignee_route_includes_workspace_and_completed_since(self) -> None:
        path, params = list_tasks.resolve_route(
            make_args(
                assignee="me",
                workspace="1200000000000001",
                completed_since="2026-06-01T00:00:00Z",
            )
        )
        self.assertEqual(path, "/tasks")
        self.assertEqual(params["assignee"], "me")
        self.assertEqual(params["workspace"], "1200000000000001")
        self.assertEqual(params["completed_since"], "2026-06-01T00:00:00Z")

    def test_all_uses_get_all(self) -> None:
        client = FakeClient()
        list_tasks.list_tasks(client, make_args(tag="1200000000000000", all=True))
        self.assertEqual(client.calls[0][0], "GET")
        self.assertEqual(client.calls[0][1], "/tags/1200000000000000/tasks")
        # get_all path does not set a per-request limit param
        self.assertNotIn("limit", client.calls[0][2])

    def test_no_selector_raises_bad_argument(self) -> None:
        with self.assertRaises(list_tasks.AsanaApiError) as error:
            list_tasks.resolve_route(make_args())
        self.assertEqual(error.exception.category, "bad_argument")

    def test_multiple_selectors_raise_bad_argument(self) -> None:
        with self.assertRaises(list_tasks.AsanaApiError) as error:
            list_tasks.resolve_route(make_args(project="1200000000000000", tag="1200000000000001"))
        self.assertEqual(error.exception.category, "bad_argument")

    def test_assignee_without_workspace_raises_bad_argument(self) -> None:
        with self.assertRaises(list_tasks.AsanaApiError) as error:
            list_tasks.resolve_route(make_args(assignee="me"))
        self.assertEqual(error.exception.category, "bad_argument")


if __name__ == "__main__":
    unittest.main()
