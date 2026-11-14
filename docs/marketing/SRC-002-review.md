# SRC-002 source preparation and review

This is an original research-paper adaptation, not a historical rebuild. Its nine
sections address the selected research argument, stop diagnosis, human effort,
bounded execution, workload selection, economics, evaluation, hypotheses and
counterarguments. The 18-file recursive paper scope is accounted for in
`SRC-002-disposition.json`; ten additional bundle files are recorded as exclusions.
All 28 selected preserved-file hashes were checked against the private retained
manifest. Exact original identities, paths and hashes remain private.

No project-wide license was established for the selected paper or its diagrams.
Owner-directed adaptation is not a blanket relicense. All historical prose,
diagram expression, coordinates, style and binaries remain excluded. Concepts are
handled through newly written text and five original editable tabular schematics.
The economic diagrams remain excluded, with their concepts represented only in the
unchanged canonical SRC-005 text. There are no recreated curves or invented data.
The public mapping uses opaque review-unit IDs rather than original paths.

## Citations

`SRC-002-citations.json` accounts for all 18 bibliography entries, with primary
URLs, reviewed dates/versions, narrow uses and explicit limits. The METR title is
corrected to its primary-page title. XSTest, OR-Bench and ReAct distinguish preprint
and conference dates. Dynamic OpenAI documentation is dated by review, not an
invented publication date. The ChatGPT agent overview now states that the product
is no longer available, while lower sections retain old availability guidance;
it is historical/transitional evidence, not a current native comparator. The NBER direct page returned 403; the primary indexed
abstract and AEA DOI supplied the corroborating record. No numerical benchmark,
productivity result, refusal prevalence or ROI transfers to Runspindle.

The first three bibliography entries retain the frozen economics numbering:
agentsmatter, anthropic2026 and jcurve. All other citations use matching LaTeX keys.
Static checks cover key closure, order and URLs. Actual PDF citation destinations,
link annotations and visual layout remain unverified until a reviewed native build.

## Unchanged economics and earlier evidence

The canonical economics narrative is inserted verbatim, apart from the same
LaTeX character escaping used by its existing renderer. The generator narrative,
economics.md, overview.md, economics-model.md, original SRC-005 review and original
SRC-005-validation.json remain unchanged. The current disposition changes only
the containing paper TeX hash; its original validation receipt is retained as
evidence about the earlier source tree, not relabeled as validation of this paper.
The new source receipt records this integration and the preserved PDF separately.

The older ReportLab PDF remains byte-identical. Its public generated TeX companion
is retained under `paper/legacy/reportlab-paper.tex`, explicitly uncompiled.
The receipt identifies the old renderer and source commit. Neither that TeX nor
the new authored TeX is claimed to have produced this PDF through compilation.

## Boundaries and remaining work

No native compilation, installation, runtime action, service, provider call,
publication or deployment was performed by this source preparation. Component
Gitlinks, STATUS and acceptance gates remain unchanged. SRC-010's four pinned
files and SRC-013's sixteen pinned files, notices and original evidence remain
byte-preserved. No workflow file changes belong to this work.

`SRC-002-build-plan.json` is a bounded proposal, not an execution receipt or a
complete toolchain lock. A later native action needs independent review of the
exact source, confinement, limits and dependency pins. Then compile the actual
source, inspect every page, validate citation/link targets and record output and
loaded-dependency hashes. Any layout corrections must be reviewed and rebuilt.
Issue 4 stays open; migration remains partial. Static source checks do not satisfy
the native-build, all-pages, citation and link acceptance gates. Safe original-expression
exclusions resolve that adaptation choice: rights to excluded originals do not
need to be secured to qualify this original paper. Runtime/live-behavior gates
remain separate and are neither passed nor made prerequisites for paper acceptance.

Latin Modern is a planned font dependency, not newly embedded output at this stage.
Its separate GUST Font License/LPPL terms must accompany any later compiled font
use as applicable: https://ctan.org/texarchive/fonts/lm and
https://ctan.org/license/gfl. No MIT or other blanket project license is assigned.

## Source-only validation commands

From the repository root, with existing tools only:

```
python3 tools/check_paper_source.py
python3 tools/check_economics_source.py
python3 tools/check_scaffold.py
python3 tools/check_artifacts.py
python3 -m unittest discover -s tests -p 'test_marketing*.py' -v
```

The tests use temporary copies, include negative preflight mutations, and must
preserve all files on failure. Generator runs preserve both paper representations;
they are not a native paper build. Exact final validation is recorded separately.

## Additive independent-review correction

The previous source and validation receipts are retained unchanged under
`paper/history/` and still describe the earlier local source identity. The current
checker uses a TeX control-word boundary rather than Python's word boundary for
its forbidden primitive check, including digit-suffixed primitives. Negative
mutations are rehashed and run through generator subprocesses in both normal and
optimized Python modes; the mutation text is never executed by a TeX engine.
This check is a narrow preflight, not a complete TeX parser or sandbox. Exact
hash review and separately approved external confinement remain the execution
boundary. The historical/transitional ChatGPT agent citation is corrected without
claiming capabilities of any replacement product. Frozen economics text remains
unchanged, and only its containing TeX identity changes.
