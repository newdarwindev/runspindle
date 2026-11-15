"""Fixed pre-check diagnostics without exposing metadata or relaxing gates."""

from __future__ import annotations

import base64
import copy
import io
import json
import os
import subprocess
import sys
import unittest
from contextlib import ExitStack, redirect_stderr, redirect_stdout
from pathlib import Path
from typing import Any
from unittest.mock import patch

from tools import partition_validation as gate

CANARY = "PRIVATE_CANARY_URL_TOKEN"
BINDING_FIELDS = (
    "image_sha256",
    "image_source_sha",
    "controller_sha256",
    "recipe_sha256",
    "tool_closure_sha256",
)


class PartitionDiagnosticsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manifests = gate.manifests()
        self.image = self.manifests[0]["image"]
        self.instance = {
            "image_sha256": self.image["sha256"],
            "image_source_sha": self.image["source_sha"],
            **{
                key: self.image[key]
                for key in ("controller_sha256", "recipe_sha256", "tool_closure_sha256")
            },
        }
        self.guest = {
            "rust_closure_sha256": self.image["rust_closure_sha256"],
            "runtime_builder": {"archive_sha256": self.image["builder_archive_sha256"]},
        }

    def invoke(
        self,
        *,
        failure: str = "",
        category: str = "invalid_value",
        observed: dict[str, Any] | None = None,
        binding_failures: list[str] | None = None,
    ) -> tuple[dict[str, Any], Any]:
        instance = copy.deepcopy(self.instance if observed is None else observed)
        guest = copy.deepcopy(self.guest)
        if failure == "image_binding" and observed is None:
            instance["image_sha256"] = CANARY
            binding_failures = ["image_sha256:mismatched"]
        if failure == "rust_closure":
            guest["rust_closure_sha256"] = CANARY
        if failure == "builder_archive":
            guest["runtime_builder"]["archive_sha256"] = CANARY

        def read(path: Path) -> str:
            stage = (
                "instance_metadata"
                if path.name == "runspindle-instance.json"
                else "image_metadata"
            )
            if failure == stage:
                raise ValueError(CANARY)
            return json.dumps(instance if stage == "instance_metadata" else guest)

        output = io.StringIO()
        with ExitStack() as stack:
            stack.enter_context(
                patch.object(sys, "argv", ["partition_validation.py", "mutation_4"])
            )
            stack.enter_context(
                patch.dict(os.environ, {"GITHUB_SHA": "a" * 40, "GITHUB_RUN_ID": "17"})
            )
            stack.enter_context(
                patch.object(
                    gate,
                    "manifests",
                    return_value=self.manifests,
                    side_effect=ValueError(CANARY) if failure == "manifest" else None,
                )
            )
            stack.enter_context(patch.object(Path, "read_text", read))
            stack.enter_context(
                patch.object(
                    gate,
                    "digest",
                    return_value=CANARY
                    if failure == "quality_closure"
                    else self.image["quality_closure_sha256"],
                )
            )
            stack.enter_context(
                patch.object(
                    gate,
                    "source_sha",
                    return_value="b" * 40 if failure == "run_identity" else "a" * 40,
                    side_effect=ValueError(CANARY)
                    if failure == "source_identity"
                    else None,
                )
            )
            check = stack.enter_context(
                patch.object(gate, "receipt", side_effect=ValueError(CANARY))
            )
            with redirect_stdout(output), redirect_stderr(io.StringIO()) as stderr:
                code = gate.cli()
        self.assertEqual(code, 2)
        self.assertEqual(stderr.getvalue(), "")
        raw = output.getvalue()
        self.assertNotIn(CANARY, raw)
        self.assertNotIn("receipt=", raw)
        result = json.loads(raw)
        expected: dict[str, Any] = {
            "status": "failed",
            "reason": "validation_error",
            "stage": failure,
            "category": category,
        }
        if binding_failures is not None:
            expected["binding_failures"] = binding_failures
        self.assertEqual(result, expected)
        self.assertLessEqual(len(raw), 512)
        return result, check

    def test_each_binding_field_missing_mismatched_or_invalid_still_fails(self) -> None:
        for field in BINDING_FIELDS:
            observed = self.instance.copy()
            del observed[field]
            with self.subTest(field=field, problem="missing"):
                _, check = self.invoke(
                    failure="image_binding",
                    observed=observed,
                    binding_failures=[field + ":missing"],
                )
                check.assert_not_called()
            for actual in (
                "0" * len(self.instance[field]),
                "",
                CANARY * 1000,
                None,
                True,
                17,
                1.25,
                [CANARY],
                {CANARY: CANARY},
            ):
                with self.subTest(field=field, actual_type=type(actual).__name__):
                    _, check = self.invoke(
                        failure="image_binding",
                        observed={**self.instance, field: actual, CANARY: CANARY},
                        binding_failures=[field + ":mismatched"],
                    )
                    check.assert_not_called()

    def test_multiple_binding_failures_have_fixed_field_order(self) -> None:
        observed: dict[str, Any] = {CANARY: {CANARY: CANARY}}
        for field in reversed(BINDING_FIELDS):
            if field in ("image_source_sha", "recipe_sha256"):
                observed[field] = CANARY
        _, check = self.invoke(
            failure="image_binding",
            observed=observed,
            binding_failures=[
                "image_sha256:missing",
                "image_source_sha:mismatched",
                "controller_sha256:missing",
                "recipe_sha256:mismatched",
                "tool_closure_sha256:missing",
            ],
        )
        check.assert_not_called()
        _, check = self.invoke(
            failure="image_binding",
            observed={},
            binding_failures=[field + ":missing" for field in BINDING_FIELDS],
        )
        check.assert_not_called()

    def test_matching_binding_ignores_unrelated_metadata(self) -> None:
        observed = {**self.instance, CANARY: {CANARY: [CANARY]}}
        gate.validate_instance_binding(observed, self.image)
        with (
            patch.object(
                Path,
                "read_text",
                side_effect=[json.dumps(observed), json.dumps(self.guest)],
            ),
            patch.object(
                gate, "digest", return_value=self.image["quality_closure_sha256"]
            ),
        ):
            self.assertEqual(gate.guest_identity(self.image), observed)

    def test_binding_exception_retains_no_metadata_or_values(self) -> None:
        with self.assertRaises(gate.ImageBindingFailure) as caught:
            gate.validate_instance_binding(
                {field: CANARY for field in BINDING_FIELDS} | {CANARY: CANARY},
                self.image,
            )
        error = caught.exception
        self.assertEqual(str(error), "wrong or missing qualified image binding")
        self.assertEqual(
            error.__dict__,
            {"binding_failures": tuple(f + ":mismatched" for f in BINDING_FIELDS)},
        )
        self.assertNotIn(CANARY, repr(error) + repr(error.__dict__))

    def test_tampered_binding_hints_are_omitted_without_changing_failure(self) -> None:
        class HostileString(str):
            def __eq__(self, other: object) -> bool:
                raise AssertionError(CANARY)

            __hash__ = str.__hash__

        class HostileTuple(tuple[str, ...]):
            def __iter__(self) -> Any:
                raise AssertionError(CANARY)

        valid = ("image_sha256:missing",)
        for hint in (
            None,
            (),
            list(valid),
            {CANARY: CANARY},
            CANARY,
            valid * 6,
            (CANARY,),
            ("image_sha256:" + CANARY,),
            (CANARY + ":missing",),
            (HostileString(valid[0]),),
            HostileTuple(valid),
            (17,),
            valid * 2,
            ("image_sha256:missing", "image_sha256:mismatched"),
            ("recipe_sha256:missing", "image_sha256:missing"),
            (valid[0], CANARY),
        ):
            error = gate.PartitionFailure(gate.Stage.IMAGE_BINDING, ValueError(CANARY))
            error.__dict__["binding_failures"] = hint
            with (
                patch.object(gate, "main", side_effect=error),
                redirect_stdout(io.StringIO()) as output,
                redirect_stderr(io.StringIO()) as stderr,
            ):
                self.assertEqual(gate.cli(), 2)
            self.assertEqual(
                json.loads(output.getvalue()),
                {
                    "status": "failed",
                    "reason": "validation_error",
                    "stage": "image_binding",
                    "category": "invalid_value",
                },
            )
            self.assertNotIn(CANARY, output.getvalue())
            self.assertEqual(stderr.getvalue(), "")
        for stage, cause in (
            (gate.Stage.MANIFEST, ValueError(CANARY)),
            (gate.Stage.IMAGE_BINDING, KeyError(CANARY)),
        ):
            error = gate.PartitionFailure(stage, cause)
            error.__dict__["binding_failures"] = valid
            self.assertNotIn("binding_failures", gate.failure_record(error))

    def test_each_precheck_failure_is_specific_and_never_runs_checks(self) -> None:
        for stage in (
            "manifest",
            "instance_metadata",
            "image_metadata",
            "image_binding",
            "rust_closure",
            "builder_archive",
            "quality_closure",
            "source_identity",
            "run_identity",
        ):
            with self.subTest(stage=stage):
                _, check = self.invoke(failure=stage)
                check.assert_not_called()

    def test_execution_failure_is_not_mislabeled_image_failure(self) -> None:
        _, check = self.invoke(failure="check_execution")
        check.assert_called_once()

    def test_closed_categories_never_include_exception_content(self) -> None:
        errors = [
            (json.JSONDecodeError(CANARY, CANARY, 0), "invalid_json"),
            (UnicodeError(CANARY), "invalid_encoding"),
            (FileNotFoundError(CANARY), "missing_file"),
            (PermissionError(CANARY), "file_access_denied"),
            (
                subprocess.CalledProcessError(1, CANARY, output=CANARY),
                "command_failed",
            ),
            (KeyError(CANARY), "missing_field"),
            (OSError(CANARY), "io_error"),
            (ValueError(CANARY), "invalid_value"),
        ]
        for error, expected in errors:
            with (
                self.subTest(category=expected),
                self.assertRaises(gate.PartitionFailure) as caught,
            ):
                with gate.diagnostic_stage(gate.Stage.MANIFEST):
                    raise error
            self.assertEqual(caught.exception.category, expected)
            self.assertNotIn(CANARY, str(caught.exception))
            self.assertTrue(caught.exception.__suppress_context__)

    def test_success_receipt_bytes_and_exit_remain_unchanged(self) -> None:
        value = {"status": "passed", "checks": [], "synthetic": "receipt"}
        expected = base64.b64encode(
            json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
        ).decode()
        import tempfile

        with tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
            destination = Path(directory) / "output"
            stack.enter_context(
                patch.object(
                    sys,
                    "argv",
                    [
                        "partition_validation.py",
                        "mutation_4",
                        "--output",
                        str(destination),
                    ],
                )
            )
            stack.enter_context(
                patch.dict(os.environ, {"GITHUB_SHA": "a" * 40, "GITHUB_RUN_ID": "17"})
            )
            stack.enter_context(
                patch.object(gate, "manifests", return_value=self.manifests)
            )
            stack.enter_context(
                patch.object(gate, "guest_identity", return_value=self.instance)
            )
            stack.enter_context(patch.object(gate, "source_sha", return_value="a" * 40))
            stack.enter_context(patch.object(gate, "receipt", return_value=value))
            with redirect_stdout(io.StringIO()) as output:
                self.assertEqual(gate.cli(), 0)
            self.assertEqual(output.getvalue(), "")
            self.assertEqual(destination.read_text(), "receipt=" + expected + "\n")

    def test_check_failure_exit_and_receipt_output_failure_remain_failures(
        self,
    ) -> None:
        for output_failure in (False, True):
            with self.subTest(output_failure=output_failure), ExitStack() as stack:
                stack.enter_context(
                    patch.object(
                        sys,
                        "argv",
                        [
                            "partition_validation.py",
                            "mutation_4",
                            "--output",
                            "/unused/output",
                        ],
                    )
                )
                stack.enter_context(
                    patch.dict(
                        os.environ, {"GITHUB_SHA": "a" * 40, "GITHUB_RUN_ID": "17"}
                    )
                )
                stack.enter_context(
                    patch.object(gate, "manifests", return_value=self.manifests)
                )
                stack.enter_context(
                    patch.object(gate, "guest_identity", return_value=self.instance)
                )
                stack.enter_context(
                    patch.object(gate, "source_sha", return_value="a" * 40)
                )
                value = {
                    "status": "failed",
                    "checks": [
                        {"id": "outbox-mutations", "status": "failed", "exit_code": 1}
                    ],
                }
                stack.enter_context(patch.object(gate, "receipt", return_value=value))
                stream = io.StringIO()
                stack.enter_context(
                    patch.object(
                        Path,
                        "open",
                        side_effect=PermissionError(CANARY) if output_failure else None,
                        return_value=stream,
                    )
                )
                with redirect_stdout(io.StringIO()) as output:
                    code = gate.cli()
                self.assertNotIn(CANARY, output.getvalue())
                if output_failure:
                    self.assertEqual(code, 2)
                    self.assertEqual(
                        json.loads(output.getvalue()),
                        {
                            "status": "failed",
                            "reason": "validation_error",
                            "stage": "receipt_output",
                            "category": "file_access_denied",
                        },
                    )
                else:
                    self.assertEqual(code, 1)
                    self.assertIn("hygiene failure:", output.getvalue())

    def test_invalid_aggregate_input_does_not_call_aggregate_or_checks(self) -> None:
        with ExitStack() as stack:
            stack.enter_context(
                patch.object(sys, "argv", ["partition_validation.py", "aggregate"])
            )
            environment = {"GITHUB_SHA": "a" * 40, "GITHUB_RUN_ID": "17"}
            environment.update(
                {"RECEIPT_" + name.upper(): "" for name in gate.PARTITIONS}
            )
            stack.enter_context(patch.dict(os.environ, environment))
            stack.enter_context(
                patch.object(gate, "manifests", return_value=self.manifests)
            )
            stack.enter_context(
                patch.object(gate, "guest_identity", return_value=self.instance)
            )
            stack.enter_context(patch.object(gate, "source_sha", return_value="a" * 40))
            aggregate = stack.enter_context(patch.object(gate, "aggregate"))
            checks = stack.enter_context(patch.object(gate, "receipt"))
            with redirect_stdout(io.StringIO()) as output:
                self.assertEqual(gate.cli(), 2)
            self.assertEqual(json.loads(output.getvalue())["stage"], "aggregate_input")
            aggregate.assert_not_called()
            checks.assert_not_called()

    def test_forged_exception_fields_and_subclasses_cannot_leak(self) -> None:
        class BadStage:
            @property
            def value(self) -> str:
                raise AssertionError(CANARY + " property accessed")

        class BadCategory(str):
            def __eq__(self, other: object) -> bool:
                raise AssertionError(CANARY + " equality accessed")

            __hash__ = str.__hash__

        class ForgedFailure(gate.PartitionFailure):
            @property
            def category(self) -> str:
                raise AssertionError(CANARY + " subclass property accessed")

            @category.setter
            def category(self, value: str) -> None:
                raise AssertionError(CANARY + " subclass setter accessed")

        errors: list[BaseException] = []
        forged_stage = str.__new__(gate.Stage, CANARY)
        object.__setattr__(forged_stage, "_name_", CANARY)
        object.__setattr__(forged_stage, "_value_", CANARY)
        for stage, category in (
            (gate.Stage.MANIFEST, CANARY),
            (CANARY, "invalid_value"),
            (BadStage(), "invalid_value"),
            (forged_stage, "invalid_value"),
            (gate.Stage.MANIFEST, BadCategory("invalid_value")),
            (gate.Stage.MANIFEST, [CANARY]),
        ):
            error = gate.PartitionFailure(gate.Stage.MANIFEST, ValueError())
            error.__dict__.update(stage=stage, category=category)
            errors.append(error)
        subclass = ForgedFailure.__new__(ForgedFailure)
        errors.append(subclass)
        missing = gate.PartitionFailure(gate.Stage.MANIFEST, ValueError())
        missing.__dict__.clear()
        errors.append(missing)
        expected = {
            "status": "failed",
            "reason": "validation_error",
            "stage": "unclassified",
            "category": "unclassified",
        }
        for candidate in errors:
            with (
                patch.object(gate, "main", side_effect=candidate),
                redirect_stdout(io.StringIO()) as output,
            ):
                self.assertEqual(gate.cli(), 2)
            self.assertEqual(json.loads(output.getvalue()), expected)
            self.assertNotIn(CANARY, output.getvalue())

    def test_mutable_enum_value_is_never_serialized(self) -> None:
        error = gate.PartitionFailure(gate.Stage.MANIFEST, ValueError())
        original = gate.Stage.MANIFEST.value
        try:
            object.__setattr__(gate.Stage.MANIFEST, "_value_", CANARY)
            with (
                patch.object(gate, "main", side_effect=error),
                redirect_stdout(io.StringIO()) as output,
            ):
                self.assertEqual(gate.cli(), 2)
            self.assertEqual(json.loads(output.getvalue())["stage"], "manifest")
            self.assertNotIn(CANARY, output.getvalue())
        finally:
            object.__setattr__(gate.Stage.MANIFEST, "_value_", original)


if __name__ == "__main__":
    unittest.main()
