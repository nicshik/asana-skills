#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "asana-list-tags" / "scripts" / "list_tags.py"
SPEC = importlib.util.spec_from_file_location("list_tags", SCRIPT)
assert SPEC and SPEC.loader
list_tags = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = list_tags
SPEC.loader.exec_module(list_tags)


class FakeClient:
    def __init__(self, tags=None, error=None) -> None:
        self.calls: list[tuple[str, str, dict | None]] = []
        self.tags = tags if tags is not None else [
            {"gid": "1200000000000000", "name": "Example", "color": "light-blue"},
            {"gid": "1200000000000001", "name": "Other", "color": None},
        ]
        self.error = error

    def request(self, method, path, params=None, data=None, wrap=True, full=False):
        raise AssertionError("list_tags must not call request directly")

    def get_all(self, path, params=None, page_size=100):
        self.calls.append(("GET", path, params))
        if self.error is not None:
            raise self.error
        return self.tags


class ListTagsTest(unittest.TestCase):
    def test_list_tags_returns_rows_and_reads_only(self) -> None:
        client = FakeClient()
        tags = list_tags.list_tags(client, "1200000000000000", fields=None)
        self.assertEqual(len(tags), 2)
        self.assertEqual(tags[0]["gid"], "1200000000000000")
        self.assertEqual(client.calls[0][0], "GET")
        self.assertEqual(client.calls[0][1], "/workspaces/1200000000000000/tags")

    def test_list_tags_uses_default_fields(self) -> None:
        client = FakeClient()
        list_tags.list_tags(client, "1200000000000000", fields=None)
        self.assertEqual(client.calls[0][2], {"opt_fields": "name,color"})

    def test_list_tags_honors_fields_override(self) -> None:
        client = FakeClient()
        list_tags.list_tags(client, "1200000000000000", fields="name,color,notes")
        self.assertEqual(client.calls[0][2], {"opt_fields": "name,color,notes"})

    def test_list_tags_propagates_api_error(self) -> None:
        client = FakeClient(error=list_tags.AsanaApiError("not_found", "Asana API HTTP 404: Not Found"))
        with self.assertRaises(list_tags.AsanaApiError) as error:
            list_tags.list_tags(client, "1200000000000000", fields=None)
        self.assertEqual(error.exception.category, "not_found")


if __name__ == "__main__":
    unittest.main()
