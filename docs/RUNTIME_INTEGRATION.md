# H02 and H07 composition lanes

These are two independently runnable isolated development lanes:

- H02: real core, immutable pinned Rust host library and pinned Temporal; scripted
  native peer. No native app-server wire compatibility is claimed.
- H07: real core SQLite artifact acceptance/outbox and pinned Temporal; scripted
  destination. Tether's real source/transport remains a separate blocker.

The reviewed `runspindle.integration.v1` extension leaves Runtime v1 and the
synthetic fixture format unchanged. Component gitlinks/lock entries and core's
host library Cargo revision must agree. Preparation pins exact dependencies,
bundled SQLite bytes, notices, toolchain, source, executable and image. Missing
or mismatching preparation blocks a lane; no service/runner is substituted.
Use the reviewed `delivery-runtime` prepared artifact matching
`components/core/docs/runtime-build.json`. Explicit acquisition/build is
`python3 components/core/tools/prepare_temporal_runtime.py --acquire --features delivery-runtime`.
It produces a candidate; a different image/build record needs separate
qualification and must not silently replace the committed record.

```sh
python3 tools/check_library_pins.py
python3 tools/runtime_integration_scenario.py --lane H02 \
  --platform-prepared /path/to/verified/platform-prepared \
  --core-prepared /path/to/verified/core-prepared --report local/H02.json
python3 tools/runtime_integration_scenario.py --lane H07 \
  --platform-prepared /path/to/verified/platform-prepared \
  --core-prepared /path/to/verified/core-prepared --report local/H07.json
```

Each command deliberately exits **78** when its isolated lane passes but the
system aggregate remains blocked. Consult `lane_status` separately from
`aggregate`. Unexpected executed-command/assertion failures exit 1. Unavailable
prerequisites never become successful acceptance.

Composition loads exact pinned Python source without bytecode caches, invokes
the pinned component controllers and supplies its own read-only observer before
scratch cleanup. The observer opens independent native/destination SQLite ledgers
and the real coordinator stores directly. It checks exact operation/host/session
bindings, observed sequences/outcomes, call count/order, cancellation/completion
race receipts, actual byte SHA-256, immutable validation/acceptance, stable target,
no resend after reservation, and retained receipt-conflict fences. Component
coordinator status alone cannot pass these oracles. Component tests additionally
cover concurrent owners, stale/future observations, ambiguity, default denial,
capacity and malformed/conflicting revisions.

Both lanes repeat the same seed twice and compare normalized independent outcomes.
Fresh processes cover host dispatch, validation/acceptance commits, delivery
reservation and lost acknowledgement; real Temporal server restarts retain its
actual database. History replay must leave external peer ledgers unchanged.
Core/host behavioral mutations demonstrate duplicate dispatch, session rebinding,
skipped validation, changed bytes and fabricated delivery receipts. Mutation build
targets are separate from qualification output and package-cleaned per mutation;
shared-target results were discarded and original code was rebuilt.

Before-send interruption remains Unknown with zero destination receipts; it is
not a successful delivery. A confirmed delivery later encountering a contradictory
receipt retains its earlier receipt and a persistent conflict fence. No automatic
resolution or resend is introduced. There is no provider-backed live test, native
qualification, production identity, credential, paid call, runner installation,
external posting or production activation. Browser/console/refinery/source-rights
work outside this tranche remains queued or blocked. The full-system and live
acceptance aggregate remains non-success.

## H07 Core–Tether delivery candidate

`H07.tether_delivery_and_resolution` exercises the actual Core outbox and
Tether wire and resolution journals with synthetic authority and an independent
SQLite-backed Slack HTTP fixture. It covers exact accepted bytes and destination,
lost completion and bridge acknowledgements, contradictory receipts, wrong
thread, revocation, a stale resolution or changed accepted bytes, and concurrent
resolution. The pinned Core tests reopen durable stores in new processes and
verify the fixture observes one allocation, one upload and one completion.
Six mutations of the independent expected request must fail before any
store or provider effect. The same cases run under normal and optimized Python.

The [lane manifest](../specs/tether-delivery-scenario-v1.json) names the first Core
merge with both wire delivery and explicit resolution. Its Rust source differs
from the source recorded in the existing prepared Temporal image. Keep the
candidate in a separate clean checkout to preserve H02 and H07's prepared runs.
The report binds the candidate, composition commit, all seven gitlinks, fixture
bytes, locked Cargo dependencies, and tool versions. It reports this lane
independently of the prepared Temporal and live Slack gates.

With a local clone of `newdarwindev/runspindle-core`, initialize composition's
submodules and create a detached candidate worktree at the manifest commit.
Use Python 3.11 or newer, Rust with the local locked dependency cache populated,
and a local protobuf compiler and matching includes. Run from the clean
composition checkout with a report path outside both checkouts.

```sh
python3 -m tools.tether_delivery_scenario \
  --core-source /path/to/core-candidate \
  --protoc /path/to/protobuf/bin/protoc \
  --protoc-include /path/to/protobuf/include \
  --report /path/to/scratch/h07-tether.json
```

Cargo runs locked and offline. The fixture denies Python socket creation.
The runner uses a disposable build and state directory and bounds subprocesses.
Read `lane_status` for the result. A passing lane produces exit 78 while the
combined system remains blocked. Failed execution produces exit 1.
