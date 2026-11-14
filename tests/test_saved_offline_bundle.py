import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

PATH = Path(__file__).resolve().parents[1] / "tools/run_saved_offline_bundle.py"
spec = importlib.util.spec_from_file_location("saved_offline_bundle", PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class SavedBundleTests(unittest.TestCase):
    def test_changed_bootstrap_and_symlinks_reject_before_execution(self):
        for link in (False, True):
            with self.subTest(link=link), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                name = "composition/tools/maintained_lane_worker.py"
                metadata = {
                    "bundles": {
                        "baseline": {
                            "manifest": {"files": {name: {"sha256": "a" * 64}}}
                        }
                    }
                }
                (root / "bundle-input.json").write_text(json.dumps(metadata))
                bootstrap = root / "bootstrap" / name
                bootstrap.parent.mkdir(parents=True)
                if link:
                    bootstrap.symlink_to(root / "bundle-input.json")
                else:
                    bootstrap.write_bytes(b"changed executable source")
                with patch.object(module.subprocess, "run") as docker:
                    with self.assertRaisesRegex(ValueError, "bootstrap differs"):
                        module.run(root)
                    docker.assert_not_called()


if __name__ == "__main__":
    unittest.main()
