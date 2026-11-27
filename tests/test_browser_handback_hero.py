"""H06 component acceptance and source admission regressions."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools import browser_handback_hero as hero

BROWSER = hero.ROOT / "components/browser"


class BrowserHandbackHeroTests(unittest.TestCase):
    def test_missing_browser_checkout_fails_closed(self) -> None:
        spec = json.loads(hero.MANIFEST.read_bytes())
        with (
            tempfile.TemporaryDirectory() as directory,
            patch.object(hero, "git") as git,
            patch.object(hero, "ROOT", Path(directory)),
        ):
            root = Path(directory)
            (root / "composition.lock.json").write_bytes(
                (hero.MANIFEST.parents[1] / "composition.lock.json").read_bytes()
            )
            entries = json.loads((root / "composition.lock.json").read_bytes())[
                "components"
            ]
            git.side_effect = [
                ("160000 " + row["commit"] + " 0\t" + row["path"]).encode()
                for row in entries
            ]
            with self.assertRaisesRegex(ValueError, "clean pinned Browser required"):
                hero.stage_sources(root / "staged", spec)
            self.assertFalse((root / "staged").exists())

    @unittest.skipUnless((BROWSER / ".git").exists(), "exact Browser checkout required")
    def test_exact_source_recovery_and_mutation(self) -> None:
        result = hero.run()
        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["system_acceptance"], "blocked")
        self.assertEqual(result["repeat_runs"], 2)
        self.assertEqual(result["incomplete_closure_mutation"], "detected")

    @unittest.skipUnless((BROWSER / ".git").exists(), "exact Browser checkout required")
    def test_mutated_manifest_source_digest_is_rejected(self) -> None:
        spec = json.loads(hero.MANIFEST.read_bytes())
        spec["source_sha256"][hero.LEASE_SOURCE] = "0" * 64
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "Browser source digest mismatch"):
                hero.stage_sources(Path(directory), spec)
