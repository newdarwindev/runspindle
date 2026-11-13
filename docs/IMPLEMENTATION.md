# Bounded implementation progress

The composition remains a scaffold, not an integrated or deployed system.
`composition.lock.json` and all seven gitlinks are advanced together only to
component commits merged after separate exact-head review and local checks.

## Implemented component slices

- **Core:** dependency-free process-local request/revision/host-pin and exact-reference
  artifact/delivery model. Twenty Rust tests include 97,655 action-prefix checks;
  three deliberate model mutations are detected. No durable outbox, real hashing,
  authentication, native launch or Temporal integration is implemented.
- **Refinery:** original bounded process-local immutable byte/hash lineage,
  attributable-feedback verifier seam, conflict quarantine and family-grouped
  locked split. The verifier defaults to deny; it is not an authentication system.
  No provider, durable store, evaluation, promotion or serving adapter is supplied.
- **Console:** original process-local identity/revision/freshness projection and
  cancellable read/passive-view controller, with no control grant. Fourteen Node
  tests and three detected mutations cover late replies, invalid identity, unknown
  timestamps and viewer invalidation. No rendered UI, actual desktop or authoritative
  backend is connected.

See the exact pinned component evidence in
[core](../components/core/docs/IMPLEMENTATION_EVIDENCE.md),
[refinery](../components/refinery/docs/IMPLEMENTATION_EVIDENCE.md) and
[console](../components/console/docs/IMPLEMENTATION_EVIDENCE.md). Component tests
exercise the actual bounded library code with synthetic inputs. They do not
qualify real upstream adapters or establish durable/restart guarantees.

## Shared synthetic fixture adoption

All seven components vendor their relevant immutable subset of the original
[test-only fixture kit](FIXTURE_KIT.md) from composition commit
`e8cd5779968fede213443db13a591c992cd0e183`. Each has a separate reviewed pin for
source commit, schema and origin/subset manifest digests. Consumers verify all
bytes before executing the exact verified Python source snapshot; unpinned
bytecode cannot substitute for it. Golden observations and negative identity,
version, epoch, receipt and digest vectors run without sibling services.

This establishes Python fixture-format conformance in each source repository,
not cross-language runtime wire compatibility. Host/browser runtime entrypoints
still fail closed; Tether/platform runtime adapters are not implemented. The
fixture schema remains provisional and is not the native app-server, vault,
viewer, telemetry or Temporal protocol.

## Verification and remaining gates

[composition-pin-checks.json](composition-pin-checks.json) records checks rerun
against the exact new pins, tool versions, source/config hashes and outcomes.
Local checks are separate from GitHub Actions, isolated integration and live
acceptance. The repositories expose no required branch status contexts; merges
use normal exact-head GitHub merges after independent review and required local
checks. No bypass or protection setting was used or changed.

No qualified isolated runner is visible; GitHub workflows remain unverified.
Wiring optional refinery behavior tests into CI was rejected because the connected
OAuth app lacks workflow scope; the optional workflow edit was removed without
credential changes. Existing self-hosted-only workflows and blocked acceptance
entrypoints are preserved.

Remaining gates include reviewed authenticated authority/identity/retention/store
interfaces, durable outbox/epoch fencing and fresh-process recovery; actual
native/browser/Tether/telemetry/serving adapters; pinned qualified upstreams and
licenses; rendered accessibility; system integration and distribution. Exact
private source/dependency and rights dispositions remain necessary for all full
selected-source lifts. No legacy archival, production activation or deployment
follows from the local synthetic results.
