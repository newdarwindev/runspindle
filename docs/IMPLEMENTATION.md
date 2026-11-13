# Bounded implementation progress

The composition remains an undeployed development boundary. Component code,
isolated development integration and full-system acceptance are separate evidence.
The [runtime.v1 contract](../specs/runtime-v1.md) is specified independently of the
[test-only fixture format](FIXTURE_KIT.md). No operational acceptance gate is
changed to unconditional success.

## Component slices

- **Core:** Rust SDK 1.2.0 implements a durable bounded admission-registry workflow,
  deterministic child operations, explicit revisions, injected default-deny grants
  and uncertain-effect reconciliation without blind activity retry. The registry
  retains at most 1,024 deliveries/revisions without eviction and assumes one
  registry authority per Temporal namespace. Twenty-seven Rust and eleven Python
  tests, strict offline Clippy/formatting, three registry-code mutations and a real
  development lane exercise fresh worker/server recovery, revoked authority,
  cancellation races and four history replays. Native freshness/wire qualification,
  browser-side fencing and production durability remain blocked. The process-local
  artifact model does not implement real validation/acceptance/delivery adapters.
- **Host:** transport-independent bounded Rust lifecycle coordination preserves
  the selected host/workspace, operation/epoch and actual observed native session.
  Lost launch replies reconcile before further dispatch. Cancellation request,
  acknowledgement and observed terminal outcome remain distinct. Nineteen Rust
  and seven Python tests plus three deliberate mutations exercise scripted peers.
  This is process-local component evidence; native app-server/macOS/Linux protocol,
  durable host recovery, capture, text transfer and submission remain unqualified.
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

A real-core/real-Temporal composition scenario is a separate development lane.
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
