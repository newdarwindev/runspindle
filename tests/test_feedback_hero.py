"""Candidate component integration, never a replacement for existing hero gates."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools import feedback_hero as hero


class FeedbackHeroTests(unittest.TestCase):
    def test_missing_sources_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                hero.verify_sources(Path(directory) / "missing", Path(directory))

    def test_sql_observer_does_not_create_missing_store(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "absent.sqlite"
            with self.assertRaises(ValueError):
                hero.rows(path, "SELECT 1")
            self.assertFalse(path.exists())

    def test_manifest_retains_existing_composition_bases(self) -> None:
        manifest = json.loads(hero.MANIFEST.read_bytes())
        lock = {
            x["component"]: x
            for x in json.loads((hero.ROOT / "composition.lock.json").read_bytes())[
                "components"
            ]
        }
        self.assertEqual(set(manifest["sources"]), {"tether", "refinery"})
        for name, source in manifest["sources"].items():
            self.assertEqual(source["base"], lock[name]["commit"])
            self.assertNotEqual(source["commit"], source["base"])
            self.assertTrue(source["files"])

    def test_changed_source_bytes_rejected_before_import(self) -> None:
        manifest = json.loads(hero.MANIFEST.read_bytes())
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)
            selected = manifest["sources"]["tether"]
            for name in selected["files"]:
                path = source / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"changed")

            def fake_git(root: Path, *args: str) -> str:
                if args[0] == "rev-parse":
                    return str(selected["commit"])
                if args[0] == "ls-files" and "--stage" in args:
                    return "160000 " + str(selected["base"]) + " 0\tcomponents/tether"
                return ""

            with (
                patch.object(hero, "git", fake_git),
                patch.object(subprocess, "run") as ancestry,
            ):
                ancestry.return_value.returncode = 0
                with self.assertRaises(ValueError):
                    hero.verify_sources(source, source)

    def test_public_error_does_not_expose_canary(self) -> None:
        import io
        from contextlib import redirect_stdout

        with (
            patch.object(hero, "run", side_effect=ValueError("PRIVATE_CANARY")),
            patch("sys.argv", ["feedback_hero"]),
            redirect_stdout(io.StringIO()) as output,
        ):
            self.assertEqual(hero.main(), 2)
        self.assertNotIn("PRIVATE_CANARY", output.getvalue())
        self.assertEqual(json.loads(output.getvalue())["status"], "failed")

    @unittest.skipUnless(
        os.environ.get("RUNSPINDLE_FEEDBACK_HERO_REFINERY")
        and os.environ.get("RUNSPINDLE_FEEDBACK_HERO_TETHER"),
        "candidate source checkouts must be explicitly prepared; no fetch/fallback",
    )
    def test_ignored_root_bytecode_rejected_by_actual_worker(self) -> None:
        import py_compile

        source = Path(os.environ["RUNSPINDLE_FEEDBACK_HERO_REFINERY"])
        tether = Path(os.environ["RUNSPINDLE_FEEDBACK_HERO_TETHER"])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            checkout = root / "candidate"
            subprocess.run(
                ["git", "clone", "--no-checkout", str(source), str(checkout)],
                check=True,
                capture_output=True,
            )
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(checkout),
                    "checkout",
                    "--detach",
                    "5690ddd600f5d7b237eed2dac63fc573292a29a1",
                ],
                check=True,
                capture_output=True,
            )
            (checkout / ".git/info/exclude").write_text("html.pyc\n")
            payload = root / "payload.py"
            marker = root / "root-shadow-executed"
            payload.write_text(
                f"open({str(marker)!r}, 'w').write('executed')\n"
                "raise RuntimeError('ROOT_SHADOW_CANARY')\n"
            )
            py_compile.compile(
                str(payload), cfile=str(checkout / "html.pyc"), doraise=True
            )
            self.assertEqual(hero.git(checkout, "status", "--porcelain"), "")
            completed = subprocess.run(
                [
                    sys.executable,
                    *(["-O"] if sys.flags.optimize else []),
                    "-B",
                    str(Path(hero.__file__)),
                    "--worker",
                    "prepare",
                    "--directory",
                    str(root),
                    "--tether",
                    str(tether),
                    "--refinery",
                    str(checkout),
                ],
                env=dict(
                    os.environ,
                    PYTHONPYCACHEPREFIX=str(root / "cache"),
                    PYTHONDONTWRITEBYTECODE="1",
                ),
                capture_output=True,
                timeout=30,
            )
            self.assertEqual(completed.returncode, 2)
            self.assertNotIn(b"ROOT_SHADOW_CANARY", completed.stdout + completed.stderr)
            self.assertEqual(json.loads(completed.stdout)["status"], "failed")
            self.assertFalse((root / "admission.sqlite").exists())
            self.assertFalse(marker.exists(), "untrusted root bytecode executed")

    @unittest.skipUnless(
        os.environ.get("RUNSPINDLE_FEEDBACK_HERO_REFINERY")
        and os.environ.get("RUNSPINDLE_FEEDBACK_HERO_TETHER"),
        "candidate source checkouts must be explicitly prepared; no fetch/fallback",
    )
    def test_ignored_sourceless_package_rejected_before_import(self) -> None:
        import py_compile

        source = Path(os.environ["RUNSPINDLE_FEEDBACK_HERO_REFINERY"])
        tether = Path(os.environ["RUNSPINDLE_FEEDBACK_HERO_TETHER"])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            checkout = root / "candidate"
            subprocess.run(
                ["git", "clone", "--no-checkout", str(source), str(checkout)],
                check=True,
                capture_output=True,
            )
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(checkout),
                    "checkout",
                    "--detach",
                    "5690ddd600f5d7b237eed2dac63fc573292a29a1",
                ],
                check=True,
                capture_output=True,
            )
            (checkout / ".git/info/exclude").write_text("refinery/storage/\n")
            package = checkout / "refinery/storage"
            package.mkdir()
            payload = root / "payload.py"
            payload.write_text("raise RuntimeError('SOURCE_SUBSTITUTION_CANARY')\n")
            py_compile.compile(
                str(payload), cfile=str(package / "__init__.pyc"), doraise=True
            )
            self.assertEqual(hero.git(checkout, "status", "--porcelain"), "")
            with patch.object(hero, "fixture") as fixture:
                with self.assertRaises(ValueError):
                    hero.worker(root, tether, checkout, "prepare")
                fixture.assert_not_called()

    @unittest.skipUnless(
        os.environ.get("RUNSPINDLE_FEEDBACK_HERO_REFINERY")
        and os.environ.get("RUNSPINDLE_FEEDBACK_HERO_TETHER"),
        "candidate source checkouts must be explicitly prepared; no fetch/fallback",
    )
    def test_actual_pinned_stores_twice_restart_negatives_and_mutation(self) -> None:
        result = hero.run(
            Path(os.environ["RUNSPINDLE_FEEDBACK_HERO_TETHER"]),
            Path(os.environ["RUNSPINDLE_FEEDBACK_HERO_REFINERY"]),
        )
        self.assertEqual(result["repeat_runs"], 2)
        self.assertEqual(result["precommit_process_crash_recovery"], "passed")
        self.assertTrue(result["deliberate_mutation_detected"])
        self.assertEqual(result["system_acceptance"], "blocked")


if __name__ == "__main__":
    unittest.main()
