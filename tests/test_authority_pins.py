"""Fail-closed exact-pin and gitlink agreement tests."""

import copy
import json
from pathlib import Path
import unittest

from tools.qualify_authority_pins import validate_lock


class PinTests(unittest.TestCase):
    def setUp(self):
        self.lock = json.loads(
            (Path(__file__).resolve().parents[1] / "composition.lock.json").read_text()
        )
        self.entries = {
            c["path"]: "160000 " + c["commit"] for c in self.lock["components"]
        }

    def test_exact_pins(self):
        validate_lock(self.lock, self.entries)

    def test_newer_core_not_implicitly_qualified(self):
        lock = copy.deepcopy(self.lock)
        core = next(c for c in lock["components"] if c["component"] == "core")
        core["commit"] = "f" * 40
        self.entries[core["path"]] = "160000 " + core["commit"]
        with self.assertRaises(ValueError):
            validate_lock(lock, self.entries)

    def test_gitlink_mismatch(self):
        self.entries["components/tether"] = "160000 " + "a" * 40
        with self.assertRaises(ValueError):
            validate_lock(self.lock, self.entries)

    def test_missing_component(self):
        self.lock["components"].pop()
        with self.assertRaises(ValueError):
            validate_lock(self.lock, self.entries)

    def test_duplicate_component(self):
        self.lock["components"][-1] = copy.deepcopy(self.lock["components"][0])
        with self.assertRaises(ValueError):
            validate_lock(self.lock, self.entries)

    def test_plain_file_not_gitlink(self):
        self.entries["components/core"] = self.entries["components/core"].replace(
            "160000", "100644"
        )
        with self.assertRaises(ValueError):
            validate_lock(self.lock, self.entries)
