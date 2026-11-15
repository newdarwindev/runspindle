import copy
import importlib.util
import json
import pathlib
import subprocess
import sys
import types
import unittest
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "envelope_codec", ROOT / "conformance/envelope-v1/codec.py"
)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("envelope codec module could not be loaded")
codec = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(codec)


class Envelopes(unittest.TestCase):
    def setUp(self) -> None:
        self.vectors = json.loads(
            (ROOT / "conformance/envelope-v1/vectors.json").read_text()
        )

    def test_vectors_and_independent_component_mappings(self) -> None:
        for v in self.vectors:
            e = codec.decode(codec.encode(v["envelope"]))
            self.assertEqual(codec.component(e), v["component"])

    def test_invalid_before_adapter(self) -> None:
        observed: list[dict[str, Any]] = []
        e = self.vectors[0]["envelope"]
        invalid = []
        for key, value in [
            ("version", "unsupported"),
            ("message_type", "unknown"),
            ("message_id", "-bad"),
        ]:
            x = copy.deepcopy(e)
            x[key] = value
            invalid.append(json.dumps(x))
        for key in e:
            x = copy.deepcopy(e)
            del x[key]
            invalid.append(json.dumps(x))
        x = copy.deepcopy(e)
        x["payload"]["binding"] = e["binding"]
        invalid.append(json.dumps(x))
        for invalid_counter in [0, -1, 1.0, True, 2**64]:
            x = copy.deepcopy(e)
            x["binding"]["lease_epoch"] = invalid_counter
            invalid.append(json.dumps(x))
        invalid += [
            json.dumps(e)[:-1] + ',"version":"runspindle.envelope.v1"}',
            json.dumps(e).replace('"revision": 1', '"revision": 1,"revision": 2'),
        ]
        for raw in invalid:
            with self.assertRaises((AssertionError, ValueError, TypeError)):
                codec.consume(raw, e["binding"], observed.append)
        self.assertEqual(observed, [])

    def consume_with_context(
        self, consumer: Any, envelope: dict[str, Any], expected: Any, calls: list[Any]
    ) -> None:
        payload = envelope["payload"]
        request = payload.get("request", payload)
        consumer(
            codec.encode(envelope),
            expected,
            calls.append,
            session=payload.get("native_session_id"),
            destination=(request.get("account_id"), request.get("destination_id")),
        )

    def test_invalid_expected_binding_zero_adapter_calls(self) -> None:
        for vector in self.vectors:
            envelope = vector["envelope"]
            binding = envelope["binding"]
            invalid: list[Any] = [None, [], "invalid", {**binding, "extra": "value"}]
            for key in binding:
                invalid.append(
                    {name: value for name, value in binding.items() if name != key}
                )
                values: list[Any] = (
                    [True, False, float(binding[key]), 0, -1, 2**64]
                    if key in ("revision", "lease_epoch")
                    else [None, True, 1, "", "-invalid"]
                )
                invalid.extend({**binding, key: value} for value in values)
            for expected in invalid:
                with self.subTest(kind=envelope["message_type"], expected=expected):
                    before = copy.deepcopy(expected)
                    calls: list[Any] = []
                    with self.assertRaises(AssertionError):
                        self.consume_with_context(
                            codec.consume, envelope, expected, calls
                        )
                    self.assertEqual(calls, [])
                    self.assertEqual(expected, before)

    def test_valid_expected_binding_preserves_context_and_mapping(self) -> None:
        for vector in self.vectors:
            envelope = vector["envelope"]
            expected = copy.deepcopy(envelope["binding"])
            calls: list[Any] = []
            self.consume_with_context(codec.consume, envelope, expected, calls)
            self.assertEqual(calls, [vector["component"]])
            self.assertEqual(expected, envelope["binding"])

    def test_expected_binding_guard_mutation_detected(self) -> None:
        source = (ROOT / "conformance/envelope-v1/codec.py").read_text()
        guard = "    validate_binding(expected_binding)\n"
        self.assertEqual(source.count(guard), 1)
        mutant = types.ModuleType("unguarded_expected_binding")
        exec(
            compile(source.replace(guard, ""), "synthetic-mutant", "exec"),
            mutant.__dict__,
        )
        envelope = self.vectors[0]["envelope"]
        expected = dict(envelope["binding"], revision=True)
        calls: list[Any] = []
        with self.assertRaises(AssertionError):
            self.consume_with_context(codec.consume, envelope, expected, calls)
        self.assertEqual(calls, [])
        self.consume_with_context(mutant.consume, envelope, expected, calls)
        # The independent effect oracle must catch this removed context guard.
        with self.assertRaises(AssertionError):
            self.assertEqual(calls, [])
        self.assertEqual(calls, [self.vectors[0]["component"]])

    def test_stale_epoch_session_sequence_and_wrong_destination_zero_calls(
        self,
    ) -> None:
        calls: list[dict[str, Any]] = []
        for v in self.vectors:
            e = v["envelope"]
            expected = dict(e["binding"], lease_epoch=2)
            with self.assertRaises(AssertionError):
                codec.consume(codec.encode(e), expected, calls.append)
        e = self.vectors[1]["envelope"]
        for args in [dict(session="wrong"), dict(session="session-1", last_sequence=1)]:
            with self.assertRaises(AssertionError):
                codec.consume(codec.encode(e), e["binding"], calls.append, **args)
        for v in self.vectors[2:4]:
            e = v["envelope"]
            with self.assertRaises(AssertionError):
                codec.consume(
                    codec.encode(e),
                    e["binding"],
                    calls.append,
                    destination=("account-1", "wrong"),
                )
        self.assertEqual(calls, [])


class LexicalCounters(unittest.TestCase):
    def test_negative_zero_and_bom_are_rejected(self) -> None:
        e = json.loads((ROOT / "conformance/envelope-v1/vectors.json").read_text())[1][
            "envelope"
        ]
        raw = codec.encode(e)
        for malformed in [
            raw.replace(b'"observed_at_ms":0', b'"observed_at_ms":-0'),
            b"\xef\xbb\xbf" + raw,
        ]:
            with self.assertRaises((AssertionError, ValueError)):
                codec.decode(malformed)


class OptimizedInterpreter(unittest.TestCase):
    def test_validation_and_context_checks_survive_optimization(self) -> None:
        # Run existing negative and positive cases under -O without recursively
        # invoking this subprocess test. unittest assertions remain active.
        result = subprocess.run(
            [
                sys.executable,
                "-O",
                "-m",
                "unittest",
                "test_envelopes.Envelopes",
                "test_envelopes.LexicalCounters",
                "-v",
            ],
            cwd=ROOT / "tests",
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
