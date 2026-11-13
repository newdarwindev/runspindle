# Offline maintained-workflow candidates

The contract extension is `runspindle.maintained-evidence.v1`. New core, refinery
and platform work is retained on isolated component branches. The reviewed
composition lock and gitlinks are unchanged. The unrelated platform checkout
on `feat/isolated-runner-fleet` is preserved; do not reset it to run these lanes.

The [candidate source manifest](../specs/maintained-scenarios-v1.json) names the
exact old pins and candidate revisions. The runner requires clean exact
component checkouts and validates ancestry, gitlinks, versions and preparation
bytes. It does not silently execute a newer component in the reviewed lane.
Independent final-head review and dependency-ordered merges/pin qualification
are still required. No issue is closed by these candidate results.

Use separate clean component worktrees for the manifest's candidate commits:

```sh
python3.13 tools/maintained_scenarios.py \
  --manifest specs/maintained-scenarios-v1.json \
  --component core=/path/to/exact/core-candidate \
  --component refinery=/path/to/exact/refinery-candidate \
  --component platform=/path/to/exact/platform-candidate \
  --report local/maintained-scenarios.json
```

The refinery worktree needs the explicit ignored wheel preparation described in
its `specs/durable-offline.md`; runtime never downloads dependencies. Docker
must have the exact Linux arm64 Python image in the candidate toolchain record.
Missing/changed prerequisites block. Successful bounded lanes still return
**exit 78** because required review, native/Tether, Langfuse and full-product
gates remain non-success. No cloud CI fallback or runner provisioning is added.

H10 independently reads real refinery SQLite records, exact old/new output
bytes, quarantine and locked family assignments. Tether observations and
collection/actor authority are scripted. H11 runs real pinned DSPy `Predict`
over the same locked heldout cases in actual durable experiments, using a
deterministic local LM and synthetic measurements. It kills the worker after
actual candidate load but before registry acknowledgement, observes the active
serving bytes independently, then starts a fresh worker to reconcile and roll
back. Parent SQL/serving reads verify eight attempts, exactly three loads in
order, prior-byte restoration and historical output attribution. Provider
quality, monetary cost and production approval are not established.

H12 builds, installs and reads back a checksummed **development metadata
bundle** inside a disposable Linux arm64 target. It contains component
identities, contract metadata and rights notices, with exact dependency
inventory/toolchain bindings. It contains no runnable product distribution or
installed services. The platform's separate Linux component lane exercises
fresh-process interrupted installation and rollback. Unsupported product
capabilities appear in the bundle and observed result. The generated artifact
is `local/maintained-artifacts/development.bundle`.

H08 remains blocked as a whole. Platform's separate standard-Collector lanes
exercise synthetic whole-envelope privacy (including resource/scope schema
URLs), actual file-exporter readback, duplicates, HTTP rejection, volatile
buffer loss and persistent exporter-queue recovery after SIGKILL. They are
Collector/file diagnostic evidence, not Langfuse or native compatibility.
Langfuse preparation is blocked on unavailable public MinIO artifacts; exact
registry/checksum failures and unfinished inventories are retained in the
platform candidate. No Langfuse service ran and no substitute backend was
introduced.

H02/H07 regression evidence uses the existing pinned host library, actual
Temporal, core/host SQLite stores and independent scripted peer ledgers.
Additional authenticated admission coverage exercises concurrent callers,
conflicting replay, explicit successor gating, expired authority and recovery
after host prepare commit. The synthetic authority is exact-request/default
deny; it is not production authentication or real Tether admission. The precise
server interruption between registry mutation and child creation is not
separately injected. Browser, console, visual generation, selected-source
migrations, live providers and paid evaluation retain their agreed deferrals.

The [issue criterion audit](offline-issue-audit.json) reconciles every original
listed criterion and acceptance paragraph with exact component revisions,
implementation/test references and remaining gaps. Existing historical evidence
remains separate. Run the full composition unit suite in a separate composition
worktree with the reviewed seven pins; running its pin checks against the
unrelated platform checkout correctly fails closed. The current checkout's
scaffold and candidate lanes can run without modifying that checkout.

Concurrent remote mains have since advanced to a separate Strix/CI tranche, including newer composition pins. These candidates retain the instructed base and do not qualify those newer revisions. Reconcile that work, then independently review and retest the exact merged heads before any pin upgrade. Draft dependency reviews: [contract #40](https://github.com/newdarwindev/runspindle/pull/40), [core #15](https://github.com/newdarwindev/runspindle-core/pull/15), [refinery #14](https://github.com/newdarwindev/runspindle-refinery/pull/14), [platform #13](https://github.com/newdarwindev/runspindle-platform/pull/13).

The [composition draft #41](https://github.com/newdarwindev/runspindle/pull/41) gathers the component review links and candidate evidence. Twenty issue bodies were reconciled and independently read back; original checklists are preserved and all remain open.
