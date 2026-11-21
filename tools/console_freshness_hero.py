#!/usr/bin/env python3
"""H09 component lane with the real pinned Console projection and scripted feeds."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "scenarios/console-freshness-v1.json"
COMPONENTS = {"browser", "console", "core", "host", "platform", "refinery", "tether"}

# The two ES modules run in the same context so the pinned projection's
# identity prototype checks see real objects from its own realm.
NODE_LOADER = r"""
import {readFileSync} from "node:fs";
import {SourceTextModule, createContext} from "node:vm";
const [projectionPath, fixturePath] = process.argv.slice(1);
const context = createContext({
  URL, AbortController, fixtureText: readFileSync(fixturePath, "utf8"),
}, {codeGeneration: {strings: false, wasm: false}});
const projection = new SourceTextModule(readFileSync(projectionPath, "utf8"), {context});
const driver = new SourceTextModule(DRIVER_SOURCE, {context});
try {
  await projection.link(() => { throw Error("unexpected Console import"); });
  await driver.link((name) => {
    if (name !== "projection") throw Error("unexpected harness import");
    return projection;
  });
  await driver.evaluate({timeout: 3000});
  console.log(driver.namespace.receipt);
} catch (error) {
  console.error(error.message);
  process.exitCode = 1;
}
"""

CONSOLE_DRIVER = r"""
import {createProjection} from "projection";
const fixture = JSON.parse(fixtureText);
const [a, b] = fixture.tasks;
const reads = [], views = [], closed = [];
let now = fixture.clock_ms;
function check(value, message) {
  if (!value) throw Error("H09: " + message);
}
function pending(log, fields) {
  return new Promise((resolve, reject) => log.push({...fields, resolve, reject}));
}
const projection = createProjection({
  clock: () => now,
  maxAgeMs: fixture.max_age_ms,
  allowedViewOrigins: [fixture.viewer_origin],
  readSnapshot: (identity, {signal}) => pending(reads, {identity, signal}),
  openPassive: (request, {signal}) => pending(views, {request, signal}),
});
const viewUrl = fixture.viewer_origin + "/synthetic";
function event(identity, revision, fields = {}) {
  return {
    version: 1, identity, revision, observedAt: now, connection: "online",
    authority: "human", label: "Synthetic observation", evidenceClass: "synthetic_component",
    simulated: true, viewUrl, ...fields,
  };
}
function handle(name) {
  return {close: () => closed.push(name)};
}
async function snapshot(observation) {
  const result = projection.refresh();
  reads.at(-1).resolve(observation);
  check(await result, "snapshot refused");
}
function visible(status, freshness) {
  const current = projection.state();
  check(current.status === status && current.freshness === freshness, "incorrect " + status);
  check(current.canExecute === false, "projection enabled control");
}

projection.select(a);
const oldTask = projection.refresh();
projection.select(b);
const oldRead = projection.refresh();
const currentRead = projection.refresh();
check(reads[0].signal.aborted && reads[1].signal.aborted, "superseded reads not canceled");
reads[2].resolve(event(b, 4));
check(await currentRead, "current read refused");
reads[0].resolve(event(a, 50));
check(await oldTask === false, "old task response accepted");
reads[1].resolve(event(b, 5));
check(
  await oldRead === false && projection.state().record.revision === 4,
  "superseded snapshot overwrote the selection",
);
check(projection.state().identity.task === b.task, "selected task changed");
check(!projection.merge(event({...b, leaseEpoch: 1}, 5)), "wrong lease accepted");
check(!projection.merge(event(b, 4)), "duplicate revision accepted");
check(!projection.merge(event(b, 5, {observedAt: now - 1})), "older timestamp accepted");
check(!projection.merge(event(b, 5, {observedAt: undefined})), "absent timestamp accepted");
check(projection.merge(event(b, 5, {observedAt: null})), "unknown time rejected");
check(
  projection.state().status === "unknown" && projection.state().freshness === "unknown",
  "missing timestamp appeared current",
);
check(!await projection.view() && views.length === 0, "unknown observation opened a view");
check(projection.merge(event(b, 7)), "gap update refused");
check(projection.state().record.gap, "revision gap hidden");
visible("unknown", "fresh");
check(!await projection.view() && views.length === 0, "gap opened a view");
check(projection.merge(event(b, 8, {connection: "offline"})), "disconnect refused");
visible("offline", "fresh");
const outage = projection.refresh();
reads.at(-1).reject(Error("synthetic dependency timeout"));
check(!await outage, "failed refresh reported success");
visible("error", "fresh");
check(!await projection.view() && views.length === 0, "outage opened a view");

await snapshot(event(b, 9));
visible("ready", "fresh");
const canceledView = projection.view();
check(views.length === 1, "missing pending passive call");
projection.select(a);
views[0].resolve(handle("pending"));
check(views[0].signal.aborted && !await canceledView, "late view became active");
check(closed.join() === "pending", "late view leaked");

