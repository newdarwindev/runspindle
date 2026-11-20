"""Composition H04 staging and independent canary observer checks."""

from __future__ import annotations

import base64
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools import browser_profile_hero as hero


class ProfileHeroTests(unittest.TestCase):
    def test_pin_mismatch_rejects_before_exporting_browser_sources(self) -> None:
        manifest = json.loads(hero.MANIFEST.read_bytes())
        manifest["browser_commit"] = "0" * 40
        with (
            tempfile.TemporaryDirectory() as directory,
            patch.object(hero, "git", wraps=hero.git) as reads,
        ):
            stage = Path(directory) / "source"
            with self.assertRaisesRegex(ValueError, "clean pinned Browser required"):
                hero.stage_sources(stage, manifest)
            self.assertFalse(stage.exists())
            self.assertTrue(
                all("show" not in call.args[1:] for call in reads.call_args_list)
            )

    def test_observer_finds_raw_and_encoded_canaries(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            raw = b"H04_SYNTHETIC_OBSERVER_PROBE"
            self.assertEqual(hero.scan(root, (raw,)), 0)
            (root / "private").write_bytes(raw)
            (root / "encoded").write_bytes(b"RANDOM H04 not the encoded canary")
            self.assertEqual(hero.scan(root, (raw,)), 1)
            (root / "encoded").write_bytes(base64.b64encode(raw))
            self.assertEqual(hero.scan(root, (raw,)), 2)

    def test_read_only_observation_cannot_create_a_store(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            unknown = Path(directory) / "unopened.sqlite"
            with self.assertRaises(sqlite3.OperationalError):
                hero.read_db(unknown, "SELECT 1")
            self.assertFalse(unknown.exists())
