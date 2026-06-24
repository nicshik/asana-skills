#!/usr/bin/env python3
from __future__ import annotations

import unittest

from asana_common import refs


class RefsTest(unittest.TestCase):
    def test_bare_gid(self) -> None:
        ref = refs.parse_task_reference("1200000000000000")
        self.assertEqual(ref.lookup, "1200000000000000")
        self.assertEqual(ref.input_kind, "gid")

    def test_url_with_gid(self) -> None:
        ref = refs.parse_task_reference("https://app.asana.com/0/1200000000000001/1200000000000000")
        self.assertEqual(ref.lookup, "1200000000000000")
        self.assertEqual(ref.input_kind, "url_with_gid")

    def test_url_without_gid(self) -> None:
        ref = refs.parse_task_reference("https://app.asana.com/home")
        self.assertEqual(ref.input_kind, "url_without_gid")

    def test_empty(self) -> None:
        ref = refs.parse_task_reference("   ")
        self.assertEqual(ref.input_kind, "empty")

    def test_raw_non_gid(self) -> None:
        ref = refs.parse_task_reference("not-a-gid")
        self.assertEqual(ref.input_kind, "raw")

    def test_not_found_details_shape(self) -> None:
        ref = refs.parse_task_reference("https://app.asana.com/home")
        details = refs.task_not_found_details(ref)
        self.assertEqual(details["error_code"], "task_not_found")
        self.assertIn("hint", details)
        self.assertIn("input_kind", details)


if __name__ == "__main__":
    unittest.main()
