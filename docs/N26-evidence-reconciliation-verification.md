# N26: bounded evidence-reconciler verification

References: [issue 44](https://github.com/newdarwindev/runspindle/issues/44),
[parent issue 2](https://github.com/newdarwindev/runspindle/issues/2).
The [machine-readable record](N26-evidence-reconciliation-verification.json)
contains the criterion matrix, source/tool pins, complete direct-check logs and
SHA256 digests of each embedded log. This is synthetic offline checker evidence,
not a campaign receipt or downstream product acceptance.

## Exact source and results

Tested source: `6d354d54f48b69c79a75a1159cbb21793a1f8db2`.
Tested tree: `5baa74b8ff9cec635b83b514f47600ab0bb310c2`.
All 253 source entries (blobs, modes and component gitlinks) were matched against
the public tree in an isolated local reconstruction. Components were not checked
out or executed. The reconstructed index wrote the exact tree above; its local
Git HEAD was not claimed to be the public commit. The source was verified unchanged
after testing. Main was unchanged before/after; in-flight native-turn PR65 was
preserved, not merged or qualified.

On 2026-11-16, 34 reconciliation tests passed normally and 34 with `-O`, zero
skips. The existing artifact-digest mutation checker detected the deliberate
broken invariant. The suite also detects Python-equality, float-decoder and
producer-identity guard mutations. Scaffold/100-file artifact integrity,
targeted Ruff lint/format and strict mypy passed. See the JSON for exact outputs.
The initial evidence-only publication does not retroactively change the tested source
identity or assert that its own new head was the source of those historical runs.
The initial evidence-only record changed no implementation. The follow-up below
changes only the test fixture lifecycle; STATUS, production implementation, pins
and workflows remain unchanged.

## Reproduce on an isolated local runner

Use the exact tested source above, CPython 3.12.16 and Git 2.53.0. Source bytes
pin configuration, fixtures and composition dependencies. The JSON records
binary SHA256s and the exact already-available quality package versions matching
`requirements-quality.txt`; installing tools is not part of these commands.
`PYTHON` means the absolute path to that interpreter and `QUALITY` the directory
containing those verified quality packages. Both are runner-local inputs, not
private paths published by this record. From the source root, one bounded command:

```sh
env -i PATH=/usr/bin:/bin LANG=C.UTF-8 LC_ALL=C.UTF-8 \
  PYTHONDONTWRITEBYTECODE=1 GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL=/dev/null \
  "$PYTHON" -m unittest discover -s tests -p test_evidence_reconciliation.py -v
```

Companion commands used with the same allowlisted environment:

```sh
"$PYTHON" -O -m unittest discover -s tests -p test_evidence_reconciliation.py -v
"$PYTHON" tools/check_evidence_mutations.py
"$PYTHON" tools/check_scaffold.py
# Quality commands additionally receive PYTHONPATH="$QUALITY" only.
"$PYTHON" -m ruff check --select E4,E7,E9,F,I tools/reconcile_evidence.py tools/check_evidence_mutations.py tests/test_evidence_reconciliation.py
"$PYTHON" -m ruff format --check tools/reconcile_evidence.py tools/check_evidence_mutations.py tests/test_evidence_reconciliation.py
"$PYTHON" -m mypy --strict tools/reconcile_evidence.py tools/check_evidence_mutations.py tests/test_evidence_reconciliation.py
```

## Claim boundaries and criterion interpretation

The matrix maps each criterion to executable coverage. Expected invalid inputs
are rejected; the exact-source positive receipt passes only its bounded criterion.
Blocked, not-run, unknown, historical, draft and stale results remain distinct
non-success states. Synthetic receipts do not become current-main campaign proof.
The independent observer runs in another process and reads a separate synthetic
effect ledger. Actual temporary Git stores, artifact bytes and fresh CLI processes
are exercised; no mutable application store or crash/power-loss durability is
claimed. TemporaryDirectory cleanup is registered before fixture setup; this is
not cancellation qualification for an operational installer or service.

## Cancellation follow-up: test-only overlay

The original 34-test run did not inject cancellation. A follow-up found that
CPython unittest skips registered cleanups when KeyboardInterrupt escapes. The
fixture now cleans its owned TemporaryDirectory on that path only; ordinary
success/failure accounting stays with unittest. If cleanup itself fails, the
same interruption propagates with a sanitized failure note, never a success.

The JSON pins this follow-up by base source/tree plus the SHA256 of the sole
executable overlay, `tests/test_evidence_reconciliation.py`, avoiding a circular
hash of this evidence document. Production code is unchanged. Five additional
lifecycle tests use actual temporary files and Git stores: success, assertion
failure, setup interruption, interruption during reconciliation artifact hashing,
and cleanup failure preserving the original interruption. All 39 tests pass
normally and optimized, zero skips. Removing the interruption cleanup in memory
causes both cancellation-filesystem regressions to fail as expected; their own
safety cleanup removes the deliberately leaked fixtures. The original digest
mutation checker still passes. Strict mypy passes for the same three files.
The reproduction command above also runs this follow-up when used with the
exact overlaid test file whose digest is recorded in the JSON.

Failed checks: none in the bounded verification. Blocked prerequisites: none
for the offline suite or controlled fixture-cancellation checks. Cancellation
means injected catchable KeyboardInterrupt, not SIGKILL, arbitrary process
termination or service cancellation. No mutable application-store durability is
claimed. Not run: full aggregate, native/component/provider or campaign
qualification, CI reruns and application cancellation/crash campaigns.
Downstream acceptance is unknown from this evidence and `system_acceptance`
remains `not_inferred`. Parent issue 2 keeps its broader acceptance criteria.
Issue closure and any release or runtime qualification require separate decisions.
