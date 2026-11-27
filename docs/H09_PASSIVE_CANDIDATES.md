# H09 passive Core and Browser candidate replay

This scenario runs the actual Core passive readback and Browser passive peer
together at exact candidate revisions. It verifies the app-facing contract
using a synthetic selection coordinator and two separate read grants.
[H09](https://github.com/newdarwindev/runspindle/issues/16),
[real adapter rollout](https://github.com/newdarwindev/runspindle/issues/45),
[Core candidate](https://github.com/newdarwindev/runspindle-core/pull/76),
[Browser candidate](https://github.com/newdarwindev/runspindle-browser/pull/82).

| Boundary | Exercise |
| --- | --- |
| Core | `BrowserRegistry::passive_control_status` over its true SQLite control history, opened in a fresh process each time |
| Browser | `PassivePeer.observe` over explicitly scripted admissions and physical observations, in a fresh isolated Python process |
| Native fence and reconciliation | A scripted peer during setup records exactly one dispatch and one separate readback |
| Selection coordinator | The test harness joins Core and Browser receipts by exact selection and independently computed scope |
| Console, Host, Platform, Refinery, Tether and external providers | Synthetic boundaries with zero runtime calls |

The [fixed schedule](../scenarios/h09-passive-candidates-v1.json) starts with
a reserved Core head and a recent Browser observation. The head has no holder
until the scripted reconciliation confirms it. After a task change, the
coordinator discards a late response for the previous selection. It also
discards a captured older Core generation for the current task and a Browser
response older than the current observation. Duplicate samples leave the
displayed view intact.

A stale Core grant leaves the view unknown. Missing, stale, future and
wrong-account Browser observations and an expired passive grant leave only
retained Core metadata. A later observation in a fresh process restores the
physical timestamp. The harness keeps that timestamp distinct from the
Core state. It does not infer current control from either receipt.

After each passive step, the parent checks SQLite rows, schema, database
bytes, and the separately recorded native calls. The Browser worker audits
unexpected subprocess, socket and SQLite connection attempts. A temporary
Browser source mutation removes its physical scope check. The independent
wrong-account case must reject the mutant.

## Local invocation

Use Python 3.12 or later, Rust, Protobuf `protoc`, and an already prepared
offline Cargo cache for the exact Core lockfile. Check out the Core and
Browser revisions named in the fixture into separate local directories.

```sh
python3 tools/h09_passive_candidates.py --core /path/to/core --browser /path/to/browser
python3 -O tools/h09_passive_candidates.py --core /path/to/core --browser /path/to/browser
```

Use `--target-dir` to reuse a prepared local Cargo build directory. The harness
builds the worker with Cargo's locked offline mode and gives each child a
deadline. It stages source from Git objects, uses temporary stores, and
compares normalized receipts from two independent runs. The JSON report
includes all composition gitlinks and their lock digest, candidate source
archives, the Core dependency lock, harness and fixture hashes, toolchain
versions, and per-case observations. The candidate revisions do not change
the seven composition gitlinks.

The system aggregate remains blocked. The exact candidate pair provides
offline evidence for the passive seam. Actual desktop streaming, a real
Console client, authenticated native adapters, and full integration at the
composition gitlinks still require separate verification.
