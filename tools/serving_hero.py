"""H11 on the reviewed Refinery pin, with a scripted model and approval source."""

from __future__ import annotations

import io
import json
import os
import platform
import shutil
import sqlite3
import subprocess
import sys
import tarfile
from contextlib import closing
from dataclasses import replace
from datetime import UTC, datetime
from importlib import import_module
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Callable

from tools.browser_effect_hero import canonical as _canonical
from tools.browser_effect_hero import git, require
from tools.browser_effect_hero import rows as _rows
from tools.browser_effect_hero import sha as _sha
from tools.maintained_scenarios import decode

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "scenarios/refinery-serving-recovery-v1.json"
FAULTS = ["forged_approval", "crash_after_load", "rejected_rollback"]
DECODE: Callable[[Any], Any] = decode
canonical: Callable[[object], bytes] = _canonical
rows: Callable[[Path, str], list[tuple[Any, ...]]] = _rows
sha: Callable[[bytes], str] = _sha
ACTOR = "synthetic-reviewer"
PROOF = "synthetic-approval-proof"


def stage_source(stage: Path, spec: dict[str, Any]) -> tuple[dict[str, str], str]:
    lock = json.loads((ROOT / "composition.lock.json").read_bytes())["components"]
    pins = {entry["component"]: entry["commit"] for entry in lock}
    require(
        len(lock) == 7
        and set(pins)
        == {"browser", "console", "core", "host", "platform", "refinery", "tether"},
        "invalid composition pin inventory",
    )
    for name, commit in pins.items():
        path = f"components/{name}"
        require(
            git(ROOT, "ls-files", "--stage", "--", path).decode().strip()
            == f"160000 {commit} 0\t{path}",
            "composition gitlink mismatch",
        )
    source = ROOT / "components/refinery"
    pin = pins["refinery"]
    require(pin == spec["refinery_commit"], "scenario Refinery pin mismatch")
    require(
        git(source, "rev-parse", "--show-toplevel").decode().strip() == str(source)
        and git(source, "rev-parse", "HEAD").decode().strip() == pin
        and not git(source, "status", "--porcelain"),
        "need the clean, pinned Refinery checkout",
    )
    tree = git(source, "rev-parse", f"{pin}:refinery").decode().strip()
    require(tree == spec["refinery_tree"], "Refinery source tree mismatch")
    fixtures = ("tests/test_durable.py", "tests/test_lineage.py")
    require(set(spec["fixture_sha256"]) == set(fixtures), "invalid fixture inventory")
    for path in fixtures:
        require(
            sha(git(source, "show", f"{pin}:{path}")) == spec["fixture_sha256"][path],
            "Refinery fixture digest mismatch",
        )
    archive = git(source, "archive", pin, "refinery", *fixtures)
    stage.mkdir()
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as unpack:
        unpack.extractall(stage, filter="data")
    return pins, sha(archive)


def program(answer: str) -> bytes:
    return canonical({"format": "synthetic.map.v1", "responses": {"hello": answer}})


def begin_candidates(
    store: Any, registry: Any, adapter: Any, spec: dict[str, Any]
) -> None:
    ev = import_module("refinery.evaluation")
    durable = import_module("refinery.durable_evaluation")
    serving = import_module("refinery.serving")
    version = import_module("refinery.storage").VERSION
    fixture = import_module("test_durable").setup
    clock = ev.VirtualClock()
    for index, answer in enumerate(spec["answers"]):
        name = f"candidate-{index}"
        content = program(answer)
        snapshot, experiment, provider = fixture(store, content=content, clock=clock)
        report = durable.run(
            store,
            version,
            name,
            snapshot,
            experiment,
            provider=provider,
            budget_id=spec["budget_id"],
            synthetic_fixture=True,
        )
        require(report.status == "passed", "scripted evaluation did not pass")
        key = registry.qualify(
            version, name, serving.Policy("local", 1_000_000, 0, 1000, 1000)
        )
        candidate = store.get("candidate", key)
        approval = serving.Approval(
            sha(content),
            candidate["evaluation_sha256"],
            candidate["policy_sha256"],
            "local",
            ACTOR,
            PROOF,
        )
        if index == 1:
            deny_forged(registry, version, key, approval)
        registry.begin(version, name, key, approval, expected_generation=index)
        checkpoint = crash_after_load if index == 1 else lambda _: None
        require(
            registry.load(version, name, adapter, checkpoint=checkpoint) == "active",
            "initial activation failed",
        )


def deny_forged(registry: Any, version: str, key: str, approval: Any) -> None:
    try:
        registry.begin(
            version,
            "forged",
            key,
            replace(approval, evidence="forged"),
            expected_generation=1,
        )
    except ValueError as exc:
        require(str(exc) == "approval denied", "unexpected forged approval result")
        return
    raise AssertionError("forged approval reached registry")


def crash_after_load(point: str) -> None:
    if point == "after_candidate_load":
        os._exit(93)


