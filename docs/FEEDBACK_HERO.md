# H10 retained-feedback candidate component integration

This bounded lane implements part of composition #45 using actual merged-ancestry
Tether and Refinery source. It does not qualify the deployed composition, all of
H10, H12, or system acceptance. Current validation uses the exact Tether and Refinery commits recorded in the
composition lock and `scenarios/feedback-collection-current-v1.json`. Earlier
maintained-scenario receipts and `scenarios/feedback-collection-v1.json` are
historical evidence.

## Reproduce

Prepare clean, cache-free full-history worktrees of the two repositories at the exact commits
in that manifest. No tool here fetches dependencies, installs software or expands
access. Verify merge ancestry objects are available in those clones. Run:

```
python3 tools/feedback_hero.py --tether /prepared/tether --refinery /prepared/refinery
```

A clean authorized checkout can prepare the same inputs explicitly:

```
git submodule update --init --recursive
git clone https://github.com/newdarwindev/runspindle-tether.git local/feedback-sources/tether
git -C local/feedback-sources/tether checkout --detach 1e8d2091c55dfad47fdc64ec2e73fcd946da9921
git clone https://github.com/newdarwindev/runspindle-refinery.git local/feedback-sources/refinery
git -C local/feedback-sources/refinery checkout --detach d86a720b0a41bbc8e2dfefb773348aaaa563961b
python3 tools/feedback_hero.py --tether local/feedback-sources/tether --refinery local/feedback-sources/refinery
```

These explicit checkout commands need existing authorized repository read access.
They are preparation, not a network fallback performed by the lane.

For the unittest integration set `RUNSPINDLE_FEEDBACK_HERO_TETHER` and
`RUNSPINDLE_FEEDBACK_HERO_REFINERY` to those paths. Without both, that test explicitly
skips; the standalone command fails closed for missing/wrong sources. This lane is
not silently included in or substituted for existing H10–H12 gates. Run normal and
optimized Python. Python stdlib and Git suffice. No DSPy execution is performed.
The existing isolated validation workflow explicitly checks out both exact sources
into ignored local/feedback-sources directories with existing read-only access and
full history (including the root composition checkout), runs the standalone lane as a required step, and provides both test
environment variables. Failed/missing materialization fails CI, never silently
skips this lane. Remote CI qualification is pending. No hosted fallback or token/
access expansion is introduced.

## Boundary matrix

| Boundary | Exercised | Evidence limits |
|---|---|---|
| Tether Admission, ProviderJournal, FeedbackStore | Actual pinned Python components and SQLite files | Authentication/retention/validator callbacks synthetic |
| Destination transport | Existing in-memory FakeSlack only during fixture preparation | No real Slack message or receipt |
| Refinery collect and Store.commit_lineage | Actual pinned source, six persisted content-addressed objects | Source-material verifier and distinct collection/training grants synthetic |
| Source and output | Invented immutable bytes and exact revision/digest bindings | No real user data |
| Independent readback | Composition-owned read-only SQL and existing independent codec | No component serializer used to decode evidence |
| Core/Host/native/browser | Not exercised | Acceptance blocked |
| Training/evaluation/serving | Not invoked | Separate approval and qualification remain blocked |

The trusted-source loader verifies clean exact commits, all tracked component file
hashes, no untracked files anywhere in either import root, including ignored root-level
stdlib shadows, sourceless bytecode packages and platform extensions, unchanged composition base/gitlink agreement,
base ancestry and recorded reviewed merge ancestry. Refinery's exact internal Tether pin must equal the selected Tether commit. Workers use an empty temporary bytecode prefix and
`-B`; Tether additionally loads hash-verified source snapshots itself. This is
reviewed local source verification, not remote identity attestation.

## Scenario and independent effects

1. Prepare actual admission/delivery/retained-feedback stores using synthetic
   adapters. Only this phase invokes the fake provider (send and lookup).
2. Exit. A new process reopens those stores and runs explicit exact-event
   selection into Refinery. Collection and training grants have separate refs
   and must match the independently prepared exact batch digest.
3. Read objects, hashes, source/output/actor identities, retained event digest and
   collection-receipt links using read-only SQL. Reopen in another process and
   replay collection; object digests and snapshot identity must be unchanged.
4. Repeat in an isolated directory; normalized object digests must match.
5. Exit a worker with code70 at the final precommit training permission boundary.
   Observe zero persisted objects after rollback, reopen and collect successfully.
