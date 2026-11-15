# SRC-005 economics review

Status: original conceptual adaptation with explicit source-expression exclusions.
The selected section is part of the SRC-002 paper bundle. Overall migration remains
**partial** and issue 7 remains open. Source selection is not a reuse license.

## Scope and rights decisions

The [item-level map](SRC-005-disposition.json) accounts for six prose blocks, the
single cost equation, both diagrams and captions, and all three citation entries.
The exact selected section and the selected diagram/bibliography closure were
reviewed against their privately retained hashes. No source location, private
identity or original hash is published in this record.

- Definitions, equations and economic mechanisms are rewritten in original
  language. The arithmetic restatement explicitly includes fixed integration,
  disjoint costs, units, accepted authorized outcomes, zero-completion and
  unknown-input handling. No historical source code is imported.
- Both source diagrams are excluded: no project-wide expression-reuse license
  was established, and their hand-entered curves are schematic, not measurements.
  Original text explains possible amortization without a crossing estimate and
  three opportunity scenarios without probabilities or transferred coordinates.
- The three primary references are attributed with limits. The NBER page denied
  direct retrieval; its primary-domain indexed abstract/metadata and the AEA
  journal abstract were checked instead. No access restriction was bypassed.
  Neither citations nor owner-directed adaptation relicense source expression.
- No historical binaries, source build commands, fonts, packages, runtime data,
  private snapshots or unselected Git history were copied or executed.

## Accounting and comparison

[economics.md](economics.md), the economics section of
[runspindle-paper.tex](runspindle-paper.tex), its ReportLab PDF and the overview
share one narrative in `build_documents.py`. The complete economics text is the
only changed section of those narrative derivatives. The overview changes because
it includes that same section. No other product page or deck is refreshed.

The existing [original executable specification](economics-model.md) and
`tools/economics.py` remain distinct from the historical source. Its cost fields
include failed attempts, repair, maintenance, verification and fixed integration.
The synthetic denominator sensitivity is not a forecast. Comparison needs matched
workloads, authority, acceptance criteria, periods, currencies and explicit setup
allocation. Unknown workload/price inputs remain unknown.

Customer value, cash savings and vendor revenue are separated. Incentive risks,
possible absence of break-even, provider changes and complementary investment are
explicit. The three references are context, never transferred Runspindle results.

## Reproduction and evidence boundaries

Use the existing Python 3.12.14 / ReportLab 4.4.9 renderer, without installing or
provisioning anything. From the root:

```
python3 -B docs/marketing/build_documents.py
python3 tools/check_economics_source.py
python3 -m unittest discover -s tests -p 'test_economics.py' -v
python3 -O -m unittest discover -s tests -p 'test_economics.py' -v
python3 -m unittest discover -s tests -p 'test_marketing_*.py' -v
python3 -O -m unittest discover -s tests -p 'test_marketing_*.py' -v
python3 tools/check_scaffold.py
python3 tools/check_artifacts.py
```

The source checker compares the complete generated economics prose, identities,
dispositions, citation closure and result hashes using checks that remain active
under Python `-O`. Negative tests reject denominator/source drift, missing scope,
rights/measurement promotion and stale hashes. Existing mirror tests still require
all four SRC-010 files and all sixteen SRC-013 files to stay pinned and intact;
failed mirror preflights must perform no generator writes. Twice-run generator
checks require byte stability with the installed renderer.

Run isolated Ruff E4,E7,E9,F,I and formatting checks on authored/modified Python.
Run strict mypy on `docs/marketing/build_documents.py`; check the new checker and
test together with `--strict --explicit-package-bases` to resolve the repository's
namespace-package layout. This is path resolution, not a type suppression or a
baseline expansion. Record actual command outcomes separately from these commands.

Full root tests require the existing exact feedback sources configured in the
validation workflow. Keep their revisions and all component Gitlinks unchanged.
A local pass does not repair the dependent PR54 runner's missing ReportLab
prerequisite or demonstrate remote CI success. This candidate depends on PR54 and
PR53 and must not bypass either gate. No native compilation, workflow changes,
installation, deployment or live evaluation is included.

Final observed results and exact tested content identity belong in the additive
SRC-005 validation receipt. Original SRC-010/SRC-013 notices, pins, guards and
receipts remain unchanged. Independent review and remote publication are separate
steps, not inferred from arithmetic, static checks or a successful PDF render.
