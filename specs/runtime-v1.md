# Runtime v1 development contract

Version: `runspindle.runtime.v1`. This original, bounded development contract
freezes the seams for core, host and offline refinery implementations. It is
separate from `runspindle.fixture.v1`, which remains a synthetic test format.
The [machine-readable descriptor](../contracts/runtime-v1.json) lists exact
field/state names. Native Rust/Python types may map to these semantics; a mapping
must document differences and cannot claim JSON wire conformance without tests.
An unknown version, missing binding or malformed value rejects before dispatch.
No native app-server, browser, provider or identity protocol is qualified here.

## Values and authority

Identifiers use ASCII `[A-Za-z0-9][A-Za-z0-9._:-]{0,127}`. Digests are SHA-256 of
exact bytes, encoded as 64 lowercase hexadecimal characters. Counters and revisions
are unsigned 64-bit integers; revision and lease epoch start at one. Booleans,
floats and overflow are invalid integer encodings. Null means unknown, never zero.
Only public synthetic references belong in histories; raw prompts, credentials,
account content and grants containing secrets are forbidden. `grant_ref` refers to
an injected verifier, which defaults to denial. A verifier must bind the complete
request, policy, operation and selected target before any effect. Tests may inject
synthetic grants. Admission does not itself authorize future operations. External
feedback, Temporal replay, session discovery and cancellation do not widen scope.

A Binding has `task_id`, `revision`, `operation_id`, `policy_revision`, `host_id`,
`workspace_id`, `lease_epoch`. An operation ID is immutable for an effect across
retries/reconnect. Browser account/origin/instance and artifact/candidate digests,
when used, are additional immutable operation target fields; they cannot be
inferred from a mutable URL or from user content. Missing target authority denies.
Epoch comparison in core is not proof that a browser/provider has fenced effects.

## Durable admission and revisions

Admission fields are listed in the descriptor, plus the version envelope. The
`(delivery_namespace, delivery_id)` key binds exactly one admitted request. The
`(task_id, revision)` key binds normalized digest, policy, explicit host/workspace
lease epoch and caller-provided initial `operation_id`. This operation ID must
be unique within a task revision and immutable for its initial effect; a different
operation ID for an existing delivery/revision conflicts. Subsequent effects must
have distinct IDs with separately verified authority. Repeated identical delivery returns the original job binding;
a changed field conflicts. Another delivery of the same exact revision returns
the same job. No text similarity merges distinct task IDs.

The first revision is one with null predecessor. A new revision is exactly the
previous revision plus one and names it in `predecessor_revision`. It rejects
while its predecessor is active, including unknown effect and requested or merely
acknowledged cancellation. Only observed terminal completion/failure/cancellation
permits the next revision. Duplicate reconciliation of an older known revision
still returns its original binding; it does not become current again.

The Temporal admission-registry workflow retains at most 1,024 accepted delivery
keys and 1,024 distinct task/revision records. Known duplicates reconcile at
capacity; new keys reject without eviction, including new delivery IDs for a
known revision at delivery capacity. Rejections consume no identity. The initial
registry has no expiry, eviction, continue-as-new or production-scale retention
claim. Workflow state records binding and pending child dispatch in the same
workflow-task decision. Deterministic child ID = `job-` + SHA-256 of UTF-8
`task_id + "\n" + decimal_revision`; IDs disallow newlines. A pending child is
reconciled by this identity after lost responses; no second child ID is invented.
No nondurable caller cache can establish admission uniqueness.

## Operations, reconciliation and cancellation

Scheduling records intent, not an external effect. `acknowledged` records an
adapter acknowledgement, not terminal success. A timeout/lost reply becomes
`unknown` and schedules read-only reconciliation with the same Binding and target.
Effectful activities use a single attempt; workflow/activity retry machinery must
never blindly resubmit an effect. Read-only observations may retry with bounds.
A reconciliation result binds the complete operation, target, receipt/session and
trusted observation. `proven_absent` alone permits a separately authorized retry;
absence must come from authoritative exhaustive readback, never a timeout or an
empty eventually consistent query. Ambiguous/stale/unavailable readback remains
unknown. Repeated identical observed terminal receipts are idempotent; conflicting
receipts/identities reject and preserve prior state. Host offline queues on the
selected host; no alternative host is selected.

