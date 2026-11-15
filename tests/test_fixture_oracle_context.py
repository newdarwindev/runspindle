"""Independent context negatives for the existing synthetic fixture oracle."""

import copy
import importlib.util
import json
import types
import unittest
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "fixtures/v1/fixturekit.py"
SPEC = importlib.util.spec_from_file_location("context_fixturekit", SOURCE)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("fixture kit cannot be loaded")
kit: Any = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(kit)


class FixtureOracleContextTests(unittest.TestCase):
    def setUp(self) -> None:
        self.golden: list[dict[str, Any]] = json.loads(
            (SOURCE.parent / "golden.json").read_text()
        )

    def observations(self, fixture: dict[str, Any]) -> dict[str, Any]:
        return {
            fixture["state"]: {
                "identity": copy.deepcopy(fixture["identity"]),
                "detail": copy.deepcopy(fixture["detail"]),
            },
            "accepted_digest": fixture["identity"].get("artifact_digest"),
            "approved_digest": fixture["identity"].get("candidate_digest"),
        }

    def invalid_identities(self, identity: dict[str, Any]) -> list[Any]:
        values: list[Any] = [None, [], "identity", {**identity, "extra": "field"}]
        for name, value in identity.items():
            values.append({k: v for k, v in identity.items() if k != name})
            replacements: list[Any] = (
                [True, False, float(value), -1, 2**53, "1", None]
                if type(value) is int
                else [None, True, 1, "", "white space"]
            )
            values.extend(
                {**identity, name: replacement} for replacement in replacements
            )
        return values

    def test_expected_identities_reject_malformed_fields_without_mutation(self) -> None:
        for fixture in self.golden:
            for identity in self.invalid_identities(fixture["identity"]):
                observations = self.observations(fixture)
                before = copy.deepcopy((fixture, identity, observations))
                with self.subTest(kind=fixture["kind"], identity=identity):
                    with self.assertRaises(kit.ContractError):
                        kit.assert_conforms(
                            fixture, identity, fixture["state"], observations
                        )
                    self.assertEqual((fixture, identity, observations), before)

    def test_independent_receipt_identities_reject_malformed_fields(self) -> None:
        for fixture in self.golden:
            if fixture["state"] not in ("delivered", "persisted", "serving"):
                continue
            for identity in self.invalid_identities(fixture["identity"]):
                observations = self.observations(fixture)
                observations[fixture["state"]]["identity"] = identity
                before = copy.deepcopy((fixture, observations))
                with self.subTest(kind=fixture["kind"], identity=identity):
                    with self.assertRaises(kit.ContractError):
                        kit.assert_conforms(
                            fixture, fixture["identity"], fixture["state"], observations
                        )
                    self.assertEqual((fixture, observations), before)

    def test_all_valid_contexts_and_counter_boundaries(self) -> None:
        for original in self.golden:
            for counter in (1, 2**53 - 1):
                fixture = copy.deepcopy(original)
                fixture["identity"] = {
                    key: counter if type(value) is int else value
                    for key, value in fixture["identity"].items()
                }
                self.assertTrue(
                    kit.assert_conforms(
                        fixture,
                        fixture["identity"],
                        fixture["state"],
                        self.observations(fixture),
                    )
                )
            self.assertTrue(
                kit.assert_conforms(
                    original,
                    original["identity"],
                    original["state"],
                    self.observations(original),
                )
            )

    def test_other_oracle_comparisons_remain_fail_closed(self) -> None:
        for fixture in self.golden:
            with self.subTest(kind=fixture["kind"]):
                for state in (True, None, "unsupported-state"):
                    with self.assertRaises(kit.ContractError):
                        kit.assert_conforms(
                            fixture,
                            fixture["identity"],
                            state,
                            self.observations(fixture),
                        )
                if fixture["state"] in ("delivered", "persisted", "serving"):
                    receipt: Any
                    for receipt in (None, [], {}, {"extra": "field"}):
                        observations = self.observations(fixture)
                        observations[fixture["state"]] = receipt
                        with self.assertRaises(kit.ContractError):
                            kit.assert_conforms(
                                fixture,
                                fixture["identity"],
                                fixture["state"],
                                observations,
                            )
                    observations = self.observations(fixture)
                    observations[fixture["state"]]["detail"] = {"receipt_id": True}
                    with self.assertRaises(kit.ContractError):
                        kit.assert_conforms(
                            fixture, fixture["identity"], fixture["state"], observations
                        )
        for index, digest_name in ((4, "accepted_digest"), (7, "approved_digest")):
            fixture = self.golden[index]
            digest: Any
            for digest in (None, True, 1, [], {}, "0" * 64):
                observations = self.observations(fixture)
                observations[digest_name] = digest
                with self.assertRaises(kit.ContractError):
                    kit.assert_conforms(
                        fixture, fixture["identity"], fixture["state"], observations
                    )

    def test_each_removed_identity_guard_reproduces_false_pass(self) -> None:
        source = SOURCE.read_text()
        for guard, independent in (
            ("    validate(dict(envelope, identity=expected_identity))\n", False),
            ('        validate(dict(envelope, identity=receipt["identity"]))\n', True),
        ):
            self.assertEqual(source.count(guard), 1)
            mutant = types.ModuleType("fixture_context_mutant")
            mutant.__file__ = str(SOURCE)
            exec(
                compile(source.replace(guard, ""), "synthetic-mutant", "exec"),
                mutant.__dict__,
            )
            fixture = self.golden[5] if independent else self.golden[0]
            expected = copy.deepcopy(fixture["identity"])
            observations = self.observations(fixture)
            if independent:
                observations[fixture["state"]]["identity"]["sequence"] = False
            else:
                expected["intent_revision"] = True
            with self.assertRaises(kit.ContractError):
                kit.assert_conforms(fixture, expected, fixture["state"], observations)
            result = mutant.assert_conforms(
                fixture, expected, fixture["state"], observations
            )
            self.assertTrue(result)
            with self.assertRaises(AssertionError):
                self.assertFalse(result, "malformed independent context falsely passed")


if __name__ == "__main__":
    unittest.main()
