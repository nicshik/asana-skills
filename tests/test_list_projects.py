#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "asana-list-projects" / "scripts" / "list_projects.py"
SPEC = importlib.util.spec_from_file_location("list_projects", SCRIPT)
assert SPEC and SPEC.loader
list_projects = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = list_projects
SPEC.loader.exec_module(list_projects)


class FakeClient:
    def __init__(self, rows=None, error=None) -> None:
        self.calls: list[tuple[str, dict]] = []
        self.rows = rows if rows is not None else [
            {"gid": "1200000000000000", "name": "Example Project", "archived": False},
            {"gid": "1200000000000001", "name": "Example Archive", "archived": True},
        ]
        self.error = error

    def get_all(self, path, params=None, page_size=100):
        self.calls.append((path, dict(params or {})))
        if self.error is not None:
            raise self.error
        return self.rows


class ListProjectsTest(unittest.TestCase):
    def test_workspace_scope_uses_workspace_endpoint(self) -> None:
        client = FakeClient()
        rows = list_projects.list_projects(client, "1200000000000000", None, None, None)
        self.assertEqual(len(rows), 2)
        path, params = client.calls[0]
        self.assertEqual(path, "/workspaces/1200000000000000/projects")
        self.assertEqual(params["opt_fields"], "name,archived,permalink_url")
        self.assertNotIn("archived", params)

    def test_team_scope_uses_team_endpoint(self) -> None:
        client = FakeClient()
        list_projects.list_projects(client, None, "1200000000000001", None, None)
        path, _ = client.calls[0]
        self.assertEqual(path, "/teams/1200000000000001/projects")

    def test_archived_filter_and_fields_override(self) -> None:
        client = FakeClient()
        list_projects.list_projects(client, "1200000000000000", None, "false", "name")
        _, params = client.calls[0]
        self.assertEqual(params["archived"], "false")
        self.assertEqual(params["opt_fields"], "name")

    def test_error_propagates(self) -> None:
        client = FakeClient(error=list_projects.AsanaApiError("not_found", "Asana API HTTP 404: Not Found"))
        with self.assertRaises(list_projects.AsanaApiError) as error:
            list_projects.list_projects(client, "1200000000000000", None, None, None)
        self.assertEqual(error.exception.category, "not_found")


if __name__ == "__main__":
    unittest.main()
