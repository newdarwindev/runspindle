# SRC-001 core-product artifact coverage

This directory records a complete requirement-level adaptation of one selected
historical artifact. It does not publish the original document or its navigation
links. Exact original repository, revision, path, bytes and SHA-256 remain in the
private source record. The selected file has been reviewed in full. Its linked
legacy documents are navigation dependencies, not implicitly selected imports.

The canonical public [coverage inventory](coverage.json) renders the
[system contract](../../specs/system.md). Public component targets are exact
composition pins, with their specification hashes recorded in the inventory.
The current seven component boundaries replace the historical architecture.
No submodule pin or component implementation is changed by this lift.

## Source inventory and review decisions

| Source section | Opaque units | Disposition |
|---|---|---|
| Purpose | I01 | Adapted scope boundary |
| Product boundary and two paths | B01–B05 | Adapted outcome, execution, learning and authority |
| Capability index | O01, P01–P10 | Adapted labels and all ten capability requirements |
| Cross-component contracts | C01–C05 | Adapted identity and evidence obligations |
| Acceptance introduction, rows and evidence policy | A00, G01–G08, A09 | Adapted all eight gates; no passed full-slice claim |
| Evidence and gap maintenance | M01–M07 | Adapted all seven maintenance obligations |
| Historical coordination references and currency warning | X01–X07 | Six individually resolved navigation exclusions; adapted currency warning |

There are **46 units: 40 adapted and six excluded**. Every excluded unit records
its reason and current replacement target. No requirement is silently omitted;
none of these six references imports its destination or an operational snapshot.
The public opaque unit names are documentation labels, not original paths.

### Rights and privacy

Owner-directed adaptation covers the selected requirements. It is not a blanket
license to redistribute original expression or its dependencies. The public prose
is newly written for the current component boundaries. No historical executable
source, binary, original text passage, figure, third-party dependency, device
snapshot, runtime ledger or private navigation destination is imported. No new
license is granted to the historical material. This scope therefore needs no
new dependency notice; existing repository and component notices remain intact.
Ambiguous expression and all linked unselected material are excluded rather than
assumed cleared. A later import requires its own exact rights and privacy review.

The reviewer compared all selected units with the original retained file, verified
its original SHA-256, and checked the owning component specifications. This is a
source/requirements review; it is not independent runtime qualification. A separate
independent review of the frozen candidate is required before publication. Its
outcome and exact commit/tree belong in the publication receipt, not an invented
success here.

## Evidence classes and remaining work

- Historical reference: retained privately, with original identity and hash intact.
- Adapted content: this inventory and system contract account for the selected scope.
- Executable implementation: unchanged by this work. New executable files are
  artifact validation only, not product adapters or runtime services.
- Verified behavior: the checker/tests qualify inventory, hashes, target consistency,
  exclusions, privacy guards and fail-closed status handling only.
- Runtime acceptance: all eight full-slice gates remain not_run. Related H02/H07,
  H08, H10 and H11 evidence is linked at its own bounded scope and original revisions.
  A library pass, synthetic transport or source check is not authenticated native,
  browser, provider, telemetry, Console or full-system acceptance.

[Composition issue #1](https://github.com/newdarwindev/runspindle/issues/1) owns the
reusable synthetic scenarios. Existing fixture, runtime, integration and maintained
contracts are referenced rather than changed or reimplemented. The coverage checker
adds no runtime wire fields and cannot approve a live operation. Current pins may
have fewer capabilities than newer component mains; this artifact does not move
pins or transfer a newer main's evidence to them. Browser profile encryption remains
a requirement even though the pinned browser has no qualified implementation.

Only [artifact issue #3](https://github.com/newdarwindev/runspindle/issues/3) is eligible
for closure after its source and validation review. Other source issues, composition
#1, live gates, global migration status and archived applications are unchanged.
Global selected-source migration remains partial. Existing related SRC-001
adaptations in Browser, Platform and Refinery keep their own partial scope; this
canonical root mapping neither upgrades their provenance nor qualifies their code.

## Reproduce artifact validation

Use an initialized exact composition checkout and the existing Python environment.
No compiler, service, provider, installation, credential or network change is needed
for these checks. Initialize public pinned submodules as an explicit preparation
step if they are absent. The checker fails closed when a referenced spec is missing
or its bytes differ, rather than silently passing absent targets.

For zero-skip full-suite runs, prepare the exact existing candidate sources described
in [FEEDBACK_HERO.md](../FEEDBACK_HERO.md): Tether
670989839a0fccbcf2014d01609778ae6e4df424 and Refinery
b68ba9d77d51ca453b3f0fa3a9fa31573d065250. Export their local prepared checkout paths as
RUNSPINDLE_FEEDBACK_HERO_TETHER and RUNSPINDLE_FEEDBACK_HERO_REFINERY. Do not replace
them with component main branches or claim a full pass if those tests skip.

```sh
python3 tools/check_scaffold.py
python3 tools/check_core_product.py
python3 -O tools/check_core_product.py
python3 -m unittest discover -s tests -v
python3 -O -m unittest discover -s tests -v
python3 tools/validate.py
python3 -O tools/validate.py
ruff check --select E,F,I,UP,B,SIM --ignore E501 tools/check_core_product.py tests/test_core_product.py
ruff format --check tools/check_core_product.py tests/test_core_product.py
mypy --strict --explicit-package-bases tools/check_core_product.py tests/test_core_product.py
```

The aggregate runs the dedicated checker unconditionally and includes the tests.
Its optimized driver does not make child interpreters optimized: the separate
`python3 -O -m unittest` command is necessary. Existing main has no strict whole-repo
hygiene gate; strict checks above apply to the new checker and tests without altering
the separate hygiene proposal, baselines or workflow/image gates.

[Artifact manifest](artifact-manifest.json) binds every new artifact/checker/test and
the aggregate registration by SHA-256, plus only the SRC-001 provenance record.
It intentionally excludes itself to avoid a self-hash cycle. The checker emits the
actual tested Git commit and whether tracked/untracked changes exist. Freeze first,
then record exact resulting commit, tree, manifest hash, commands, environment,
test counts and review outcome in the candidate/publication receipt. The public PR
receipt can bind that exact commit without embedding a self-referential commit in
its own tree. Original source identity/hash remains private and is never replaced
by the resulting public commit/hash. Hash refresh alone does not validate semantic
changes; rerun affected tests and source review for changed content.
