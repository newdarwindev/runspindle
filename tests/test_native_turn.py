"""Independent synthetic wire oracles; no provider, native binary or store."""

import copy
import hashlib
import importlib.util
import json
import pathlib
import subprocess
import sys
import types
import unittest
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
CODEC = ROOT / "conformance/native-turn-v1/native_turn.py"
SPEC = importlib.util.spec_from_file_location("native_turn_codec", CODEC)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("codec could not be loaded")
codec = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(codec)


def encoded(value: dict[str, Any]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


class NativeTurnContract(unittest.TestCase):
    def setUp(self) -> None:
        self.vectors = json.loads((CODEC.parent / "vectors.json").read_text())
        self.vector = self.vectors[0]
        self.request: dict[str, Any] = copy.deepcopy(self.vector["request"])
        self.data = self.vector["input_utf8"].encode("utf-8")
        self.raw = self.vector["canonical_request"].encode("utf-8")
        self.effects: list[bytes] = []
        self.verifications: list[dict[str, Any]] = []

    def verify(self, request: dict[str, Any]) -> bool:
        self.verifications.append(copy.deepcopy(request))
        return request == self.request

    def consume(self, raw: bytes, **kwargs: Any) -> Any:
        options = {"verifier": self.verify, "request_id": 7}
        options.update(kwargs)
        return codec.consume(
            raw,
            self.request["binding"],
            self.request["thread_id"],
            self.data,
            self.effects.append,
            **options,
        )

    def rejected(self, raw: bytes) -> None:
        with self.assertRaises(codec.Rejected):
            self.consume(raw)
        self.assertEqual(self.effects, [], "forbidden adapter effect")

    def test_independent_vectors_producer_consumer_and_exact_request_digest(
        self,
    ) -> None:
        for vector in self.vectors:
            request = vector["request"]
            original = copy.deepcopy(request)
            data = vector["input_utf8"].encode("utf-8")
            raw = codec.produce(
                request["binding"],
                request["thread_id"],
                data,
                request["profile"]["model"],
            )
            self.assertEqual(raw, vector["canonical_request"].encode("utf-8"))
            self.assertEqual(hashlib.sha256(raw).hexdigest(), vector["request_sha256"])
            self.assertEqual(codec.decode(raw), original)
            self.assertEqual(codec.encode(original), raw)
            calls: list[bytes] = []
            codec.consume(
                raw,
                request["binding"],
                request["thread_id"],
                data,
                calls.append,
                verifier=lambda value: value == original,
                request_id=7,
            )
            self.assertEqual(len(calls), 1)
            # Independently inspect the actual callback bytes, not codec status.
            self.assertEqual(json.loads(calls[0]), vector["upstream_rpc"])
            self.assertTrue(calls[0].endswith(b"\n"))
            self.assertLessEqual(len(calls[0]), 4096)
            self.assertEqual(request, original)
            request["binding"]["task_id"] = "modified-later"
            self.assertEqual(codec.decode(raw), original)

    def test_every_nested_field_missing_extra_duplicate_or_wrong_shape(self) -> None:
        for path in [(), ("binding",), ("input",), ("profile",)]:
            node = self.request[path[0]] if path else self.request
            for field in node:
                value = copy.deepcopy(self.request)
                target = value[path[0]] if path else value
                del target[field]
                self.rejected(encoded(value))
                with self.assertRaises(codec.Rejected):
                    codec.encode(value)
            value = copy.deepcopy(self.request)
            target = value[path[0]] if path else value
            target["unknown"] = "no-override"
            self.rejected(encoded(value))
            invalid: Any
            for invalid in [None, [], 1, "object"]:
                value = copy.deepcopy(self.request)
                if path:
                    value[path[0]] = invalid
                else:
                    value = invalid
                self.rejected(encoded(value))
            # Inject a duplicate at each object depth without dict collapsing it.
            original_node = encoded(node)
            duplicate = (
                b'{"' + next(iter(node)).encode() + b'":null,' + original_node[1:]
            )
            self.rejected(self.raw.replace(original_node, duplicate))

    def test_versions_profiles_input_refs_and_upstream_overrides_fail_closed(
        self,
    ) -> None:
        for version in ["runspindle.envelope.v1", "runspindle.native-turn.v2", None, 1]:
            value = copy.deepcopy(self.request)
            value["version"] = version
            self.rejected(encoded(value))
        for profile in ["read_only_text_v2", "workspace_write", None, 1]:
            value = copy.deepcopy(self.request)
            value["profile"]["kind"] = profile
            self.rejected(encoded(value))
        for location in ["/tmp/input", "https://fixture.invalid/input", "file:input"]:
            value = copy.deepcopy(self.request)
            value["input"]["sha256"] = location
            self.rejected(encoded(value))
        for field in [
            "cwd",
            "sandboxPolicy",
            "approvalPolicy",
            "tools",
            "disabledPluginIds",
            "input",
        ]:
            value = copy.deepcopy(self.request)
            value["profile"][field] = "unauthorized"
            self.rejected(encoded(value))
        for digest in ["A" * 64, "a" * 63, "a" * 65, None, 1]:
            value = copy.deepcopy(self.request)
            value["input"]["sha256"] = digest
            self.rejected(encoded(value))

    def test_descriptor_agrees_with_exercised_contract(self) -> None:
        descriptor = json.loads((ROOT / "contracts/native-turn-v1.json").read_text())
        self.assertEqual(descriptor["version"], codec.VERSION)
        self.assertEqual(set(descriptor["fields"]), set(self.request))
        self.assertEqual(descriptor["binding_fields"], list(codec.BINDING))
        self.assertEqual(descriptor["max_input_bytes"], codec.MAX_INPUT_BYTES)
        self.assertEqual(descriptor["max_envelope_bytes"], codec.MAX_ENVELOPE_BYTES)
        self.assertEqual(
            descriptor["max_upstream_rpc_bytes_including_newline"], codec.MAX_RPC_BYTES
        )
        self.assertEqual(
            set(descriptor["upstream_parameter_fields"]),
            set(self.vector["upstream_rpc"]["params"]),
        )
        self.assertEqual(descriptor["profile_kinds"], [self.request["profile"]["kind"]])

    def test_all_identifiers_counters_and_bool_aliases(self) -> None:
        for key in [
            "task_id",
            "operation_id",
            "policy_revision",
            "host_id",
            "workspace_id",
        ]:
            for invalid in ["", "_prefix", "a/b", "x y", "é", "x" * 129, True, None, 1]:
                value = copy.deepcopy(self.request)
                value["binding"][key] = invalid
                self.rejected(encoded(value))
        for path in [("thread_id",), ("profile", "model")]:
            for invalid in ["", "_prefix", "a/b", "x y", "é", "x" * 129, True, None, 1]:
                value = copy.deepcopy(self.request)
                if len(path) == 1:
                    value[path[0]] = invalid
                else:
                    value[path[0]][path[1]] = invalid
                self.rejected(encoded(value))
        for parent, key in [
            ("binding", "revision"),
            ("binding", "lease_epoch"),
            ("input", "byte_length"),
        ]:
            for invalid in [0, -1, True, False, 1.0, None, "1", 2**64]:
                value = copy.deepcopy(self.request)
                value[parent][key] = invalid
                self.rejected(encoded(value))
        for token in [b"-0", b"-1", b"1.0", b"1e0", b"true", b"NaN", b"Infinity"]:
            self.rejected(self.raw.replace(b'"revision":1', b'"revision":' + token))
        value = copy.deepcopy(self.request)
        value["input"]["byte_length"] = 2049
        self.rejected(encoded(value))

    def test_binding_and_thread_fences_before_authority_or_adapter(self) -> None:
        for key in self.request["binding"]:
            value = copy.deepcopy(self.request)
            value["binding"][key] = 2 if key in ("revision", "lease_epoch") else "other"
            self.rejected(encoded(value))
        value = copy.deepcopy(self.request)
        value["thread_id"] = "other-thread"
        self.rejected(encoded(value))
        self.assertEqual(self.verifications, [])
        # Expected counters cannot exploit Python True == 1.
        expected = copy.deepcopy(self.request["binding"])
        expected["revision"] = True
        with self.assertRaises(codec.Rejected):
            codec.consume(
                self.raw, expected, "thread-fixture", self.data, self.effects.append
            )
        self.assertEqual(self.effects, [])

    def test_full_request_authority_not_admission_or_truthiness(self) -> None:
        with self.assertRaises(codec.Rejected):
            codec.consume(
                self.raw,
                self.request["binding"],
                "thread-fixture",
                self.data,
                self.effects.append,
            )
        result: Any
        for result in [False, None, 1, "allow", {}]:
            with self.assertRaises(codec.Rejected):
                self.consume(self.raw, verifier=lambda _: result)
        value = copy.deepcopy(self.request)
        value["profile"]["model"] = "another-model"
        self.rejected(encoded(value))
        value = copy.deepcopy(self.request)
        value["input"]["sha256"] = "0" * 64
        self.rejected(encoded(value))
        answers = iter([True, False])
        with self.assertRaises(codec.Rejected):
            self.consume(self.raw, verifier=lambda _: next(answers))
        self.assertEqual(self.effects, [])
        self.consume(self.raw)
        self.assertEqual(self.verifications[-2:], [self.request, self.request])

    def test_callback_cannot_mutate_validated_request(self) -> None:
        def verifier(value: dict[str, Any]) -> bool:
            value["profile"]["model"] = "changed"
            value["input"]["sha256"] = "0" * 64
            return True

        self.consume(self.raw, verifier=verifier)
        self.assertEqual(json.loads(self.effects[0]), self.vector["upstream_rpc"])

    def test_input_bytes_are_exact_no_normalization(self) -> None:
        for invalid in [
            b"",
            b"x" * 2049,
            b"\xff",
            b"\xc0\x80",
            b"\xed\xa0\x80",
            "text",
            bytearray(b"text"),
        ]:
            with self.assertRaises(codec.Rejected):
                codec.produce(
                    self.request["binding"], "thread-fixture", invalid, "model-fixture"
                )
        for changed in [
            self.data[:-1],
            self.data + b" ",
            b"x" * len(self.data),
            b"\xff" * len(self.data),
        ]:
            with self.assertRaises(codec.Rejected):
                codec.consume(
                    self.raw,
                    self.request["binding"],
                    "thread-fixture",
                    changed,
                    self.effects.append,
                    verifier=self.verify,
                )
        self.assertEqual(self.effects, [])
        raw1 = codec.produce(
            self.request["binding"], "thread-fixture", "é".encode(), "model-fixture"
        )
        raw2 = codec.produce(
            self.request["binding"],
            "thread-fixture",
            "e\u0301".encode(),
            "model-fixture",
        )
        self.assertNotEqual(codec.decode(raw1)["input"], codec.decode(raw2)["input"])
        # No hidden newline, BOM, trimming or Unicode normalization.
        for data in [b" ", b"\x00", b"\xef\xbb\xbf", b"x" * 2048]:
            request = codec.decode(
                codec.produce(
                    self.request["binding"], "thread-fixture", data, "model-fixture"
                )
            )
            self.assertEqual(
                codec.native_params(request, data)["input"][0]["text"].encode(), data
            )

    def test_envelope_canonical_and_byte_bounds(self) -> None:
        for raw in [
            self.raw + b"\n",
            b" " + self.raw,
            json.dumps(self.request).encode(),
            self.raw.replace(b"task-fixture", b"task\\u002dfixture"),
            b"[]",
            b"null",
            b"\xff",
            b"{" * 4096,
            b" " * 4097,
            b"\xef\xbb\xbf" + self.raw,
        ]:
            self.rejected(raw)
        self.assertEqual(codec.decode(self.raw), self.request)

    def test_rpc_size_counts_escaping_id_and_newline_independently(self) -> None:
        for data in [b"x" * 2048, "🙂".encode() * 512]:
            raw = codec.produce(
                self.request["binding"], "thread-fixture", data, "model-fixture"
            )
            request = codec.decode(raw)
            self.assertEqual(len(data), 2048)
            self.assertLessEqual(len(codec.rpc_bytes(request, data, 2**64 - 1)), 4096)
        # Input limit alone is insufficient: JSON escaping expands this text.
        data = b"\x00" * 2048
        raw = codec.produce(
            self.request["binding"], "thread-fixture", data, "model-fixture"
        )
        with self.assertRaises(codec.Rejected):
            codec.consume(
                raw,
                self.request["binding"],
                "thread-fixture",
                data,
                self.effects.append,
                verifier=lambda _: True,
            )
        self.assertEqual(self.effects, [])
        for request_id in [True, 0, -1, 1.0, 2**64]:
            with self.assertRaises(codec.Rejected):
                self.consume(self.raw, request_id=request_id)
        # Find both exact boundary sizes without reusing the codec's size oracle.
        observed: dict[int, bytes] = {}
        for zeros in range(600, 650):
            for suffix in range(7):
                data = b"\x00" * zeros + b"x" * suffix
                params = copy.deepcopy(self.vector["upstream_rpc"])
                params["params"]["input"][0]["text"] = data.decode()
                size = len(encoded(params)) + 1
                if size in (4096, 4097):
                    observed[size] = data
        self.assertEqual(set(observed), {4096, 4097})
        for size, data in observed.items():
            request = codec.decode(
                codec.produce(
                    self.request["binding"], "thread-fixture", data, "model-fixture"
                )
            )
            if size == 4096:
                self.assertEqual(len(codec.rpc_bytes(request, data, 7)), size)
            else:
                with self.assertRaises(codec.Rejected):
                    codec.rpc_bytes(request, data, 7)

    def test_deliberate_mapping_authority_and_digest_mutations_are_observed(
        self,
    ) -> None:
        source = CODEC.read_text()
        mutations = [
            (
                '"threadId": request["thread_id"]',
                '"threadId": request["binding"]["task_id"]',
            ),
            ("if verifier(copy.deepcopy(request)) is not True:", "if False:"),
            (
                'or hashlib.sha256(data).hexdigest() != request["input"]["sha256"]',
                "or False",
            ),
        ]
        for index, (old, new) in enumerate(mutations):
            self.assertEqual(source.count(old), 2 if index == 1 else 1)
            mutant = types.ModuleType("mutant_native_turn")
            exec(compile(source.replace(old, new), str(CODEC), "exec"), mutant.__dict__)
            effects: list[bytes] = []
            mutant.consume(
                self.raw,
                self.request["binding"],
                "thread-fixture",
                b"x" * len(self.data) if index == 2 else self.data,
                effects.append,
                verifier=(lambda _: False) if index == 1 else self.verify,
                request_id=7,
            )
            self.assertEqual(len(effects), 1)
            if index == 0:
                with self.assertRaises(AssertionError):
                    self.assertEqual(
                        json.loads(effects[0]), self.vector["upstream_rpc"]
                    )
            else:
                with self.assertRaisesRegex(AssertionError, "forbidden adapter effect"):
                    self.assertEqual(effects, [], "forbidden adapter effect")


class OptimizedNativeTurn(unittest.TestCase):
    def test_validation_is_not_removed_by_python_optimization(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-B",
                "-O",
                "-m",
                "unittest",
                "test_native_turn.NativeTurnContract",
                "-v",
            ],
            cwd=ROOT / "tests",
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
