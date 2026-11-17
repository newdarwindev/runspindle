# Shared isolation fixture acceptance

This audit addresses composition issue #1's **synthetic contract and reusable test-kit** scope. It does not qualify runtime protocols, production, source migration, native runners or live providers. Original synthetic fixtures retain their provenance and rights notices. No workflow, standing job, credential, security setting or runtime component pin changes.

## Exact sources and reproduction

Source bundle: `e283957d80aebc48fb0bd3b6e2a600850ff6dc97`.
`fixtures/consumer-lock.json` records seven merged consumer commits, Git trees and every isolated input's SHA-256. It is independent of `composition.lock.json`, whose runtime pins remain unchanged. `docs/shared-fixture-consumer-evidence.json` records actual UTC execution times, Python version, tool/lock hashes, four runs per consumer and bounded evidence class.

Prerequisites: Python 3.12, Git, Linux/POSIX for the graceful cancellation test; no packages or live services. Prepare the exact seven commits from the lock as local checkouts. Write a local JSON object mapping the seven component names to those checkout paths. The matrix does not fetch, authenticate or install anything:

```sh
python3 -B tools/qualify_fixture_consumers.py --checkouts /path/to/checkouts.json
python3 -B -m unittest discover -s tests -p 'test_fixture*.py'
python3 -O -B -m unittest discover -s tests -p 'test_fixture*.py'
python3 tools/check_scaffold.py
```

Each component can run its own suite without any sibling or composition checkout:

```sh
python3 -B -m unittest discover -s tests -p 'test_shared*fixture*.py'
python3 -O -B -m unittest discover -s tests -p 'test_shared*fixture*.py'
```

The composition matrix verifies committed blobs before copying only the fixture subset, two focused test files and required standalone helper into a disposable directory. There are no runtime modules, sibling checkouts or services there. Python socket creation, connection and DNS are denied; any attempted call is logged and causes matrix failure even if caught by a test. This is an instrumented trusted-Python test lane, not an OS sandbox for hostile code. Processes are bounded at 60 seconds; zero tests, skipped tests, nonzero exits and incomplete cleanup reject. Normal and optimized mode each run twice with seed `90210`. Source drift, omitted tests and rehashed uncommitted changes reject before execution.

## Criterion-by-criterion evidence

| Requirement | Implementation and direct verification | Outcome |
|---|---|---|
| Producer/consumer boundary inventory | `FIXTURE_KIT.md` boundary table covers admission, native launch/reconnect/cancel observation, browser account/origin/lease/handoff observation, sanitized event, artifact, telemetry, feedback/evaluation/serving. Unsupported request shapes remain explicitly provisional, not invented protocol claims. | passed, fixture scope |
| Versioned envelopes and applicability | `fixtures/v1/contract.json`, strict `fixturekit.py` validator, required/kind-specific identity and detail fields; unknown keys/version/events, invalid combinations, Boolean/float counters rejected. `test_fixturekit.py` and `test_fixture_oracle_context.py`. | passed |
| Golden and adversarial conformance vectors | `golden.json`, `vectors.json`, actual `artifact.txt`, provenance and manifest. Independent expected identities/state/receipts; changed digest, fabricated delivery, stale epoch and unknown outcome reject. | passed |
| Injectable seams and fault schedules | Seeded IDs, virtual clock, allowlisted spy, temporary store, seven fault schedules. Root and consumer tiny models execute duplicate/reorder/timeout/partial/retry/restart/uncertain schedules. Restart observation is explicitly blocked pending a durable adapter. | passed as test infrastructure; durable recovery not claimed |
| Independent assertions and negative mutations | Per-step state/count/attempt/sequence, ordered actual effect calls and actual call identity checked against declarative oracle. Duplicate send, stale overwrite, unauthorized retry, reordered observations, altered identity and oracle-type mutants reject. | passed |
| Isolated consumer pins and reviewed upgrades | Seven exact commits in consumer lock; byte-identical relevant exports from reviewed source. Each consumer retains compatibility byte/metadata diff and observed old/new golden/invalid decisions in `docs/shared-fixture-compatibility.json`. Older malformed float oracle counters accepted before and rejected now, unchanged valid golden accepted by both. | passed |
| Repeated deterministic output | Root repeated byte-identical export tests; seeded clock/IDs; each consumer run four times with stable inventory. Compatibility diff determinism is directly asserted. | passed |
| Isolation, cleanup and failure classification | No network calls in copied-only matrix; per-case state reset; normal/error/partial-export cancellation and graceful SIGTERM cleanup tests. Missing prerequisites fail/not-run, never success; status aggregation remains fail closed. SIGKILL/power-loss durability outside helper promise. | passed within documented lane |
| Structural and evidence checks | Exact source manifest, all input hashes, committed bytes, complete test inventory, trace labels and UTC evidence; scaffold and selected static checks. No operational gate weakened. | see recorded final verification |

## Merged consumers

| Component | PR | Tests per isolated run (four runs) |
|---|---|---:|
| Core | runspindle-core #35 | 13 |
| Host | runspindle-host #27 | 9 |
| Browser | runspindle-browser #50 | 9 |
| Tether | runspindle-tether #43 | 8 |
| Refinery | runspindle-refinery #52 | 13 |
| Console | runspindle-console #31 | 9 |
| Platform | runspindle-platform #47 | 8 |

The shared fixture prerequisite is separate from broader component quality. Prior consumer full suites passed individually (Core 110; Host 108; Browser 486; Tether 441 with one optional skip; Refinery 456; Console 118 Python plus 89 Node; Platform 447 with 13 pre-existing skips). Those runs used their documented prerequisites and are **not** the isolated matrix. Required broad aggregates remained failed for documented static/runtime prerequisite checks. This report does not relabel them green or replace historical evidence.

## Remaining production decisions, not fixture acceptance

| Gate | Further mockable evidence | Real prerequisite / current status |
|---|---|---|
| Runtime interoperability and durable restart | Additional state-machine/fault mutations using this kit | Exact runtime adapters, durable store/fresh-process recovery and composition pin qualification; not established here |
| Native runner qualification | Capability-denial, cancellation and identity models | Actual supported native runtime/OS, prepared runner and measured lifecycle; not run here |
| Tether deletion actor | Provider tombstone invalidation and fail-closed provenance models | Verified actual deleter attribution; Slack `message_deleted` does not supply it. Installation user or original author is not a substitute. Tether #8 remains open |
| Live provider and upstream compatibility | Typed replay of signed fixtures and failure decisions | Explicit supported upstream pins, authorized real account/provider lane and real receipts; provisional/not run |

Completion of this fixture issue grants no broader production acceptance. Historical evidence remains historical; later runtime changes must earn fresh exact-source qualification.