Cancellation has independent `not_requested`, `requested`, `acknowledged` and
`observed_terminal` states. Requested/acknowledged cancellation is not completion,
and cancellation timeout is not proof that the operation stopped. A race may
observe completed/failed instead of cancelled; preserve that actual terminal
outcome. Unknown effects remain reconcilable after cancellation. A terminal state
cannot be overwritten by stale acknowledgement/running events.

## Host seam

`launch(binding)`, `discover(binding)`, `cancel(binding, native_session_id)` and
observation polling are injected transport ports, not an app-server implementation.
A launch with a lost reply must discover first; exactly one matching observed
native session may bind. Zero ambiguous/incomplete results remain unknown unless
authoritative absence is proven; multiple matching sessions remain unknown. The
native session ID is observed from the peer and never synthesized from the job ID.
Reconnect preserves it. A changed host/workspace/epoch/operation/session rejects.
Native observations carry complete Binding, actual native session ID, monotonic
sequence and integer `observed_at_ms`. Trusted adapter time/freshness policy must
reject future/stale observations and old sequences before updating state. Queue
capacity is explicit and bounded; overflow rejects before an effect and never
silently drops a terminal/cancellation observation. Unsupported events/capabilities
fail closed. This tranche cannot qualify native macOS/Linux, capture or submission.

## Offline evaluation seam

Input locks exact candidate, baseline, dataset/split and metric/config bytes by
SHA-256, using the existing immutable lineage manifest. Reject train/test family
leakage, malformed splits and empty held-out evaluation. Baseline and candidate
must evaluate the same held-out cases; neither may tune on held-out results.
`evaluate(locked_manifest, configuration, provider, cancellation, budget)` uses
synthetic providers/scoring only in this tranche. It exposes no approval, promotion
or serving authority. Provider errors/unknown safety/cost cannot produce a pass.

One cumulative budget covers baseline, candidate, optimization, scoring, retries
and reservations: integer calls, tokens, elapsed milliseconds and cost microunits.
Limits are finite nonnegative integers with explicit units/currency scale in config.
Reserve an upper bound before each provider call; unknown bounds deny dispatch.
Settle measured usage, release unused reservation, never refund consumed usage.
Over-bound/unmeasured usage invalidates evaluation and stops further calls. Actual
elapsed time comes from an injected monotonic clock, includes all stages and never
resets per stage/retry. Cancellation is checked before every call and after return;
in-flight consumption remains charged. Concurrent calls must share reservations.
Unknown quality/safety/cost/time, missing results, exhausted budget or cancellation
blocks the gate. Thresholds are explicit locked config, not fabricated defaults.

The descriptor freezes evaluation input/output field names. `manifest_digest`
locks the exact lineage dataset and split. `config_digest` locks canonical config
bytes including metric ID/version, provider and optimizer config IDs, currency and
positive integer cost scale (microunits per currency unit). Thresholds contain
minimum quality, maximum quality regression versus baseline, maximum latency in
milliseconds, maximum measured cost in microunits and `require_safe=true`. Quality
metrics/thresholds must be finite numbers in the locked metric's declared range;
all integer units follow the value rules above. Native mappings may expose richer
threshold types but must hash every effective gate argument; an unhashed override
is invalid. Results echo all five input digests/version, cumulative usage,
baseline/candidate metrics, status and explicit blocking reasons. Result status is
`passed`, `blocked` or `failed`; missing/unknown metrics remain null and cannot pass.

## Evidence and acceptance

Temporal SDK 1.2.0 and CLI 1.10.0 require exact official source revisions,
checksums, lockfile and licenses recorded before execution. Preparation can acquire
dependencies; the prepared tests must run without downloads in a disposable
internal-network container, with UI disabled, no published ports and a per-run DB.
Worker/server recovery evidence uses fresh processes and the same real Temporal
DB. Local development persistence is not production durability or browser fencing.

Component tests, isolated integration and live acceptance remain distinct. A
composition lane with real core and Temporal must list scripted host/browser/
delivery/provider boundaries and independently observed call counts/order. Required
blocked/not-run/failed gates aggregate to non-success. A source commit, model replay,
process start or fixture success does not establish integrated or deployed behavior.