projection.select(b);
await snapshot(event(b, 10));
const activeView = projection.view();
check(views.length === 2, "missing passive call");
views[1].resolve(handle("offline"));
check(await activeView && !await projection.view(), "view duplicated");
check(projection.merge(event(b, 11, {connection: "offline"})), "second disconnect refused");
check(closed.join() === "pending,offline", "offline view leaked");
await snapshot(event(b, 12));
visible("ready", "fresh");
const afterReconnect = projection.state();
check(JSON.stringify(afterReconnect.identity) === JSON.stringify(b), "reconnect changed identity");
now += fixture.max_age_ms + 1;
visible("stale", "stale");
const afterExpiry = projection.state();
check(!await projection.view(), "expired observation opened a view");
for (const {request} of views) {
  check(
    Object.keys(request).sort().join() === "identity,mode,simulated,url" &&
    request.mode === "passive" && request.simulated === true && request.url === viewUrl &&
    JSON.stringify(request.identity) === JSON.stringify(b),
    "passive request changed",
  );
}
check(
  JSON.stringify(reads.map(({identity}) => identity)) ===
    JSON.stringify([a, ...Array(6).fill(b)]),
  "unexpected snapshot calls",
);
projection.dispose();
check(projection.state().identity === null, "disposal retained selection");
export const receipt = JSON.stringify({
  reads: reads.length, passive_calls: views.length, closed,
  current_after_reconnect: afterReconnect.identity.task,
  stale_after_expiry: afterExpiry.freshness === "stale",
  control_requests: views.filter(({request}) => request.mode !== "passive").length,
});
"""


def require(condition: object, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def git(directory: Path, *arguments: str) -> bytes:
    return subprocess.check_output(
        ["git", "-C", str(directory), *arguments], timeout=15
    )


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def pinned_projection(fixture: dict[str, Any]) -> tuple[bytes, dict[str, str], str]:
    lock = (ROOT / "composition.lock.json").read_bytes()
    entries = json.loads(lock)["components"]
    pins = {row["component"]: row["commit"] for row in entries}
    require(len(entries) == 7 and set(pins) == COMPONENTS, "invalid pin inventory")
    for name, revision in pins.items():
        path = "components/" + name
        require(
            git(ROOT, "ls-files", "--stage", "--", path).decode().strip()
            == f"160000 {revision} 0\t{path}",
            "composition gitlink mismatch",
        )
    console = ROOT / "components/console"
    require(
        git(console, "rev-parse", "--show-toplevel").decode().strip() == str(console)
        and git(console, "rev-parse", "HEAD").decode().strip()
        == pins["console"]
        == fixture["console_commit"]
        and not git(console, "status", "--porcelain"),
        "need the clean, pinned Console checkout",
    )
    source = git(console, "show", f"{pins['console']}:src/projection.js")
    require(
        sha(source) == fixture["projection_sha256"], "Console source digest mismatch"
    )
    return source, pins, sha(lock)


def invoke(
    directory: Path, source: bytes, fixture: bytes
) -> subprocess.CompletedProcess[str]:
    projection = directory / "projection.mjs"
    input_file = directory / "fixture.json"
    projection.write_bytes(source)
    input_file.write_bytes(fixture)
    loader = NODE_LOADER.replace("DRIVER_SOURCE", json.dumps(CONSOLE_DRIVER))
    environment = {
        key: value for key, value in os.environ.items() if not key.startswith("NODE_")
    }
    return subprocess.run(
        [
            "node",
            "--no-warnings",
            "--experimental-vm-modules",
            "--input-type=module",
            "-e",
            loader,
            str(projection),
            str(input_file),
        ],
        cwd=directory,
        env=environment,
        text=True,
        capture_output=True,
        timeout=12,
    )


def run() -> dict[str, Any]:
    raw = MANIFEST.read_bytes()
    fixture = json.loads(raw)
    require(
        fixture["version"] == "runspindle.console-freshness-hero.v1"
        and type(fixture["repeat_runs"]) is int
        and fixture["repeat_runs"] == 2,
        "unsupported H09 scenario",
    )
    source, pins, lock_digest = pinned_projection(fixture)
    with TemporaryDirectory(prefix="runspindle-h09-") as temporary:
        directory = Path(temporary)
        outputs = []
        for _ in range(fixture["repeat_runs"]):
            result = invoke(directory, source, raw)
            require(result.returncode == 0 and not result.stderr, result.stderr.strip())
            outputs.append(result.stdout)
        require(outputs[0] == outputs[1], "repeated projection observations differ")
        mutations = []
        for old, new, message in (
            (
                b"controller.signal.aborted || disposed || expectedGeneration !== generation || request !== latestRequest",
                b"disposed || expectedGeneration !== generation",
                "superseded snapshot overwrote the selection",
            ),
            (
                b"let freshness = 'unknown';",
                b"let freshness = 'fresh';",
                "missing timestamp appeared current",
            ),
        ):
            require(source.count(old) == 1, "mutation anchor drift")
            mutant = invoke(directory, source.replace(old, new), raw)
            require(
                mutant.returncode == 1 and mutant.stderr.strip() == "H09: " + message,
                "mutation did not reach its oracle: " + message,
            )
            mutations.append(message)
    return {
        "scenario": "H09",
        "console_lane": "passed",
        "live_stream_and_full_system": "blocked",
        "evidence_class": "pinned_component_with_scripted_snapshot_event_and_view_adapters",
        "composition_head": git(ROOT, "rev-parse", "HEAD").decode().strip(),
        "component_pins": pins,
        "lock_sha256": lock_digest,
        "fixture_sha256": sha(raw),
        "projection_sha256": sha(source),
        "node": subprocess.check_output(
            ["node", "--version"], timeout=10, text=True
        ).strip(),
        "observations": cast(dict[str, Any], json.loads(outputs[0])),
        "mutations_detected": mutations,
        "repeat_runs": len(outputs),
    }


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True))
