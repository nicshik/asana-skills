#!/usr/bin/env python3
from __future__ import annotations

import builtins
import sys
import unittest
import urllib.error
from types import SimpleNamespace
from unittest import mock

from asana_common import rest as asana_rest


class AsanaCommonTest(unittest.TestCase):
    def test_build_ssl_context_uses_certifi_when_available(self) -> None:
        sentinel = object()
        fake_certifi = SimpleNamespace(where=lambda: "/tmp/certifi.pem")

        with mock.patch.dict(sys.modules, {"certifi": fake_certifi}):
            with mock.patch.object(asana_rest.ssl, "create_default_context", return_value=sentinel) as create:
                result = asana_rest.build_ssl_context()

        self.assertIs(result, sentinel)
        create.assert_called_once_with(cafile="/tmp/certifi.pem")

    def test_build_ssl_context_falls_back_when_certifi_missing(self) -> None:
        sentinel = object()
        original_import = builtins.__import__

        def fake_import(name, *args, **kwargs):
            if name == "certifi":
                raise ImportError("missing certifi")
            return original_import(name, *args, **kwargs)

        with mock.patch("builtins.__import__", side_effect=fake_import):
            with mock.patch.object(asana_rest.ssl, "create_default_context", return_value=sentinel) as create:
                result = asana_rest.build_ssl_context()

        self.assertIs(result, sentinel)
        create.assert_called_once_with()

    def test_request_error_sanitizes_token(self) -> None:
        token = "secret-token-for-test"

        def failing_urlopen(_request, context=None, timeout=None):
            raise urllib.error.URLError(f"certificate failed for {token}")

        client = asana_rest.AsanaClient(token)
        with mock.patch.object(asana_rest.urllib.request, "urlopen", side_effect=failing_urlopen):
            with self.assertRaises(asana_rest.AsanaApiError) as error:
                client.request("GET", "/users/me")

        self.assertNotIn(token, error.exception.message)
        self.assertIn("[redacted]", error.exception.message)

    def test_resolve_token_reads_env_file(self) -> None:
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp:
            env_path = Path(tmp) / ".env.local"
            env_path.write_text("ASANA_ACCESS_TOKEN=from-env-file\n", encoding="utf-8")
            with mock.patch.dict(asana_rest.os.environ, {}, clear=True):
                token = asana_rest.resolve_token(str(env_path))
        self.assertEqual(token, "from-env-file")


if __name__ == "__main__":
    unittest.main()
