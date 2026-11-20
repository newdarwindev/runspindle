import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable, cast
from unittest.mock import patch

from tools import maintained_scenarios
from tools import run_saved_offline_bundle as module

PATH = Path(module.__file__)


class SavedBundleTests(unittest.TestCase):
    def test_qualification_reports_exact_saved_input_digest(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            artifacts = root / "artifacts"
            platform = root / "platform"
            (platform / "tools").mkdir(parents=True)
            for tool in ("development_bundle.py", "streaming_bundle.py"):
                (platform / "tools" / tool).write_text(
                    "# synthetic bootstrap fixture\n"
                )
            lock = json.loads((PATH.parents[1] / "composition.lock.json").read_bytes())
            pins = {entry["component"]: entry["commit"] for entry in lock["components"]}
            sources = {
                name: {"commit": commit, "path": platform}
                for name, commit in pins.items()
            }

            def build(
                destination: Path, *args: object, variant: str
            ) -> tuple[dict[str, str], str]:
                destination.write_text(variant)
                return {"variant": variant}, hashlib.sha256(
                    variant.encode()
                ).hexdigest()

            def worker(lane: str, directory: Path, sources: object) -> None:
                self.assertEqual(lane, "H12")
                (directory / "H12-worker.json").write_text('{"installed_files": 2}')

            run_lane = cast(
                Callable[..., dict[str, Any]], maintained_scenarios.run_lane
            )
            with (
                patch.dict(
                    sys.modules, {"build_offline_bundle": SimpleNamespace(build=build)}
                ),
                patch.object(
                    maintained_scenarios, "container_worker", side_effect=worker
                ),
            ):
                result = run_lane("H12", sources, artifacts, root, root)
                repeated = run_lane("H12", sources, artifacts, root, root)

            published = (artifacts / "bundle-input.json").read_bytes()
            self.assertEqual(result, repeated)
            self.assertEqual(
                result["bundle_input_sha256"], hashlib.sha256(published).hexdigest()
            )
            self.assertEqual(json.loads(published)["component_commits"], pins)

    def test_input_must_match_trusted_receipt_before_docker(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            expected = hashlib.sha256(b'{"component_commits":{}}').hexdigest()
            (root / "bundle-input.json").write_bytes(
                b'{"component_commits":{"core":"other"}}'
            )
            with patch.object(subprocess, "run") as docker:
                with self.assertRaisesRegex(
                    ValueError, "differs from qualification report"
                ):
                    module.run(root, input_sha256=expected)
                with self.assertRaisesRegex(ValueError, "lowercase SHA-256"):
                    module.run(root, input_sha256="floating")
                docker.assert_not_called()

    def test_cli_requires_digest(self) -> None:
        result = subprocess.run(
            [sys.executable, str(PATH), "--artifacts", "."],
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("--input-sha256", result.stderr)

    def test_changed_bootstrap_and_symlinks_reject_before_execution(self) -> None:
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
                data = json.dumps(metadata).encode()
                (root / "bundle-input.json").write_bytes(data)
                bootstrap = root / "bootstrap" / name
                bootstrap.parent.mkdir(parents=True)
                if link:
                    bootstrap.symlink_to(root / "bundle-input.json")
                else:
                    bootstrap.write_bytes(b"changed executable source")
                with patch.object(subprocess, "run") as docker:
                    with self.assertRaisesRegex(ValueError, "bootstrap differs"):
                        module.run(root, input_sha256=hashlib.sha256(data).hexdigest())
                    docker.assert_not_called()

    def test_qualified_input_digest_is_retained_in_saved_run_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            files = {}
            for name in (
                "composition/tools/maintained_lane_worker.py",
                "platform/tools/development_bundle.py",
                "platform/tools/streaming_bundle.py",
            ):
                path = root / "bootstrap" / name
                path.parent.mkdir(parents=True, exist_ok=True)
                data = name.encode()
                path.write_bytes(data)
                files[name] = {"sha256": hashlib.sha256(data).hexdigest()}
            files["composition/tools/run_saved_offline_bundle.py"] = {
                "sha256": hashlib.sha256(PATH.read_bytes()).hexdigest()
            }
            manifest = {"files": files}
            data = json.dumps(
                {"bundles": {"baseline": {"manifest": manifest}}}
            ).encode()
            (root / "bundle-input.json").write_bytes(data)
            digest = hashlib.sha256(data).hexdigest()

            def docker(args: list[str], **kwargs: object) -> SimpleNamespace:
                if args[:2] == ["docker", "run"]:
                    (root / "H12-worker.json").write_text('{"installed_files": 3}')
                return SimpleNamespace(returncode=int(args[1] == "inspect"))

            with patch.object(subprocess, "run", side_effect=docker) as calls:
                (root / "bundle-input.json").write_bytes(data + b"\n")
                with self.assertRaisesRegex(
                    ValueError, "differs from qualification report"
                ):
                    module.run(root, input_sha256=digest)
                calls.assert_not_called()
                (root / "bundle-input.json").write_bytes(data)
                self.assertEqual(
                    module.run(root, input_sha256=digest),
                    {"installed_files": 3, "bundle_input_sha256": digest},
                )
            self.assertEqual(
                [call.args[0][1] for call in calls.call_args_list],
                ["run", "rm", "inspect"],
            )


if __name__ == "__main__":
    unittest.main()
