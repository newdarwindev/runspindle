"""Verify retained page evidence and reject invalid extracted text geometry."""

import hashlib
import unittest
import xml.etree.ElementTree as ET

from tools import document_visual_baselines as lane

REFERENCE = lane.MARKETING / "visual-review"


class VisualBaselines(unittest.TestCase):
    def test_retained_assets_match_their_source_specific_receipts(self) -> None:
        staged_sources = lane.confined_source()
        for name, (_, source_id, disposition) in lane.OUTPUTS.items():
            with self.subTest(artifact=name):
                folder = REFERENCE / name
                receipt = lane.read_json(folder / "receipt.json")
                self.assertEqual(receipt["source_id"], source_id)
                self.assertEqual(receipt["classification"], "offline_tex_candidate")
                self.assertEqual(receipt["review_status"], "pending_confirmation")
                self.assertEqual(receipt["compile"]["overfull_boxes"], [])
                self.assertEqual(
                    receipt["disposition_sha256"],
                    lane.digest((lane.MARKETING / disposition).read_bytes()),
                )
                expected = dict(receipt["artifacts"])
                self.assertRegex(expected.pop("candidate.pdf"), r"^[0-9a-f]{64}$")
                actual = dict(lane.file_digests(folder))
                actual.pop("receipt.json")
                self.assertEqual(expected, actual)
                pages = receipt["output"]["pages"]
                self.assertEqual(
                    {name for name in actual if name.startswith("page-")},
                    {f"page-{index:02d}.png" for index in range(1, len(pages) + 1)},
                )
                for path, digest in receipt["source_hashes"].items():
                    self.assertEqual(digest, staged_sources[path])
                self.assertEqual(
                    receipt["profile_sha256"],
                    hashlib.sha256(lane.CONFIG.read_bytes()).hexdigest(),
                )

    def test_clipped_word_and_nonfinite_coordinates_are_rejected(self) -> None:
        word = ET.Element(
            "word", {"xMin": "8", "yMin": "20", "xMax": "22", "yMax": "30"}
        )
        self.assertTrue(lane.word_inside(word, 100, 100))
        for boundary, value in (("xMax", "112"), ("yMin", "-5"), ("xMax", "nan")):
            with self.subTest(boundary=boundary, value=value):
                changed = ET.Element("word", {**word.attrib, boundary: value})
                self.assertFalse(lane.word_inside(changed, 100, 100))
