# Exact-source evidence reconciliation

This bounded offline tool implements composition issue #44's relationship checks.
It does not establish runtime interoperability, authenticate a producer, fetch GitHub,
execute recorded commands, rewrite README/STATUS, move pins, or close issues.
Its contract is `runspindle.evidence-reconciliation.v1`. This supports the desired
intent's exact compatible revisions and distinction between execution, acceptance
and delivery; existing runtime and maintained-evidence contracts are unchanged.

Run `python3 tools/reconcile_evidence.py /private/path/manifest.json` with a
sanitized, independently collected evidence packet. Exit 0 means all supplied
criteria and claim mappings reconcile, never full-system acceptance. Any failed,
blocked, not-run, unknown, missing or invalid input is non-success. The JSON report
retains each lane's status and evidence class. No status is inferred from another
class. An intentional blocked acceptance gate stays non-success.

The manifest is an operator-reviewed inventory, not untrusted transport authority.
`main_sha` and `kind` are snapshots obtained independently from GitHub before the
check; freshness or authenticity of that snapshot is not proved by an offline tool.
Draft/historical snapshots cannot pass as current main even if their bytes match.
A source advancing after inventory collection requires a refreshed inventory and
new check. Public examples/tests contain only synthetic data; actual receipts,
source inventory and private paths belong outside Git.

## Packet contract

All hashes are lowercase SHA-256 of actual file bytes, all commit SHAs are full
lowercase Git SHA-1s. File references have shape
`{"path":"relative/path","sha256":"<64 hex>"}`. Paths and symlinks must remain
inside their declared root. Duplicate JSON keys are rejected. Receipt/observation/claim JSON or text is parsed from the same bytes whose
digest was checked; it is never reopened for interpretation. Artifact bytes are
read, never executed. Sources, pins and dirty state are checked again after
claim reads. These are optimistic before/after observations, not an immutable
filesystem snapshot: concurrent mutation and restoration between observations
is outside this bounded check; use an exclusively owned isolated checkout. Paths, command text and raw evidence are excluded
from the generated report.

A manifest contains:

- `version`: `runspindle.evidence-reconciliation.v1`.
- `composition_root`, `artifact_root`: paths relative to the manifest. Keep the
  evidence packet outside the source trees so collecting it does not dirty them.
- `sources`: a map keyed by `composition` or a component name. Each value contains
  `root`, `main_sha`, and `kind` (`current_main`, `draft`, or `historical`). The
  checker reads actual Git HEAD and tracked/untracked dirty state. Every lock
  entry must match its index gitlink; every claimed component HEAD must match its
  composition pin and the supplied current-main snapshot. Dirty composition
  sources invalidate component claims too. Unrelated component main advances
  require separate pin review; this command never advances them.
- `criteria`: a nonempty list of records with unique `id`, `issue`, `source`,
  `capability`, `evidence_class`. Classes are `structural`, `synthetic`, `component`,
  `isolated_integration`, `live_acceptance`, matched exactly, with no promotion.
- `capabilities`: a map keyed by capability ID; values contain `source`,
  `criterion`, `status`, and a `receipt` file reference.
- `claims`: a nonempty list mapping each reviewed README/STATUS claim to a
  `criterion` and a `file` reference relative to composition. JSON files use
  `selector`, a list of object keys ending at the claimed status string. Text
  files use an exact `marker` and `status` supplied by the reviewer. The entire
  file digest is checked; any prose change requires renewed mapping review.
  Unmapped prose is outside the tool's scope.

A receipt contains `source_sha`, `source_clean` (true), `criterion`,
`evidence_class`, `status`, `producer` (stable identity), `command` (argv list),
`inputs`, `artifacts` (nonempty file-reference list), `observation` (file reference).
`inputs` maps `toolchain`, `config`, `fixtures`, `dependencies` to file references
for the exact inventories/locks used. Referenced bytes must exist and match.
Each capability/receipt status is one of `passed`, `failed`, `blocked`, `not_run`,
`unknown`, and must agree. Receipt source and criterion must agree with the
actual source and criterion inventory. Clean-source declarations cannot override
the Git dirty check.

An observation contains `source_sha`, `criterion`, `observer` (distinct from
producer), integer `forbidden_calls`, integer `forbidden_effects`, `expected` and
`observed`. Passing requires zero forbidden counts and exact expected/observed
agreement. The independent verifier must actually acquire those observations;
a distinct identity string is an attribution check, not cryptographic proof of
independence. The tool checks recorded evidence relationships, never substitutes
self-reported status for an external effect observation.

## Verification and remaining gaps

`python3 -m unittest discover -s tests -p test_evidence_reconciliation.py -v`
creates actual temporary Git stores and synthetic artifacts. A separate observer
process reads a separate effect ledger. Tests cover stale main/receipt SHAs,
missing/changed bytes, dirty/untracked sources, draft/historical evidence, stale
README/STATUS mappings, all result states, evidence-class substitution, forbidden
calls/effects, wrong observers, missing input identities, path escape, duplicate
JSON keys and gitlink/lock disagreement. A fresh CLI process checks the positive
case; process spies verify recorded command strings are not executed. Temporary
stores are cleaned on success/failure by the test harness.

`python3 tools/check_evidence_mutations.py` deliberately removes the artifact
hash invariant in an external temporary copy and requires the changed-byte test
to fail. The original implementation must pass first. This is synthetic negative
verification, not real transport, native, runner or live acceptance. No database
crash/power-loss, producer authentication or signed-receipt durability claim is
made. Current-main qualification still requires independently refreshed source
snapshots and exact-head execution on the approved isolated runner lane.

## Foundation campaign integration

The foundation candidate preserves the manifest-driven `tools/validate.py`
entrypoint from hygiene PR #46. `hygiene.json` requires the evidence mutation
checker, reconciler and test module explicitly; missing files fail preflight
instead of silently dropping this check. New files pass the pinned static checks
without adding diagnostics to the existing debt baseline.

Actual campaign receipt adapters and their source inventories remain private.
A local passing draft receipt is retained as a local result, with draft, pin,
dirty, skipped and missing independent-observation reasons preventing promotion
to current-main acceptance. The synthetic test suite is qualification of the
checker, not acceptance of the campaign being checked. Hygiene and required
Strix checks must qualify before dependent merges; no pin update is included.
