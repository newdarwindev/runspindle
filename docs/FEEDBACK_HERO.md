# H10 retained-feedback candidate component integration

This bounded lane implements part of composition #45 using actual merged-ancestry
Tether and Refinery source. It does not qualify the deployed composition, all of
H10, H12, or system acceptance. Composition lock/gitlinks and the older maintained
scenario manifest/evidence are unchanged. Their historical qualification does not
transfer to these candidate pins. The new manifest is
`scenarios/feedback-collection-v1.json`.

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
git -C local/feedback-sources/tether checkout --detach 670989839a0fccbcf2014d01609778ae6e4df424
git clone https://github.com/newdarwindev/runspindle-refinery.git local/feedback-sources/refinery
git -C local/feedback-sources/refinery checkout --detach b68ba9d77d51ca453b3f0fa3a9fa31573d065250
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
base ancestry and recorded reviewed merge ancestry. Refinery's immutable internal
Tether pin stays unchanged. Workers use an empty temporary bytecode prefix and
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

## Schema-admitted candidate upgrade

The candidate pins now include Tether schema admission (PR18) and Refinery structural storage admission plus its exact Tether pin integration (PR22/23). Both schema modules are included in the verified source inventories. Fresh worker processes reject missing admission, provider-journal, feedback and Refinery tables before collection, with independent SQLite observations of zero lineage writes and no silent schema repair. Existing replay, precommit crash recovery, consent-removal mutation and ignored source-shadow tests still run. The original `docs/feedback-hero-evidence.json` remains historical; current evidence is `docs/feedback-schema-candidate-evidence.json`. Release composition/gitlinks and older acceptance artifacts remain unchanged. This is still a synthetic adapter candidate lane, not full H10/H12 or deployment qualification.
