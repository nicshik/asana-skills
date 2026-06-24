#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "asana-project-sections" / "scripts" / "project_sections.py"
SPEC = importlib.util.spec_from_file_location("project_sections", SCRIPT)
assert SPEC and SPEC.loader
project_sections = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = project_sections
SPEC.loader.exec_module(project_sections)


class FakeClient:
    def __init__(self, sections=None, created_gid: str = "1200000000000010") -> None:
        self.calls: list[tuple[str, str]] = []
        self.sections = sections if sections is not None else [
            {"gid": "1200000000000001", "name": "To Do", "created_at": "2026-01-01T00:00:00.000Z"},
            {"gid": "1200000000000002", "name": "Doing", "created_at": "2026-01-02T00:00:00.000Z"},
        ]
        self.created_gid = created_gid

    def request(self, method, path, params=None, data=None, wrap=True, full=False):
        self.calls.append((method, path))
        return {"gid": self.created_gid, "name": (data or {}).get("name")}

    def get_all(self, path, params=None, page_size=100):
        self.calls.append(("GET", path))
        return self.sections


class ProjectSectionsTest(unittest.TestCase):
    def test_list_returns_sections_via_get_all(self) -> None:
        client = FakeClient()
        result = project_sections.list_sections(client, "1200000000000000")
        self.assertEqual(result["action"], "list")
        self.assertEqual(result["count"], 2)
        self.assertEqual(result["sections"][0]["gid"], "1200000000000001")
        self.assertEqual(client.calls, [("GET", "/projects/1200000000000000/sections")])

    def test_create_posts_section_and_returns_gid(self) -> None:
        client = FakeClient()
        result = project_sections.create_section(client, "1200000000000000", "Example Section", dry_run=False)
        self.assertEqual(result["action"], "created")
        self.assertEqual(result["gid"], "1200000000000010")
        self.assertEqual(result["name"], "Example Section")
        self.assertEqual(client.calls, [("POST", "/projects/1200000000000000/sections")])

    def test_create_dry_run_does_not_write(self) -> None:
        client = FakeClient()
        result = project_sections.create_section(client, "1200000000000000", "Example Section", dry_run=True)
        self.assertEqual(result["action"], "dry_run")
        self.assertEqual(result["name"], "Example Section")
        self.assertEqual(client.calls, [])

    def test_error_category_propagates(self) -> None:
        client = FakeClient()

        def boom(*args, **kwargs):
            raise project_sections.AsanaApiError("not_found", "Asana API HTTP 404: Not Found")

        client.get_all = boom  # type: ignore[assignment]
        with self.assertRaises(project_sections.AsanaApiError) as error:
            project_sections.list_sections(client, "1200000000000000")
        self.assertEqual(error.exception.category, "not_found")


if __name__ == "__main__":
    unittest.main()
