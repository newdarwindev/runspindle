"""Verify the committed candidate and its actual-render evidence slots."""

import hashlib
import json
import pathlib
import struct
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
VISUAL = ROOT / "visual"
REFERENCE = VISUAL / "reference"


class StoryboardReference(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = json.loads((VISUAL / "storyboards.json").read_bytes())
        self.evidence = json.loads((REFERENCE / "evidence.json").read_bytes())

    def test_every_generated_asset_agrees_with_its_digest(self) -> None:
        assets = self.evidence["assets"]
        self.assertEqual(
            set(assets) | {"evidence.json"}, {p.name for p in REFERENCE.iterdir()}
        )
        for name, digest in assets.items():
            with self.subTest(asset=name):
                self.assertEqual(
                    hashlib.sha256((REFERENCE / name).read_bytes()).hexdigest(), digest
                )
        for width, height in self.fixture["render_profile"]["viewports"]:
            png = (REFERENCE / f"viewport-{width}.png").read_bytes()
            self.assertEqual(png[:8], b"\x89PNG\r\n\x1a\n")
            self.assertEqual(struct.unpack(">II", png[16:24]), (width, height))

    def test_every_story_has_an_issue_reference_and_pending_actual_render(self) -> None:
        coverage = self.evidence["coverage"]
        self.assertEqual(set(coverage), {"h01", "h06", "h07", "h08", "h09"})
        self.assertEqual(self.evidence["review"], "candidate_pending_approval")
        self.assertEqual(self.evidence["behavioral_acceptance"], "not_run")
        for case in self.fixture["cases"]:
            row = coverage[case["id"]]
            self.assertEqual(row["issue"], case["parent"])
            self.assertEqual(row["criterion"], case["criterion"])
            self.assertEqual(
                row["actual_render"], {"status": "not_run", "capture": None}
            )
            self.assertEqual(
                row["canonical_states"], [frame[4:] for frame in case["frames"]]
            )
            self.assertIn(row["reference"], self.evidence["assets"])

    def test_shared_identities_and_source_pins_are_bound(self) -> None:
        source = self.evidence["source"]
        for path, digest in source["files"].items():
            with self.subTest(input=path):
                self.assertEqual(
                    hashlib.sha256((ROOT / path).read_bytes()).hexdigest(), digest
                )
        lock = json.loads((ROOT / "composition.lock.json").read_bytes())
        self.assertEqual(
            source["composition_pins"],
            {row["component"]: row["commit"] for row in lock["components"]},
        )
        html = (REFERENCE / "index.html").read_text()
        for value in self.fixture["identity"].values():
            self.assertEqual(html.count(value), 1)
