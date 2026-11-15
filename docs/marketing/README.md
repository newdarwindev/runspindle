# Runspindle design adaptations

These are adaptations of selected historical material, not faithful re-renders or migrated live applications. SRC-013 is the full reviewed compiled paper adaptation. SRC-002 now has a two-pass compiled original nine-section paper with all-page and citation/link review; final integrated-tree review and publication remain pending. Its old ReportLab PDF is preserved separately. SRC-003 and SRC-004 now have full-scope original editable presentation sources; their older PDFs are preserved, not current renderings. Historical source dependency closure is preserved privately. Overall selected-source migration remains partial.

- `runspindle-paper.tex`: exact compiled original research and evaluation proposal.
- `runspindle-paper.pdf`: actual 12-page native compiled candidate; see [build and review evidence](SRC-002-build-evidence.json).
- `paper/legacy/reportlab-paper.pdf`: unchanged prior ReportLab derivative, not the current paper.
- `paper/legacy/reportlab-paper.tex`: old generated, uncompiled companion source.
- `SRC-002-source-receipt.json`: exact compiled-input/output mapping and preserved historical evidence.
- `argument.tex`, `fleet.tex`: original editable full-scope presentation adaptations, uncompiled.
- `argument.pdf`, `fleet.pdf`: older ReportLab derivatives, **not the new presentation sources**.
- `presentations/legacy`: preserved old generated companion TeX.
- `workflow-refinery.pdf` and `.tex`: proposed DSPy evaluation and serving boundaries.
- `economics.md`: accepted-work cost accounting with no claimed savings.
- `index.html`: standalone product/design narrative generated here.
- `browser.html`: reviewed Browser SRC-009 source with explicit link/location
  normalization, not byte-identical and never regenerated here. See
  [mirror mapping](SRC-009-mirror.md) and [exact transformations](SRC-009-mirror.json).
- `vision.html`: byte-preserved canonical Console SRC-010 adaptation, edited in
  `newdarwindev/runspindle-console` at `docs/product/vision.html`. Its exact Console
  revision and hashes are pinned in `artifacts.json`, with the same MIT notice,
  disposition map and validation record.

The SRC-010 source scope is accounted for, but responsive, keyboard and actual
zoom acceptance remains blocked. Its migration remains partial. The marketing
renderer verifies the recorded canonical mirror and notice before any writes; it
does not overwrite the vision page. See [SRC-010-lift.json](SRC-010-lift.json) and
[SRC-010-validation.md](SRC-010-validation.md).

The argument and fleet PDFs remain older ReportLab outputs, not renderings of the
new Beamer sources. The current SRC-002 paper is compiled from six exact edited
inputs and has passed native and independent all-page output review. See
[SRC-002-COMPILED.md](SRC-002-COMPILED.md) for reproduction instructions, exact
source/output mapping and review limits, and [font notices](SRC-002-NOTICES.md).
Final integrated-tree review remains separate. No document certifies a live
implementation, runner, deployment or successful integration.

## Technical grounding for future presentations

Use [desired intent](../../specs/desired-intent.md) when revising conceptual
material. Explain how scoped access, session continuity, human exceptions and
evaluation can compose into maintained workflows. Keep planned capabilities
separate from measured outcomes and implemented components. Existing rendered
artifacts are unchanged; this link does not claim they were regenerated.

## Canonical SRC-013 paper

[workflow-refinery.pdf](workflow-refinery.pdf) and its [TeX source](workflow-refinery.tex)
mirror the independently reviewed Refinery closure at commit
`1aa0a4b0ed1494f88f9e3137ff1e2b73b7a25209` (tree
`23ac8ce5d5d8f1b53023e640a90ab38a52cff339`, merged in
`fc79d78f3eed3423da901b1c5b623e76ce08e7c4`). Only the builder import order
changed from the prior canonical snapshot. [Current mirror mapping](SRC-013-wrapper-mirror.json)
and [upstream wrapper evidence](source-wrapper-change-evidence.json) record this
transition; [original integration](SRC-013-integration.json) and
[original validation](SRC-013-final-validation.json) retain the historical mapping.
All eight historical figure PDFs,
the exact MIT notice, [separate font notice](SRC-013-NOTICES.md),
[source disposition](source-disposition.json), [toolchain lock](toolchain-lock.json)
and [original build receipt](build-evidence.json) are preserved byte-for-byte.
This eight-page PDF is TeX-built, not ReportLab output. The generator validates
this full pinned closure before any writes and never regenerates its TeX or PDF.
The authored presentation sources are separate adaptations and not this canonical paper.

No additional native compilation was performed for this mirror. The copied
`build-paper.py` is a reference CLI wrapper, not executed here or during the
recorded native build; its command/environment matches the executed native wrapper.
The receipt's `document_content_commit` is a local review identity, not a
fetchable public ref. Preserve original evidence; use separate integration evidence.
No runtime, benchmark, measured gains or live acceptance follows from this paper.
No component Gitlink or acceptance gate changed. This wrapper mirror transition
requires root review and validation; it does not claim new paper or runtime acceptance.

## Original SRC-002 compiled paper

The original [source review](SRC-002-review.md), [complete disposition](SRC-002-disposition.json)
and [source-only build proposal](SRC-002-build-plan.json) remain historical stage
records. Current [build evidence](SRC-002-build-evidence.json) records the native
execution and bounded document review; [toolchain evidence](SRC-002-toolchain.json)
separates known pins from observed loaded files. The generator protects the exact
current PDF, six source inputs, historical receipts and frozen economics before
any writes. It cannot build or overwrite a paper. Issue 4 remains open pending
final review/publication decisions; selected-source migration remains partial.

## Full-scope presentation source preparation

[SRC-003-004-review.md](SRC-003-004-review.md) explains every-slide/variant scope,
rights exclusions and current component boundaries. The [disposition](SRC-003-004-disposition.json),
[citations](SRC-003-004-citations.json) and [source receipt](SRC-003-004-source-receipt.json)
separate the original edited sources from the unchanged older PDFs. No PDF
currently renders these new decks. The generator now uses only the Python standard
library and cannot rebuild any PDF or authored TeX. Native Beamer dependency
inventory, separate build review and all-page acceptance remain pending.

## Canonical Browser SRC-009 source

The canonical Browser page is pinned to merged Browser commit
`a5446d9fab1f2384b0d2ea0a051b7fd56a8af00b`. Its six specification links, source
review and notices link to verified immutable Browser files. Product navigation
stays local; two location/status sentences disclose this derivative. Reversing
only the documented substitutions recovers the exact canonical content hash.
The generator validates this mapping after all existing source guards and before
any write. It now writes four outputs and cannot overwrite the Browser page.
Browser issue 5 remains open for genuine rendered/mobile/keyboard acceptance.
This source synchronization does not establish live runtime behavior.
