import importlib.util
import json
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from typing import Any

PATH = Path(__file__).resolve().parents[1] / "tools/maintained_scenarios.py"
SPEC = importlib.util.spec_from_file_location("maintained_scenarios", PATH)
lane = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(lane)


def encoded(value: Any) -> bytes:
    def record(item: Any) -> Any:
        if isinstance(item, dict):
            return {"dict": {k: record(v) for k, v in item.items()}}
        if isinstance(item, tuple):
            return {"tuple": [record(v) for v in item]}
        return item

    return json.dumps(record(value)).encode()


def request(stage: str, artifact: str, output: str = "heldout") -> bytes:
    return encoded(
        {
            "stage": stage,
            "output_id": output,
            "output_revision": "1",
            "source_sha256": lane.sha(output.encode()),
            "artifact_sha256": artifact,
            "split_sha256": lane.sha(b"split"),
            "attempt": 1,
        }
    )


class MaintainedScenarioTests(unittest.TestCase):
    def test_unknown_version_rejects_before_component_lookup(self):
        with self.assertRaises(lane.Blocked):
            lane.inventory(
                {
                    "version": "future",
                    "sources": {},
                    "reviewed_composition_base": "a" * 40,
                },
                {},
            )

    def test_missing_database_readback_never_creates_evidence(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "missing.sqlite"
            with self.assertRaises(AssertionError):
                lane.rows(path, "SELECT 1")
            self.assertFalse(path.exists())

    def test_independent_decoder_rejects_unsupported_shapes(self):
        for value in ({"pickle": "unsafe"}, {"dict": {}, "unexpected": "x"}):
            with self.assertRaises(AssertionError):
                lane.decode(value)

    def fixture(self, directory: Path) -> dict[str, Any]:
        content = json.dumps(
            {"format": "synthetic.map.v1", "responses": {"hello": "first"}}
        ).encode()
        first, second = lane.sha(content), lane.sha(b"second")
        with closing(sqlite3.connect(directory / "refinery.sqlite")) as db:
            lineage = encoded(
                {
                    "dataset": {
                        "examples": tuple(
                            {
                                "source": {
                                    "family_id": name,
                                    "sha256": lane.sha(name.encode()),
                                },
                                "output": {"output_id": name, "revision": "1"},
                            }
                            for name in ("heldout", "train")
                        )
                    },
                    "split": {
                        "assignments": (("heldout", "heldout"), ("train", "train")),
                        "sha256": lane.sha(b"split"),
                    },
                }
            )
            db.execute(
                "CREATE TABLE objects(kind TEXT,identity TEXT,digest TEXT,payload BLOB)"
            )
            db.execute(
                "INSERT INTO objects VALUES('lineage',?,?,?)",
                (lane.sha(lineage), lane.sha(lineage), lineage),
            )
            db.execute(
                "CREATE TABLE attempts(request BLOB,outcome TEXT,receipt BLOB,experiment TEXT,ticket INTEGER)"
            )
            for experiment, candidate in (
                ("candidate-0", first),
                ("candidate-1", second),
            ):
                db.executemany(
                    "INSERT INTO attempts VALUES(?,'settled',?,?,?)",
                    [
                        (
                            request("baseline", lane.sha(b"baseline")),
                            b"receipt",
                            experiment,
                            0,
                        ),
                        (request("candidate", candidate), b"receipt", experiment, 1),
                    ],
                )
            db.execute("CREATE TABLE activations(state TEXT,generation INTEGER)")
            db.executemany(
                "INSERT INTO activations VALUES('active',?)", [(1,), (2,), (3,)]
            )
            db.commit()
        with closing(sqlite3.connect(directory / "serving.sqlite")) as db:
            db.execute(
                "CREATE TABLE calls(id INTEGER,action TEXT,activation TEXT,digest TEXT)"
            )
            db.executemany(
                "INSERT INTO calls VALUES(?,'load',?,?)",
                [
                    (1, "candidate-0", first),
                    (2, "candidate-1", second),
                    (3, "rollback", first),
                ],
            )
            db.execute(
                "CREATE TABLE active(environment TEXT,activation TEXT,generation INTEGER,digest TEXT,content BLOB)"
            )
            db.execute(
                "INSERT INTO active VALUES('local','rollback',3,?,?)", (first, content)
            )
            db.commit()
        return {
            "rolled_output": {"output": "first", "candidate_sha256": first},
            "second_output": {"output": "second", "candidate_sha256": second},
        }

    def test_serving_observer_uses_actual_bytes_and_call_order(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            result = self.fixture(directory)
            self.assertEqual(
                lane.observe_serving(directory, result)["load_order"],
                ["candidate-0", "candidate-1", "rollback"],
            )
            result["rolled_output"]["candidate_sha256"] = "0" * 64
            with self.assertRaisesRegex(AssertionError, "attribution"):
                lane.observe_serving(directory, result)

    def test_duplicate_load_unknown_attempt_and_wrong_heldout_are_not_success(self):
        for mutation in ("duplicate", "unknown", "heldout"):
            with (
                self.subTest(mutation=mutation),
                tempfile.TemporaryDirectory() as temporary,
            ):
                directory = Path(temporary)
                result = self.fixture(directory)
                if mutation == "duplicate":
                    with closing(sqlite3.connect(directory / "serving.sqlite")) as db:
                        db.execute(
                            "INSERT INTO calls SELECT 4,action,activation,digest FROM calls WHERE id=2"
                        )
                        db.commit()
                else:
                    with closing(sqlite3.connect(directory / "refinery.sqlite")) as db:
                        if mutation == "unknown":
                            db.execute(
                                "UPDATE attempts SET outcome='unknown' WHERE ticket=0"
                            )
                        else:
                            db.execute(
                                "UPDATE attempts SET request=? WHERE ticket=1",
                                (
                                    encoded(
                                        {
                                            "output_id": "wrong",
                                            "output_revision": "1",
                                            "stage": "candidate",
                                        }
                                    ),
                                ),
                            )
                        db.commit()
                with self.assertRaises(AssertionError):
                    lane.observe_serving(directory, result)

    def test_globally_matched_rows_cannot_hide_incomplete_experiments(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            result = self.fixture(directory)
            with closing(sqlite3.connect(directory / "refinery.sqlite")) as db, db:
                db.execute(
                    "DELETE FROM attempts WHERE (experiment='candidate-0' AND ticket=1) "
                    "OR (experiment='candidate-1' AND ticket=0)"
                )
            with self.assertRaisesRegex(AssertionError, "heldout"):
                lane.observe_serving(directory, result)

    def test_matching_training_rows_or_wrong_candidate_bytes_cannot_pass(self) -> None:
        for mutation in ("train", "wrong-artifact"):
            with (
                self.subTest(mutation=mutation),
                tempfile.TemporaryDirectory() as temporary,
            ):
                directory = Path(temporary)
                result = self.fixture(directory)
                with closing(sqlite3.connect(directory / "refinery.sqlite")) as db, db:
                    for raw, rowid in db.execute(
                        "SELECT request,rowid FROM attempts"
                    ).fetchall():
                        value = lane.decode(json.loads(raw))
                        if mutation == "train":
                            value["output_id"] = "train"
                            value["source_sha256"] = lane.sha(b"train")
                        elif value["stage"] == "candidate":
                            value["artifact_sha256"] = lane.sha(b"wrong")
                        db.execute(
                            "UPDATE attempts SET request=? WHERE rowid=?",
                            (encoded(value), rowid),
                        )
                with self.assertRaisesRegex(AssertionError, "heldout"):
                    lane.observe_serving(directory, result)

    def test_required_review_and_external_gates_remain_non_success(self):
        self.assertEqual(
            lane.GATES["independent_final_head_review"],
            "user_waived_no_review_performed",
        )
        self.assertEqual(lane.GATES["Langfuse"], "blocked")
        self.assertEqual(lane.GATES["full_product_release"], "blocked")


if __name__ == "__main__":
    unittest.main()
