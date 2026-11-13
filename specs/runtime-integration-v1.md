# Runtime integration v1

Version `runspindle.integration.v1` extends, without modifying, the semantics of
`runspindle.runtime.v1`. It is a Rust library mapping, not a native app-server
wire protocol or the separate `runspindle.fixture.v1` test format. Requests reject
unsupported versions and malformed values before mutation or dispatch. Runtime v1
identifier, digest and complete seven-field Binding rules apply unchanged.

## Durable host mapping (H02)

Core maps every Binding field by name to the pinned host library. Host owns the
operation store; core owns deterministic orchestration. The injected verifier
(default deny) checks the complete binding and action immediately before launch,
cancel or reconciliation. Neither replay nor a discovered session grants authority.
The library exposes submit/dispatch/reconcile/cancel/event/snapshot and a bounded
persistent receipt queue. In-memory and SQLite storage implement the same storage
interface. SQLite commits intent before invoking a peer and commits observations
with receipts atomically. Operation IDs are unique across the store. A different
binding for a retained operation conflicts, including changed policy or epoch.

A storage generation is compared and swapped transactionally. Peer calls occur
outside transactions; only the owner of the committed dispatch intent may launch.
An interrupted owner never grants a replacement owner permission to repeat the
effect. All later owners reconcile. A stale owner cannot overwrite newer state.
Cancellation intent and the single cancel-dispatch reservation are durable too.
No timeout-based lease takeover permits another launch or cancel.

Native observations contain the complete Binding, actual peer session ID,
positive increasing sequence, trusted integer observed time and optional terminal
outcome. Host rejects changed sessions, stale/future times, regressing time or
sequence, unsupported events and conflicting terminals. Identical terminal
observations are idempotent. Trusted adapter clock and maximum age are explicit;
peer time cannot establish freshness. Receipt backpressure rejects before effects
or observation mutation. Retention is finite, with no eviction of unknown work.

Core preserves host queued, scheduled, acknowledged, unknown, rejected, terminal
and cancelled-before-dispatch states, plus independent cancellation state and
last sequence/time. A pre-dispatch cancellation is a local outcome without a
fabricated native terminal observation or session. Completion racing cancellation
preserves the actual observed terminal result. Exactly one matching discovery may
bind; zero or multiple results remain unknown. Reconcile before any later effect.
Temporal effects use maximum_attempts=1. Readback may retry with explicit bounds.
The scripted-core runtime remains a distinct regression lane.

## Immutable artifacts and authorized acceptance (H07)

Core owns a separate bounded SQLite database. Artifact identity is complete
Binding + artifact ID + positive artifact revision. Store bounded actual bytes as
an immutable BLOB, compute SHA-256 from those bytes, and return that exact reference.
A duplicate identity with changed bytes conflicts. A validation records the exact
artifact reference, validator revision and policy revision, plus passed/failed.
Validation records are immutable: the artifact/validator/policy key cannot be
overwritten with another result. Acceptance records likewise cannot change their
artifact, validation, validator or policy binding. The injected validator receives
the actual stored bytes; a caller's digest or
boolean is not validation. Acceptance requires a passing validation of that exact
revision and policy and an injected authorized acceptance verifier, default deny.
The verifier sees the complete binding, artifact, validator and policy references.
Acceptance and its accepted-byte reference commit atomically. One accepted artifact
per task/revision; concurrent different references conflict. An exact duplicate is
idempotent. Acceptance does not imply delivery authorization. Changed bytes,
validation revision, policy or artifact revision never inherit acceptance.

## Durable delivery outbox and reconciliation (H07)

A delivery request carries version, complete accepted artifact reference, exact
destination (account and destination IDs) and stable delivery operation ID.
The injected delivery verifier, default deny, checks all fields before reservation
and immediately before sending. Reserve transactionally before transport invocation;
a unique operation cannot be rebound to other bytes, acceptance or destination.
Only the owner of the committed reservation may send once. After interruption,
unknown replies or lost acknowledgements, readback is mandatory and sending is
never repeated. No automatic proven-absent retry exists in this conservative lane.

The transport receives bytes read from the accepted BLOB, freshly hashed against
the accepted digest. A receipt must echo the exact delivery operation, artifact
reference, destination and an observed receipt ID. Readback is independently
provided by the destination transport, never fabricated by the outbox. Zero or
multiple receipts, mismatches or contradictory receipts remain unknown/conflict;
none can overwrite a delivered receipt. A known exact receipt is idempotent.
Delivery state and receipt commit atomically with compare-and-swap protection.
A scripted transport has a separate durable receipt ledger and independently
observable calls/order/bytes. This is not a replacement Tether implementation.

## Qualification and bounds

H02: real core + immutable pinned host Rust library + real pinned Temporal,
scripted native peer. H07: real core acceptance/outbox stores + real Temporal,
scripted destination. Each lane runs independently and fails closed on missing
prepared artifacts. No provider, browser, native protocol, Tether or live acceptance
is implied. Component stores have at most 1,024 operations/artifacts/validations/acceptances/
deliveries, 4,096 queued host receipts, and 1 MiB per artifact. Full stores reject
new identities while preserving existing records; exact duplicate validations
reconcile at capacity and changed results conflict. All SQLite dependencies, bundled
SQLite bytes, licenses and toolchain evidence are pinned before execution.

Fresh-process recovery, concurrent ownership, independent call/order and digest
assertions, malformed/unauthorized requests, stale observations, ambiguous discovery,
cancellation races and conflicting receipts are required. Deliberate duplicate
launch, session rebind, skipped validation, changed-byte and fabricated-receipt
mutations must fail behavioral assertions. Seeded repeats compare normalized
outcomes. Offline passes leave absent full-system adapters blocked.