class RejectLoad:
    """A synthetic pre-effect rejection using the real adapter for readback."""

    def __init__(self, adapter: Any, evidence: Path) -> None:
        self.adapter = adapter
        self.evidence = evidence

    def load(
        self,
        activation: str,
        environment: str,
        generation: int,
        digest: str,
        content: bytes,
        predecessor: str | None,
    ) -> bool:
        # Record the actual attempted boundary independently of the registry outcome.
        request = [
            activation,
            environment,
            generation,
            digest,
            sha(content),
            predecessor,
        ]
        with self.evidence.open("xb") as call:
            call.write(canonical(request))
        return False

    def readback(self, environment: str) -> Any:
        return self.adapter.readback(environment)


def worker(source: Path, data: Path, mode: str) -> None:
    def audit(event: str, _: tuple[object, ...]) -> None:
        if event.startswith("socket.") or event in {
            "subprocess.Popen",
            "os.system",
            "os.posix_spawn",
            "os.exec",
            "os.fork",
        }:
            (data / "forbidden").write_text("forbidden effect")
            raise AssertionError("forbidden external effect")

    sys.addaudithook(audit)
    sys.path[:0] = [str(source), str(source / "tests")]
    spec = json.loads(MANIFEST.read_bytes())
    serving = import_module("refinery.serving")
    storage = import_module("refinery.storage")
    version = storage.VERSION
    approved_digests = {sha(program(answer)) for answer in spec["answers"]}

    def verify(approval: Any) -> str | None:
        if (approval.actor, approval.environment, approval.evidence) == (
            ACTOR,
            "local",
            PROOF,
        ):
            if approval.candidate_sha256 in approved_digests:
                return ACTOR
        return None

    with (
        storage.Store(data / "refinery.sqlite") as store,
        closing(serving.LocalServing(data / "serving.sqlite")) as adapter,
    ):
        registry = serving.Registry(store, verify_approval=verify)
        if mode == "start":
            begin_candidates(store, registry, adapter, spec)
            raise AssertionError("worker did not interrupt after load")
        if mode == "recover":
            require(
                registry.load(version, "candidate-1", adapter) == "active",
                "exact readback did not settle the interrupted activation",
            )
        elif mode == "reject":
            registry.rollback(
                version, "rejected-rollback", "local", expected_generation=2
            )
            rejected = RejectLoad(adapter, data / "rejected")
            require(
                registry.load(version, "rejected-rollback", rejected) == "failed",
                "confirmed loader rejection did not preserve prior selection",
            )
        elif mode == "rollback":
            registry.rollback(version, "rollback", "local", expected_generation=3)
            require(
                registry.load(version, "rollback", adapter) == "active",
                "rollback failed",
            )
        else:
            raise AssertionError("unknown worker mode")
        print(json.dumps(adapter.predict("local", "hello"), sort_keys=True))


def invoke(source: Path, data: Path, mode: str, code: int = 0) -> Any:
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-S",
            "-B",
            *("-O" for _ in range(sys.flags.optimize)),
            "-c",
            "import sys; sys.path.insert(0, sys.argv.pop(1)); "
            "from tools.serving_hero import worker; from pathlib import Path; "
            "worker(Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3])",
            str(ROOT),
            str(source),
            str(data),
            mode,
        ],
        cwd=data,
        capture_output=True,
        text=True,
        timeout=25,
    )
    require(
        result.returncode == code
        and not result.stderr
        and not (data / "forbidden").exists(),
        "serving worker failed: " + mode,
    )
    if code:
        require(not result.stdout, "interrupted worker returned an outcome")
        return None
    return json.loads(result.stdout)


def selected(data: Path, activation: str, generation: int, answer: str) -> str:
    expected = program(answer)
    digest = sha(expected)
    require(
        rows(
            data / "serving.sqlite",
            "SELECT activation,generation,digest,content FROM active",
        )
        == [(activation, generation, digest, expected)],
        "independent serving version or bytes mismatch",
    )
    return digest


def registry_rows(data: Path) -> list[tuple[Any, ...]]:
    return rows(
        data / "refinery.sqlite",
        "SELECT identity,generation,state FROM activations ORDER BY generation",
    )


def loads(data: Path) -> list[tuple[Any, ...]]:
    return rows(
        data / "serving.sqlite",
        "SELECT activation,digest FROM calls WHERE action='load' ORDER BY id",
    )


def evaluation_readback(registry: Path, budget_id: str) -> dict[str, int]:
    require(
        rows(registry, "SELECT identity FROM budgets") == [(budget_id,)],
        "evaluation stages did not retain one shared budget",
    )
    attempts = rows(
        registry,
        "SELECT experiment,ticket,request,outcome,receipt FROM attempts ORDER BY ticket",
    )
    cohorts: dict[tuple[str, str], list[tuple[str, str]]] = {}
    for expected, (experiment, ticket, request, outcome, receipt) in enumerate(
        attempts, 1
    ):
        require(
            ticket == expected and outcome == "settled" and receipt is not None,
            "evaluation tickets were not globally consecutive and settled",
        )
        item = DECODE(json.loads(request))
        cohorts.setdefault((experiment, item["stage"]), []).append(
            (item["output_id"], item["output_revision"]),
        )
    expected_cohort = cohorts.get(("candidate-0", "baseline"))
    require(
        set(cohorts)
        == {
            (experiment, stage)
            for experiment in ("candidate-0", "candidate-1")
            for stage in ("baseline", "candidate")
        }
        and bool(expected_cohort)
        and all(cohort == expected_cohort for cohort in cohorts.values()),
        "heldout identities were not paired across both evaluations",
    )
    return {
        "global_budget_attempts": len(attempts),
        "heldout_cases": len(expected_cohort or ()),
    }


