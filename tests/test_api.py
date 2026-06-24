#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "asana-api" / "scripts" / "api.py"
SPEC = importlib.util.spec_from_file_location("api", SCRIPT)
assert SPEC and SPEC.loader
api = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = api
SPEC.loader.exec_module(api)


class FakeArgs:
    def __init__(
        self,
        method="GET",
        path="/tasks/1200000000000000",
        query=None,
        field=None,
        data_file=None,
        opt_fields=None,
        all=False,
    ) -> None:
        self.method = method
        self.path = path
        self.query = query or []
        self.field = field or []
        self.data_file = data_file
        self.opt_fields = opt_fields
        self.all = all


class FakeClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []
        self.last_params = None
        self.last_data = None
        self.last_wrap = None

    def request(self, method, path, params=None, data=None, wrap=True, full=False):
        self.calls.append((method, path))
        self.last_params = params
        self.last_data = data
        self.last_wrap = wrap
        return {"gid": "1200000000000000", "name": "Fixture task"}

    def get_all(self, path, params=None, page_size=100):
        self.calls.append(("GET", path))
        self.last_params = params
        return [{"gid": "1200000000000000"}, {"gid": "1200000000000001"}]


class ApiTest(unittest.TestCase):
    def test_split_kv_requires_equals(self) -> None:
        with self.assertRaises(api.AsanaApiError) as error:
            api.split_kv("noseparator")
        self.assertEqual(error.exception.category, "bad_argument")

    def test_field_builds_string_data_dict(self) -> None:
        client = FakeClient()
        args = FakeArgs(method="POST", path="/tasks", field=["name=Example", "workspace=1200000000000000"])
        result = api.call_api(client, args)
        self.assertEqual(client.calls, [("POST", "/tasks")])
        self.assertEqual(client.last_data, {"name": "Example", "workspace": "1200000000000000"})
        self.assertTrue(client.last_wrap)
        self.assertEqual(result["data"]["gid"], "1200000000000000")

    def test_query_and_opt_fields_build_params(self) -> None:
        client = FakeClient()
        args = FakeArgs(query=["completed=false"], opt_fields="name,completed")
        api.call_api(client, args)
        self.assertEqual(client.last_params, {"completed": "false", "opt_fields": "name,completed"})

    def test_all_uses_get_all(self) -> None:
        client = FakeClient()
        args = FakeArgs(method="GET", path="/projects/1200000000000001/tasks", all=True)
        result = api.call_api(client, args)
        self.assertEqual(client.calls, [("GET", "/projects/1200000000000001/tasks")])
        self.assertEqual(len(result["data"]), 2)

    def test_data_file_with_top_level_data_sends_unwrapped(self) -> None:
        client = FakeClient()
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
            json.dump({"data": {"name": "Example"}, "options": {"pretty": True}}, handle)
            data_path = handle.name
        try:
            args = FakeArgs(method="PUT", path="/tasks/1200000000000000", data_file=data_path)
            api.call_api(client, args)
        finally:
            Path(data_path).unlink()
        self.assertFalse(client.last_wrap)
        self.assertEqual(client.last_data, {"data": {"name": "Example"}, "options": {"pretty": True}})

    def test_data_file_without_data_key_is_inner_data(self) -> None:
        client = FakeClient()
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
            json.dump({"name": "Example"}, handle)
            data_path = handle.name
        try:
            args = FakeArgs(method="POST", path="/tasks", data_file=data_path)
            api.call_api(client, args)
        finally:
            Path(data_path).unlink()
        self.assertTrue(client.last_wrap)
        self.assertEqual(client.last_data, {"name": "Example"})

    def test_data_file_wins_over_field(self) -> None:
        client = FakeClient()
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
            json.dump({"name": "FromFile"}, handle)
            data_path = handle.name
        try:
            args = FakeArgs(method="POST", path="/tasks", field=["name=FromField"], data_file=data_path)
            api.call_api(client, args)
        finally:
            Path(data_path).unlink()
        self.assertEqual(client.last_data, {"name": "FromFile"})


if __name__ == "__main__":
    unittest.main()
