"""Synthetic runtime-preflight regressions; no image is built or qualified here."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from check_document_runtime import CLOSURE_SHA256, INTERPRETER, PACKAGES, PYTHON, check

ROOT = Path(__file__).resolve().parents[1]


class DocumentRuntimeTests(unittest.TestCase):
    def receipt(self) -> dict[str, object]:
        return {
            "status": "verified",
            "closure_sha256": CLOSURE_SHA256,
            "python": PYTHON,
            "interpreter": INTERPRETER,
            "packages": dict(PACKAGES),
            "wheel_count": 3,
        }

    def invoke(
        self,
        *,
        executable: str = INTERPRETER,
        prefix: str = "/opt/runspindle-documents",
        version: str = PYTHON,
        implementation: str = "CPython",
        machine: str = "x86_64",
        system: str = "Linux",
        packages: dict[str, str] | None = None,
        receipt: dict[str, object] | None = None,
        image: dict[str, object] | None = None,
    ) -> None:
        value = self.receipt() if receipt is None else receipt
        check(
            executable=executable,
            prefix=prefix,
            version=version,
            implementation=implementation,
            machine=machine,
            system=system,
            packages=PACKAGES if packages is None else packages,
            receipt=value,
            image={"documents": value} if image is None else image,
        )

    def test_exact_synthetic_preflight(self) -> None:
        self.invoke()

    def test_missing_wrong_extra_package(self) -> None:
        for packages in (
            {},
            {**PACKAGES, "reportlab": "4.4.8"},
            {**PACKAGES, "extra": "1"},
        ):
            with self.subTest(packages=packages), self.assertRaises(ValueError):
                self.invoke(packages=packages)

    def test_ambient_python_is_not_a_fallback(self) -> None:
        with self.assertRaises(ValueError):
            self.invoke(executable="/usr/bin/python3")
        with self.assertRaises(ValueError):
            self.invoke(prefix="/usr")
        with self.assertRaises(ValueError):
            self.invoke(version="3.12.14")
        with self.assertRaises(ValueError):
            self.invoke(implementation="PyPy")
        with self.assertRaises(ValueError):
            self.invoke(machine="aarch64")
        with self.assertRaises(ValueError):
            self.invoke(system="Darwin")

    def test_missing_stale_or_forged_receipt(self) -> None:
        for key, value in (
            ("status", "pending"),
            ("closure_sha256", "0" * 64),
            ("python", "3.12.14"),
            ("interpreter", "/usr/bin/python3"),
            ("packages", {}),
            ("wheel_count", 2),
        ):
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.invoke(receipt={**self.receipt(), key: value})
        with self.assertRaises(ValueError):
            self.invoke(receipt={})
        with self.assertRaises(ValueError):
            self.invoke(image={})

    def test_workflow_keeps_required_regeneration_and_isolation(self) -> None:
        workflow = (ROOT / ".github/workflows/validation.yml").read_text()
        preflight = f"run: {INTERPRETER} tools/check_document_runtime.py"
        validation = f"run: {INTERPRETER} tools/validate.py"
        self.assertEqual(workflow.count(preflight), 1)
        self.assertEqual(workflow.count(validation), 1)
        self.assertLess(workflow.index(preflight), workflow.index(validation))
        self.assertIn(
            "runs-on: [self-hosted, linux, x64, runspindle-isolated, strix]", workflow
        )
        self.assertIn("python3 tools/feedback_hero.py", workflow)
        for forbidden in ("pip install", "continue-on-error", "|| true"):
            self.assertNotIn(forbidden, workflow)
        generator = (ROOT / "tests/test_marketing_vision.py").read_text()
        self.assertIn("for _ in range(2):", generator)
        self.assertIn("self.assertEqual(self.snapshot(), before)", generator)
        self.assertIn("self.assertIsNotNone(", generator)


if __name__ == "__main__":
    unittest.main()
