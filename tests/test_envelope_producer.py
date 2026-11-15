"""Independent synthetic component producer oracles, not runtime authority tests."""

import copy
import importlib.util
import json
import pathlib
import subprocess
import sys
import types
import unittest
from typing import Any, Callable

ROOT = pathlib.Path(__file__).resolve().parents[1]
CODEC = ROOT / "conformance/envelope-v1/codec.py"
SPEC = importlib.util.spec_from_file_location("producer_codec", CODEC)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("envelope codec module could not be loaded")
codec = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(codec)


def mapping_paths(
    value: dict[str, Any], path: tuple[str, ...] = ()
) -> list[tuple[str, ...]]:
    result = [path]
    for key, child in value.items():
        if type(child) is dict:
            result.extend(mapping_paths(child, (*path, key)))
    return result


def at(value: dict[str, Any], path: tuple[str, ...]) -> Any:
    for key in path:
        value = value[key]
    return value


class ComponentProducer(unittest.TestCase):
    def setUp(self) -> None:
        self.vectors = json.loads((CODEC.parent / "vectors.json").read_text())

    def assert_round_trip(
        self, vector: dict[str, Any], producer: Callable[..., bytes] = codec.produce
    ) -> None:
        expected = vector["envelope"]
        source = copy.deepcopy(vector["component"])
        raw = producer(source, expected["message_type"], expected["message_id"])
        # The fixture and stdlib encoding are independent of both codec directions.
        self.assertEqual(
            raw,
            json.dumps(
                expected, sort_keys=True, separators=(",", ":"), ensure_ascii=False
            ).encode(),
        )
        self.assertEqual(json.loads(raw), expected)
        self.assertEqual(codec.component(codec.decode(raw)), vector["component"])
        self.assertEqual(source, vector["component"])
        effects: list[dict[str, Any]] = []
        payload = expected["payload"]
        request = payload.get("request", payload)
        codec.consume(
            raw,
            expected["binding"],
            effects.append,
            session=payload.get("native_session_id"),
            destination=(request.get("account_id"), request.get("destination_id")),
        )
        self.assertEqual(effects, [vector["component"]])
        # Mutating the caller afterward must not change the emitted message.
        source.clear()
        self.assertEqual(json.loads(raw), expected)

    def assert_rejected_before_effect(
        self,
        value: Any,
        vector: dict[str, Any],
        producer: Callable[..., bytes] = codec.produce,
    ) -> None:
        expected = vector["envelope"]
        before = copy.deepcopy(value)
        effects: list[dict[str, Any]] = []
        payload = expected["payload"]
        request = payload.get("request", payload)
        rejected = False
        try:
            raw = producer(value, expected["message_type"], expected["message_id"])
        except AssertionError:
            rejected = True
        else:
            try:
                codec.consume(
                    raw,
                    expected["binding"],
                    effects.append,
                    session=payload.get("native_session_id"),
                    destination=(
                        request.get("account_id"),
                        request.get("destination_id"),
                    ),
                )
            except AssertionError:
                pass  # Consumer rejection cannot substitute for producer rejection.
        self.assertEqual(effects, [], "invalid component caused an adapter effect")
        self.assertTrue(rejected, "invalid component was encoded")
        self.assertEqual(value, before, "producer changed the caller's value")

    def test_all_independent_vectors_and_canonical_bytes(self) -> None:
        for vector in self.vectors:
            with self.subTest(kind=vector["envelope"]["message_type"]):
                self.assert_round_trip(vector)

    def test_all_terminal_variants(self) -> None:
        for terminal, state in [
            (None, "running"),
            ("Completed", "completed"),
            ("Failed", "failed"),
            ("Cancelled", "cancelled"),
        ]:
            vector = copy.deepcopy(self.vectors[1])
            vector["component"]["terminal"] = terminal
            vector["envelope"]["payload"]["state"] = state
            self.assert_round_trip(vector)

    def test_revision_predecessor_and_counter_boundaries(self) -> None:
        for revision in [2, 2**64 - 1]:
            vector = copy.deepcopy(self.vectors[0])
            vector["component"]["revision"] = revision
            vector["component"]["predecessor_revision"] = revision - 1
            vector["envelope"]["binding"]["revision"] = revision
            vector["envelope"]["payload"]["predecessor_revision"] = revision - 1
            self.assert_round_trip(vector)
        for index in [2, 3]:
            vector = copy.deepcopy(self.vectors[index])
            component = vector["component"].get("request", vector["component"])
            payload = vector["envelope"]["payload"].get(
                "request", vector["envelope"]["payload"]
            )
            component["accepted"]["validation"]["artifact"]["artifact_revision"] = (
                2**64 - 1
            )
            payload["artifact_revision"] = 2**64 - 1
            self.assert_round_trip(vector)

    def test_every_nested_mapping_rejects_missing_extra_and_non_object_values(
        self,
    ) -> None:
        for vector in self.vectors:
            original = vector["component"]
            for path in mapping_paths(original):
                for field in at(original, path):
                    value = copy.deepcopy(original)
                    del at(value, path)[field]
                    with self.subTest(path=path, missing=field):
                        self.assert_rejected_before_effect(value, vector)
                value = copy.deepcopy(original)
                at(value, path)["unexpected"] = "no-second-binding"
                self.assert_rejected_before_effect(value, vector)
                malformed: Any
                for malformed in [None, [], 1, "object"]:
                    value = copy.deepcopy(original)
                    if path:
                        at(value, path[:-1])[path[-1]] = malformed
                    else:
                        value = malformed
                    self.assert_rejected_before_effect(value, vector)

    def test_validation_requires_exact_true_and_matching_policy(self) -> None:
        for vector in self.vectors[2:4]:
            passed: Any
            for passed in [False, None, 0, 1, "true", [], {}]:
                value = copy.deepcopy(vector["component"])
                request = value.get("request", value)
                request["accepted"]["validation"]["passed"] = passed
                self.assert_rejected_before_effect(value, vector)
            for policy in ["other-policy", True, 1, None, ""]:
                value = copy.deepcopy(vector["component"])
                request = value.get("request", value)
                request["accepted"]["validation"]["policy_revision"] = policy
                self.assert_rejected_before_effect(value, vector)

    def test_all_counter_fields_reject_bool_float_negative_and_overflow(self) -> None:
        class IntSubclass(int):
            pass

        for vector in self.vectors:
            original = vector["component"]
            for path in mapping_paths(original):
                for key in at(original, path):
                    if key not in [
                        "revision",
                        "lease_epoch",
                        "sequence",
                        "observed_at_ms",
                        "artifact_revision",
                    ]:
                        continue
                    invalid = [-1, 1.0, True, False, 2**64, None, "1", IntSubclass(1)]
                    if key != "observed_at_ms":
                        invalid.append(0)
                    for counter in invalid:
                        value = copy.deepcopy(original)
                        at(value, path)[key] = counter
                        with self.subTest(path=path, key=key, counter=counter):
                            self.assert_rejected_before_effect(value, vector)

    def test_all_identifiers_and_digests_are_strict(self) -> None:
        exempt = {
            "version",
            "revision",
            "lease_epoch",
            "sequence",
            "observed_at_ms",
            "artifact_revision",
            "predecessor_revision",
            "passed",
            "terminal",
        }
        for vector in self.vectors:
            original = vector["component"]
            for path in mapping_paths(original):
                for key, child in at(original, path).items():
                    if key in exempt or type(child) is dict:
                        continue
                    invalid: list[Any] = [
                        None,
                        True,
                        1,
                        [],
                        {},
                        "",
                        "é",
                        "-bad",
                        "a" * 129,
                    ]
                    if key in ["sha256", "normalized_digest"]:
                        invalid += ["A" * 64, "a" * 63, "a" * 65, "z" * 64]
                    for entry in invalid:
                        value = copy.deepcopy(original)
                        at(value, path)[key] = entry
                        self.assert_rejected_before_effect(value, vector)

    def test_invalid_terminal_predecessor_version_and_operation(self) -> None:
        for terminal in ["running", "completed", "Unknown", True, 1, {}, []]:
            value = copy.deepcopy(self.vectors[1]["component"])
            value["terminal"] = terminal
            self.assert_rejected_before_effect(value, self.vectors[1])
        for revision, predecessor in [
            (1, 0),
            (1, 1),
            (2, None),
            (2, 0),
            (2, True),
            (2, 1.0),
            (2, -1),
            (2, 2),
            (2, 2**64),
        ]:
            value = copy.deepcopy(self.vectors[0]["component"])
            value.update(revision=revision, predecessor_revision=predecessor)
            self.assert_rejected_before_effect(value, self.vectors[0])
        for index in [0, 2, 3]:
            vector = self.vectors[index]
            for version in [codec.VERSION, "unknown", None, True, {}]:
                value = copy.deepcopy(vector["component"])
                value.get("request", value)["version"] = version
                self.assert_rejected_before_effect(value, vector)
        for vector in self.vectors[2:4]:
            value = copy.deepcopy(vector["component"])
            request = value.get("request", value)
            request["delivery_operation_id"] = vector["envelope"]["binding"][
                "operation_id"
            ]
            self.assert_rejected_before_effect(value, vector)

    def test_explicit_metadata_and_wrong_mapping_reject(self) -> None:
        kind: Any
        for kind in ["unknown", "", None, True, 1, [], {}]:
            with self.assertRaises(AssertionError):
                codec.produce(self.vectors[0]["component"], kind, "message-1")
        identity: Any
        for identity in ["", "-bad", "a" * 129, None, 1, True, {}, []]:
            with self.assertRaises(AssertionError):
                codec.produce(
                    self.vectors[0]["component"], "admission_request", identity
                )
        for index, vector in enumerate(self.vectors[:4]):
            for other in self.vectors[:index] + self.vectors[index + 1 : 4]:
                with self.assertRaises(AssertionError):
                    codec.produce(
                        vector["component"],
                        other["envelope"]["message_type"],
                        "message-1",
                    )

    def test_produced_messages_preserve_consumer_context_fences(self) -> None:
        effects: list[dict[str, Any]] = []
        for vector in self.vectors:
            e = vector["envelope"]
            raw = codec.produce(vector["component"], e["message_type"], e["message_id"])
            for field, original in e["binding"].items():
                expected = dict(e["binding"])
                expected[field] = (
                    original + 1 if type(original) is int else original + "-other"
                )
                with self.assertRaises(AssertionError):
                    codec.consume(raw, expected, effects.append)
            if e["message_type"] == "host_observation":
                for session, sequence in [
                    ("wrong", 0),
                    ("session-1", e["payload"]["sequence"]),
                ]:
                    with self.assertRaises(AssertionError):
                        codec.consume(
                            raw,
                            e["binding"],
                            effects.append,
                            session=session,
                            last_sequence=sequence,
                        )
            elif e["message_type"] in ["delivery_request", "delivery_receipt"]:
                for destination in [("wrong", "destination-1"), ("account-1", "wrong")]:
                    with self.assertRaises(AssertionError):
                        codec.consume(
                            raw, e["binding"], effects.append, destination=destination
                        )
        self.assertEqual(effects, [])

    def test_negative_wire_tokens_reject_before_effect(self) -> None:
        vector = self.vectors[1]
        raw = codec.produce(vector["component"], "host_observation", "message-2")
        effects: list[dict[str, Any]] = []
        for token in [b"-0", b"-1", b"0.0", b"true"]:
            malformed = raw.replace(b'"observed_at_ms":0', b'"observed_at_ms":' + token)
            with self.assertRaises(AssertionError):
                codec.consume(
                    malformed,
                    vector["envelope"]["binding"],
                    effects.append,
                    session="session-1",
                )
        self.assertEqual(effects, [])

    def test_deliberate_mapping_and_validation_mutations_are_detected(self) -> None:
        source = CODEC.read_text()
        mutations = [
            (
                'payload["validator_revision"] = validation["validator_revision"]',
                'payload["validator_revision"] = validation["policy_revision"]',
            ),
            ('if validation["passed"] is not True:', "if False:"),
        ]
        for index, (old, new) in enumerate(mutations):
            self.assertEqual(source.count(old), 1)
            mutated = types.ModuleType("deliberately_broken_codec")
            exec(
                compile(source.replace(old, new), str(CODEC), "exec"), mutated.__dict__
            )
            if index == 0:
                # A mutually consistent encode/decode is insufficient: the fixture
                # independently pins validator identity and catches substitution.
                with self.assertRaises(AssertionError):
                    self.assert_round_trip(self.vectors[2], mutated.produce)
            else:
                value = copy.deepcopy(self.vectors[2]["component"])
                value["accepted"]["validation"]["passed"] = False
                with self.assertRaisesRegex(
                    AssertionError, "invalid component caused an adapter effect"
                ):
                    self.assert_rejected_before_effect(
                        value, self.vectors[2], mutated.produce
                    )


class OptimizedProducer(unittest.TestCase):
    def test_all_producer_checks_survive_optimization(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-O",
                "-m",
                "unittest",
                "test_envelope_producer.ComponentProducer",
                "-v",
            ],
            cwd=ROOT / "tests",
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
