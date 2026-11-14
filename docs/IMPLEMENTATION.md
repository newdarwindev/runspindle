# Bounded implementation progress

The composition remains an undeployed development boundary. Component code,
isolated development integration and full-system acceptance are separate evidence.
The [runtime.v1 contract](../specs/runtime-v1.md) is specified independently of the
[test-only fixture format](FIXTURE_KIT.md). No operational acceptance gate is
changed to unconditional success.

## Component slices

- **Core:** bounded Temporal admission now has a separately versioned real host
  library lane pinned to host `6caf08d3`, with complete bindings, native observation
  sequences/freshness, unknown outcomes and accepted cancellation intent. A separate
  core-owned SQLite store retains immutable actual artifact bytes and validation/
  acceptance references; a transactional single-send outbox reconciles exact
  destination receipts and durably fences contradictions. Forty-eight Rust and
  sixteen Python tests, strict Clippy/formatting and isolated behavioral mutations
  pass. H02/H07 each pass twice on the exact prepared binary; the original scripted
  core remains a separate regression suite. Native/provider/Tether, production
  authority, browser fencing and full-system/live acceptance remain unqualified.
- **Host:** the real Rust lifecycle adapter supports Memory and bounded SQLite
  storage with transactional compare-and-swap ownership. Dispatch/cancel intent,
  complete bindings, native identity/sequences and pending receipts survive fresh
  processes; concurrent owners cannot duplicate launches. Twenty-seven Rust and
  seven Python tests plus duplicate-dispatch/session-rebinding behavioral mutations
  pass. Native app-server compatibility, capture/text transfer/submission, production
  authority and filesystem/power-loss durability remain blocked or unqualified.
- **Refinery:** immutable byte/hash lineage and family-locked splits feed an
  offline synthetic evaluator. One reservation/settlement budget covers all
  baseline/candidate stages and retries, including in-flight cancellation usage.
  Unknown safety/cost/usage, outstanding reservations, leakage, empty evaluation
  and malformed values cannot pass. Fifty-three Python tests and three detected
  implementation mutations run without real providers. DSPy/optimizer/provider
  compatibility, durable storage, approval, promotion and serving remain absent.
- **Platform:** official CLI 1.10.0 runs the embedded development server in a
  disposable isolated internal Docker network with no host gateway or published
  ports, UI disabled and one per-run SQLite volume. Killed-server restart reuses
  that volume. Preparation qualifies official source/archive/license bytes;
  runtime revalidates them and rebuilds the exact image offline before execution.
  Eighteen tests include five real lane cases and independent cleanup readback;
  two unsafe mutations are detected. Only Linux arm64 is exercised. Other upstream
  dependencies, telemetry privacy/readback, distribution and CI remain unqualified.
- **Console:** the previously pinned process-local identity/revision/freshness
  projection and passive-view controller remain synthetic component evidence.
  Actual rendered UI, accessibility and authoritative backend are not integrated.

Component changes merge in their own repositories first. A separate pin PR moves
all changed gitlinks and `composition.lock.json` together after independent review.
[Exact-pin checks](temporal-pin-checks.json) run in a clean isolated checkout;
unrelated runner-fleet changes in the original workspace are preserved/excluded.
See the [ledger](IMPLEMENTATION_LEDGER.md) and pinned component evidence for exact
reviewed heads, merge commits, commands, source hashes and remaining issue criteria.

## Shared fixture adoption and remaining gates

All seven components retain immutable relevant subsets of synthetic fixture commit
`e8cd5779968fede213443db13a591c992cd0e183`. Their Python consumers validate bytes
before executing exact verified source; untracked bytecode cannot replace it.
This proves fixture-format conformance, not runtime wire parity or authenticated
upstream compatibility. Browser and Tether runtime work remains queued.

The [real-core/real-Temporal composition scenario](CORE_TEMPORAL_SCENARIO.md)
passed two repeated development runs with matching normalized/source/toolchain/
fault-script hashes. The core and Temporal are real, host ports scripted; browser,
delivery, provider, console and refinery operations are not exercised.
Scripted sibling boundaries must be reported explicitly. It cannot establish
browser credential isolation/fencing, exact artifact delivery, telemetry readback,
candidate serving, all-component integration or live acceptance. Required
blocked/not-run gates aggregate to non-success even when the core lane passes.

GitHub Actions is unverified; no qualified isolated runner was established by this
tranche. Current rules/readbacks and local checks are recorded separately; no
protection bypass, runner provisioning or CI/credential expansion is performed.
Exact private source/dependency/rights dispositions remain required for full source
migration. No legacy archival, live provider calls, paid evaluation, external
posting or production activation follows from local synthetic/development results.

## Historical H02/H07 tranche

[Runtime integration v1](../specs/runtime-integration-v1.md) and
[composition verification](RUNTIME_INTEGRATION.md) qualify real core + pinned host
library + Temporal, and real artifact acceptance/outbox + Temporal, respectively.
Native and destination peers remain scripted. Composition-owned query-only
observers directly read independent peer ledgers and coordinator stores; they
check call order/counts, observed identity/outcomes, actual byte digests and
persistent conflict fences. Both lanes pass two seeded runs with matching
normalized outcomes; both system aggregates remain blocked. See
[H02 evidence](H02-integration-evidence.json), [H07 evidence](H07-integration-evidence.json)
and [review/merge evidence](runtime-integration-pin-evidence.json).

Platform PR8 merged readiness preparation separately; the composition platform
pin stays `96eb567`. No runners or services were installed. The structural-only
contracts CI remains unchanged after the existing OAuth workflow-scope limitation;
`tools/check_library_pins.py` is a separate fail-closed local/runtime prerequisite.
Remote CI and live acceptance remain unverified/not run. Source/rights dependency
closure and native-produced artifact provenance remain explicit gaps; no issue or
legacy repository was closed or archived by these bounded offline lanes.

## Qualified offline development subset

[Maintained workflow qualification](MAINTAINED_OFFLINE.md) now reconciles current
Strix/CI mains and pins exact merged core, refinery and platform revisions. A
separately versioned streaming bundle installs and executes core/Temporal,
refinery/DSPy and platform helpers offline, with independent byte/history/SQL
observations and fresh-process upgrade/rollback recovery. Existing JSON metadata
validation remains intact. [Final evidence](offline-finish-evidence.json) and the
[240-criterion audit](offline-issue-audit.json) distinguish these bounded results
from full-system acceptance.

Independent review was user-waived for this tranche; no review occurred. H08
remains blocked on original dependency notice closure, MinIO build, remaining
Langfuse inventories and actual API readback. Native/Tether prerequisites and
browser/console/visual/provider/paid/source-migration/production deferrals remain.
No issues or legacy repositories were closed or archived. The unrelated platform
checkout was preserved. [Runnable bundle instructions](OFFLINE_BUNDLE.md) describe
the exact disposable development scope and the saved offline launcher.
