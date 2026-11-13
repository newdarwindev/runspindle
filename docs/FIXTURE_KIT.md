# Provisional synthetic fixture contract

This implements a bounded part of [issue #1](https://github.com/newdarwindev/runspindle/issues/1).
`fixtures/v1` is an original synthetic test bundle, **not an agreed runtime wire
protocol**, an authentication interface, or evidence of upstream compatibility.
No operational acceptance gate or CI workflow is changed.

## Local invocation and evidence

Prerequisite: Python 3.9 or newer; no package installation, service or sibling
checkout is required. From the composition source directory:

```sh
python3 fixtures/v1/fixturekit.py
python3 -m unittest discover -s tests -v
python3 tools/check_scaffold.py
```

Local checks ran on Python 3.9.6 against base composition commit
`6c7b930f1f42f5937c2c21b09fdc36e931a8ac4f`. The bundle manifest binds exact
SHA-256 hashes of the validator, declarative contract, golden fixtures, mutation
vectors, fault schedule and real artifact bytes. The eventual PR commit binds
the tests and this document. Test seed is `90210`; fixture observation time is
`2026-11-13T00:00:00Z`. This is a fixed synthetic time, not a live observation.

| Gate | Status | Evidence class |
|---|---|---|
| Bundle integrity and 17 unittest cases, including negative subcases | passed locally | synthetic fixture conformance |
| Standalone subsets for all seven components, fresh Python processes, repeated byte-identical exports | passed locally | synthetic fixture packaging |
| Structural and published artifact checks | passed locally | scaffold structure / artifact integrity |
| Actual producer/consumer adoption and cross-language validators | not-run | component contract conformance |
| Pinned upstream/native/browser/Temporal compatibility | blocked: adapters and pins absent | isolated integration |
| Durable restart, authenticated authority, live acceptance, deployment | not-run | separate product gates |

Test output is generated locally; no external services, provider calls, real
accounts, credentials or personal profiles are used. The only spawned processes
are bounded standalone Python validators (10-second timeout). They terminate
before temporary directories are removed. Temporary-store cleanup is tested on
normal export completion and injected failure. No persistent process is started.

## Boundaries and ownership

| Fixture kind | Producer / observer | Consumers / intended seam |
|---|---|---|
| `admission.observed` | Tether / core admission | core; delivery ID, intent/revision/policy/host/workspace/action |
| `native.observed` | host native adapter | core, console; actual session, cancellation states, capability |
| `browser.observed` | trusted browser observation adapter | browser, console; account reference, top/frame origin, epoch, passive/control state |
| `event.observed` | Tether sanitized event transport | Tether; exact destination, event/operation and delivery receipt |
| `artifact.observed` | core validation/delivery adapters | core, console; actual bytes digest, acceptance, destination, receipt |
| `telemetry.observed` | platform readback adapter | platform, console; producer/config version, emitted versus persisted |
| `feedback.observed` | collection / refinery adapters | refinery, Tether; actor, exact output revision/hash, family, rule, collection/transmission policies |
| `candidate.observed` | refinery evaluation / serving adapters | refinery, platform; exact candidate digest, serving receipt and rollback state |

The selected fixture kinds are intentionally small observation seams. For
example, launch requests without native IDs and independent profile deletion
operations require future reviewed kinds; adapters must not fabricate native
session IDs or extend this schema to fit them. Native protocol mappings,
authenticated principal/context, durable store CAS/retention and real browser
origin observations remain provisional adapter responsibilities.

## Envelope and compatibility rules

`contract.json` is a declarative fixture schema consumed by `fixturekit.py`; it
is not advertised as JSON Schema or an upstream service schema. All required
keys are explicit, and every unspecified top-level, identity and detail key is
rejected. Identity fields are mandatory for the selected kind; they cannot be
null or mixed into unrelated kinds. Common identity binds task, intent and
policy revision, explicit selected host/workspace, operation, attempt, sequence,
trace, span and event. Kind-specific requirements are in the schema file.

Integers exclude Booleans/floats and stay within the exact JSON integer range
(up to `2**53-1`); revisions/attempts/epochs are positive and sequence may be zero.
Identifiers are bounded ASCII tokens (128 characters); digests are lowercase
64-character SHA-256 hex, never mutable URLs. Origins are restricted to synthetic
HTTPS `.example` hosts without user info, path or port. Timestamps use a valid
UTC second. Messages are limited to 64 KiB; duplicate JSON keys, non-finite
numbers, unknown events/schema versions and unsupported state strings reject.
No free-form payload field carries source messages or secret material.

A syntactically valid envelope is **not** proof of a transition or effect.
`assert_conforms` compares the complete identity and expected state to an
independent request oracle. Delivered/persisted/serving assertions require a
separate transport/readback spy receipt matching identity and receipt detail.
Artifact delivery additionally requires the independently accepted digest;
serving requires the independently approved digest. These are synthetic test
oracles, not authenticated receipts. Real adapters must establish their own
trusted provenance and durable authorization. Unknown/blocked/not-run states
cannot report passed; aggregation returns success only for a nonempty set of
entirely passed required gates. All five statuses stay distinct in input reports.

`vectors.json` publishes wrong version, wrong identity, stale epoch, changed
digest, fabricated receipt and uncertain-success mutations with expected error
codes. Tests check the mutated adapter output against unmutated independent
oracles and real artifact bytes; they do not derive expected state from the
mutated output. Additional tests cover malformed fields, missing/extra keys,
invalid identity combinations, manifest corruption, timestamp/freshness absence,
consumer exports and fail-closed aggregation.

Contract changes must update the version for incompatible required fields,
states or semantics. Unknown versions/events reject until explicitly supported;
there is no permissive forward-compatibility fallback. Before upgrading a pin,
review both producer and consumer semantics, run the old and new vectors, and
review the manifest diff. Do not silently treat this test protocol or the
existing Rust process-local model as the public runtime API.

## Independent consumers and pins

Each component has a declared relevant kind subset in `manifest.json`. Export
one standalone subset to a **new** directory (an existing directory is refused):

```sh
python3 fixtures/v1/fixturekit.py export host /tmp/runspindle-host-fixtures-v1
python3 /tmp/runspindle-host-fixtures-v1/fixturekit.py
```

The subset contains its validator, schema, relevant golden/mutation vectors,
artifact bytes and exact file hashes. Its `origin_manifest_sha256` binds the
reviewed full bundle. Consumers should vendor that subset with a pin recording:
composition source commit, `runspindle.fixture.v1`, component name, origin
manifest SHA-256 and subset manifest SHA-256. Verify against this separately
reviewed pin before loading; an internally consistent manifest alone is not
source authentication. Do not resolve floating URLs or require running sibling
services. Components can implement validators in their own languages, using
the same vectors; cross-language parity remains a gate until exercised.

Rebuild a changed source bundle with `python3 tools/update_fixture_manifest.py`,
then inspect its compatibility and hash diff. This command only updates test
fixture metadata. It grants no authority to change consumer pins automatically.

## Fault and isolation contract

`faults.json` specifies deterministic duplicate, reorder, timeout, partial
response, explicit retry, restart and uncertain-effect checkpoints with expected
call counts and observations. It is a **schedule specification**, not a
nine-step composition driver or evidence that recovery works. A real durable
store suite must restart fresh processes and reconcile the original operation;
retaining a Python object cannot satisfy it.

`Clock` and `Ids` provide injected virtual time and seeded identifiers. `Spy`
records independently inspectable operation/identity calls and denies any
operation outside an explicit allowlist; a new spy resets its ledger. Adapters
under test must route all effects through these injected seams, with outbound
network denied by their runner/sandbox. The kit itself contains no network
transport and does not claim to provide an OS network sandbox. `temporary_store`
cleans a disposable directory on normal or exceptional exit; it does not promise
persistence or crash recovery. Every future real adapter test must specify its
resource deadline, fault points, real/fake matrix and cleanup owner independently.

## Remaining issue #1 work

Consumer pin PRs and actual producer/consumer parity in all seven repositories
remain open. Runtime adapter mappings cannot be agreed or qualified from these
fixtures alone. Stateful scenario implementations, real store concurrency and
restart, upstream pins and bounded integration belong to subsequent component
and composition work. This change therefore references #1 without closing it.
It does not complete source migration, authorize legacy archival or establish
live acceptance.
