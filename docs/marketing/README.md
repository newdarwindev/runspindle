# Runspindle design adaptations

These are adaptations of selected historical material, not faithful re-renders or migrated live applications. SRC-013 is the full reviewed compiled paper adaptation. SRC-002 now has a full original nine-section editable proposal, not yet compiled; its old PDF is preserved separately from the new source. SRC-003 and SRC-004 now have full-scope original editable presentation sources; their older PDFs are preserved, not current renderings. Historical source dependency closure is preserved privately. Overall selected-source migration remains partial.

- `runspindle-paper.tex`: full original research and evaluation proposal, uncompiled.
- `runspindle-paper.pdf`: unchanged older ReportLab derivative, **not the new paper**.
- `paper/legacy/reportlab-paper.tex`: old generated, uncompiled companion source.
- `SRC-002-source-receipt.json`: exact separation of old rendering and new source; native build remains not run.
- `argument.tex`, `fleet.tex`: original editable full-scope presentation adaptations, uncompiled.
- `argument.pdf`, `fleet.pdf`: older ReportLab derivatives, **not the new presentation sources**.
- `presentations/legacy`: preserved old generated companion TeX.
- `workflow-refinery.pdf` and `.tex`: proposed DSPy evaluation and serving boundaries.
- `economics.md`: accepted-work cost accounting with no claimed savings.
- `index.html`, `browser.html`: standalone product/design narratives generated here.
- `vision.html`: byte-preserved canonical Console SRC-010 adaptation, edited in
  `newdarwindev/runspindle-console` at `docs/product/vision.html`. Its exact Console
  revision and hashes are pinned in `artifacts.json`, with the same MIT notice,
  disposition map and validation record.

The SRC-010 source scope is accounted for, but responsive, keyboard and actual
zoom acceptance remains blocked. Its migration remains partial. The marketing
renderer verifies the recorded canonical mirror and notice before any writes; it
does not overwrite the vision page. See [SRC-010-lift.json](SRC-010-lift.json) and
[SRC-010-validation.md](SRC-010-validation.md).

The argument and fleet PDFs, plus the preserved older runspindle-paper.pdf, were generated with ReportLab, not compiled from TeX/Beamer. The new runspindle-paper.tex does not match that older PDF. Its five original schematic inputs and all 18 citations are prepared for independent source/build review; no native compilation or page review has occurred. See [BUILD.md](BUILD.md) for exact tools, reproduction commands and limits, and [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for source rights. None of these materials certifies a live implementation, runner, deployment or successful integration.

## Technical grounding for future presentations

Use [desired intent](../../specs/desired-intent.md) when revising conceptual
material. Explain how scoped access, session continuity, human exceptions and
evaluation can compose into maintained workflows. Keep planned capabilities
separate from measured outcomes and implemented components. Existing rendered
artifacts are unchanged; this link does not claim they were regenerated.

## Canonical SRC-013 paper

[workflow-refinery.pdf](workflow-refinery.pdf) and its [TeX source](workflow-refinery.tex)
mirror the independently reviewed Refinery paper at commit
`bfa8f760c1d56ec1c2ce07ea49e4d37ce4c01e5b` (merged in
`80a87f4569f1dfef14b141e141a89f30a9aaf7cd`). All eight historical figure PDFs,
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
No component Gitlink changed. Root integration remains dependent on PR 53 passing
and landing; issue 3 remains open until dependent integration passes and lands.

## Original SRC-002 source preparation

See [source review](SRC-002-review.md), [complete disposition](SRC-002-disposition.json),
[citation review](SRC-002-citations.json) and [proposed native build](SRC-002-build-plan.json).
The generator verifies source, preserved PDF and frozen economics before any
writes, then leaves both paper representations alone. It cannot be used to build
the new paper. Issue 4 remains open and selected-source migration remains partial.

## Full-scope presentation source preparation

[SRC-003-004-review.md](SRC-003-004-review.md) explains every-slide/variant scope,
rights exclusions and current component boundaries. The [disposition](SRC-003-004-disposition.json),
[citations](SRC-003-004-citations.json) and [source receipt](SRC-003-004-source-receipt.json)
separate the original edited sources from the unchanged older PDFs. No PDF
currently renders these new decks. The generator now uses only the Python standard
library and cannot rebuild any PDF or authored TeX. Native Beamer dependency
inventory, separate build review and all-page acceptance remain pending.