def run_case(source: Path, data: Path, spec: dict[str, Any]) -> dict[str, Any]:
    data.mkdir()
    first_answer, second_answer = spec["answers"]
    invoke(source, data, "start", 93)
    first = sha(program(first_answer))
    second = selected(data, "candidate-1", 2, second_answer)
    calls = [("candidate-0", first), ("candidate-1", second)]
    initial = [("candidate-0", 1, "active"), ("candidate-1", 2, "unknown")]
    require(
        registry_rows(data) == initial and loads(data) == calls,
        "activation reservation or independent effect count mismatch",
    )
    require(
        rows(data / "refinery.sqlite", "SELECT pending FROM environments")
        == [("candidate-1",)],
        "missing interrupted activation intent",
    )
    current = {"candidate_sha256": second, "output": second_answer}
    require(
        invoke(source, data, "recover") == current,
        "historical output attribution mismatch",
    )
    active = [initial[0], ("candidate-1", 2, "active")]
    require(
        registry_rows(data) == active and loads(data) == calls,
        "missing exact registry readback or duplicate load",
    )
    require(
        invoke(source, data, "reject") == current,
        "rejected rollback changed the output",
    )
    selected(data, "candidate-1", 2, second_answer)
    require(
        json.loads((data / "rejected").read_bytes())
        == ["rejected-rollback", "local", 3, first, first, second],
        "incorrect rejected rollback attempt",
    )
    after_rejection = [*active, ("rejected-rollback", 3, "failed")]
    require(
        registry_rows(data) == after_rejection and loads(data) == calls,
        "rejected rollback changed the recorded serving effect",
    )
    rolled = invoke(source, data, "rollback")
    require(
        rolled == {"candidate_sha256": first, "output": first_answer},
        "rolled back output attribution mismatch",
    )
    selected(data, "rollback", 4, first_answer)
    require(
        registry_rows(data) == [*after_rejection, ("rollback", 4, "active")]
        and loads(data) == [*calls, ("rollback", first)],
        "wrong final registry or serving effect history",
    )
    return {
        "load_order": [row[0] for row in loads(data)],
        "historical": current,
        "rollback": rolled,
        **evaluation_readback(data / "refinery.sqlite", spec["budget_id"]),
        "forged_approval_loads": 0,
        "rejected_rollback_loads": 0,
    }


def mutation(source: Path, scratch: Path, spec: dict[str, Any]) -> None:
    modified = scratch / "mutant"
    shutil.copytree(source, modified)
    implementation = modified / "refinery/serving.py"
    original = implementation.read_text()
    anchor = 'if state != "intent":\n            return self.reconcile(api_version, activation_id, adapter)'
    require(original.count(anchor) == 1, "serving mutation anchor changed")
    implementation.write_text(
        original.replace(anchor, 'if state != "intent":\n            return "active"')
    )
    try:
        run_case(modified, scratch / "mutant-case", spec)
    except AssertionError as exc:
        require(
            str(exc) == "missing exact registry readback or duplicate load",
            "serving mutation did not fail at independent readback",
        )
        return
    raise AssertionError("serving acknowledgement mutation escaped detection")


def run() -> dict[str, Any]:
    raw = MANIFEST.read_bytes()
    spec = json.loads(raw)
    require(
        spec["version"] == "runspindle.refinery-serving-recovery.v1"
        and spec["faults"] == FAULTS
        and spec["repeat_runs"] == 2,
        "unsupported H11 scenario",
    )
    with TemporaryDirectory(prefix="runspindle-h11-") as root:
        scratch = Path(root).resolve()
        source = scratch / "source"
        pins, archive_sha = stage_source(source, spec)
        repeats = [run_case(source, scratch / str(index), spec) for index in range(2)]
        require(repeats[0] == repeats[1], "H11 repeat observations changed")
        mutation(source, scratch, spec)
        return {
            "scenario": "H11",
            "refinery_lane": "passed",
            "serving": "pinned_local_sqlite",
            "provider": "scripted",
            "approval": "synthetic",
            "dspy": "not_run",
            "live_acceptance": "not_run",
            "full_system": "blocked",
            "composition_head": git(ROOT, "rev-parse", "HEAD").decode().strip(),
            "component_pins": pins,
            "source_archive_sha256": archive_sha,
            "fixture_sha256": spec["fixture_sha256"],
            "lock_sha256": sha((ROOT / "composition.lock.json").read_bytes()),
            "manifest_sha256": sha(raw),
            "python": platform.python_version(),
            "sqlite": sqlite3.sqlite_version,
            "timestamp_utc": datetime.now(UTC).isoformat(),
            "repeat_runs": len(repeats),
            "observed": repeats[0],
            "mutations_detected": ["false_acknowledgement"],
        }


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True))