6. Duplicate selection, stale retained feedback and revoked final permission must
   persist zero objects. The stale case is denied because the previously approved
   exact batch no longer matches; it does not claim every stale selection throws.
7. Deliberately remove the final recheck in an in-memory throwaway copy of the
   collection module. Independent SQL must detect unauthorized committed objects.
   The pinned source checkout is never edited and the mutant is never published
   as a component implementation.

Sockets are forbidden in workers. Collection/replay must make zero provider calls;
training/evaluation/serving tables remain empty. Temporary directories and handles
are cleaned on success, failure and handled cancellation; abrupt machine/parent
termination is outside that cleanup claim. Worker timeouts are bounded. The only
public error is a fixed failure envelope; no child stderr or raw material is
copied into it. Raw synthetic rows are transient test evidence, not public output.

Passed local candidate integration is not full-system acceptance. No live provider,
OS-native fencing, production identity, running service, deployment or serving
adapter is established. All broader issue #45 dependencies remain independent.

## Mandatory partition inventory

The hygiene integration assigns `feedback-hero` exactly once to the component
partition, with the standalone command and all source inputs required. Missing
inputs fail before child execution; optional local unittest skips cannot satisfy
this mandatory entry. Quality and component CI jobs prepare exact candidate sources;
the quality job sets `MYPYPATH` to the prepared Refinery checkout for strict type
resolution. All root checkouts fetch full history. Aggregate receipt checks,
other partition entries remain unchanged. Exact preparation refs follow the current manifest. Local full
hygiene validation requires the same ignored `local/feedback-sources` checkouts,
`MYPYPATH` and both test source variables, plus the pinned quality-tool environment.
## Historical schema-admitted candidate upgrade

The candidate pins now include Tether schema admission (PR18) and Refinery structural storage admission plus its exact Tether pin integration (PR22/23). Both schema modules are included in the verified source inventories. Fresh worker processes reject missing admission, provider-journal, feedback and Refinery tables before collection, with independent SQLite observations of zero lineage writes and no silent schema repair. Existing replay, precommit crash recovery, consent-removal mutation and ignored source-shadow tests still run. The original `docs/feedback-hero-evidence.json` remains historical; current evidence is `docs/feedback-schema-candidate-evidence.json`. Release composition/gitlinks and older acceptance artifacts remain unchanged. This is still a synthetic adapter candidate lane, not full H10/H12 or deployment qualification.

## Materialized feedback batch

The existing `feedback-hero` validation entry now also runs the
`H10.materialized_feedback_batch` lane. The lane creates one synthetic
Slack task and output through the pinned Tether ingress and journal,
checks reaction HMAC admission against that exact output, and drives the
pinned Refinery collection, dataset, and batch APIs.

The parent checks the feedback revision, lineage and collection receipts,
dataset row and batch manifest using independent SQLite reads and SHA-256
recomputation. Two clean repetitions produce the same item, receipt and
manifest. Fresh workers repeat materialization and replay the original
batch, checking the input and output bytes at the read boundary. A worker
exits after the item insert and before commit. The parent observes zero
committed items and a fresh worker recovers normally.

Fresh workers also replay the exact signed add and remove callbacks. The parent
compares the retained revision, head, delivery and invalidation rows before and
after each replay. After removal, a delayed add is rejected both with its
original delivery ID and with a new delivery ID. The parent verifies that the
original revision and the single removal record are still present. A fresh
Refinery read of the saved manifest then returns no dataset items.

Wrong-purpose and missing-consent reads return zero bytes. After signed
source removal or local dataset withdrawal, a fresh worker returns zero
bytes and the prior row is still present. Deliberately disabling the
local withdrawal guard in a disposable worker exposes the synthetic
bytes and proves the independent observation catches that regression.
The original provider attempt is unchanged and no later provider
requests or model/serving rows appear.

Run both paths with the exact prepared Tether and Refinery checkouts:

```sh
python3 tools/feedback_hero.py --tether local/feedback-sources/tether --refinery local/feedback-sources/refinery
python3 -O tools/materialized_feedback_hero.py --tether local/feedback-sources/tether --refinery local/feedback-sources/refinery
```

See the [local qualification record](materialized-feedback-hero-evidence.json)
for exact pins and checks. The evidence covers the H10 signed synthetic
feedback batch. Full H10 remains blocked on the complete authorized
artifact and live source chain. Provider transport, DSPy execution,
dataset upload, and deployment are not run.
