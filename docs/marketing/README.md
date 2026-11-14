# Runspindle design adaptations

These are adaptations of selected historical material, not faithful re-renders or migrated live applications. SRC-013 is the full reviewed paper adaptation; the other narratives and decks remain concise derivatives. Historical source dependency closure is preserved privately. Overall selected-source migration remains partial.

- `runspindle-paper.pdf` and `.tex`: proposed system and evaluation argument.
- `argument.pdf`/`.tex`, `fleet.pdf`/`.tex`: two concise design decks.
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

The three other PDFs were generated with ReportLab, not compiled from TeX/Beamer. Their editable TeX sources are not compile-verified. See [BUILD.md](BUILD.md) for exact tools, reproduction commands and limits, and [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for source rights. None of these materials certifies a live implementation, runner, deployment or successful integration.

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
The remaining narratives and decks are concise derivatives, not this full paper.

No additional native compilation was performed for this mirror. The copied
`build-paper.py` is a reference CLI wrapper, not executed here or during the
recorded native build; its command/environment matches the executed native wrapper.
The receipt's `document_content_commit` is a local review identity, not a
fetchable public ref. Preserve original evidence; use separate integration evidence.
No runtime, benchmark, measured gains or live acceptance follows from this paper.
No component Gitlink changed. Root integration remains dependent on PR 53 passing
and landing; issue 3 remains open until dependent integration passes and lands.
