#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "asana-preflight" / "scripts" / "preflight.py"
SPEC = importlib.util.spec_from_file_location("preflight", SCRIPT)
assert SPEC and SPEC.loader
preflight = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = preflight
SPEC.loader.exec_module(preflight)


class FakeClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def request(self, method, path, params=None, data=None, wrap=True, full=False):
        self.calls.append((method, path))
        return {
            "gid": "1200000000000000",
            "name": "Example User",
            "email": "user@example.com",
            "workspaces": [
                {"gid": "1200000000000001", "name": "Example Workspace"},
                {"gid": "1200000000000002", "name": "Another Workspace"},
            ],
        }

    def get_all(self, path, params=None, page_size=100):
        self.calls.append(("GET", path))
        return []


class PreflightTest(unittest.TestCase):
    def test_preflight_parses_user_and_workspaces(self) -> None:
        client = FakeClient()
        info = preflight.preflight(client)
        self.assertEqual(info["user"], "Example User")
        self.assertEqual(info["email"], "user@example.com")
        self.assertEqual(
            info["workspaces"],
            [
                {"gid": "1200000000000001", "name": "Example Workspace"},
                {"gid": "1200000000000002", "name": "Another Workspace"},
            ],
        )

    def test_preflight_calls_users_me_read_only(self) -> None:
        client = FakeClient()
        preflight.preflight(client)
        self.assertEqual(client.calls, [("GET", "/users/me")])
        self.assertTrue(all(method == "GET" for method, _ in client.calls))


if __name__ == "__main__":
    unittest.main()
