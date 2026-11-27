# Paper and deck visual review

These review candidates cover the current editable TeX for the paper, argument
deck and fleet deck. Each document has its own input and output hashes,
page geometry, extracted reading text and contact sheet. The candidate build
preserves the published PDFs and the existing source-disposition maps.

| Source | Pages | Visual reference | Text alternative | Evidence |
| --- | ---: | --- | --- | --- |
| [Research paper](runspindle-paper.tex) | 12 | [Contact sheet](visual-review/paper/contact-sheet.png) | [Reading text](visual-review/paper/text.txt) | [SRC-002 receipt](visual-review/paper/receipt.json) |
| [Argument deck](argument.tex) | 12 | [Contact sheet](visual-review/argument/contact-sheet.png) | [Reading text](visual-review/argument/text.txt) | [SRC-003 receipt](visual-review/argument/receipt.json) |
| [Fleet deck](fleet.tex) | 14 | [Contact sheet](visual-review/fleet/contact-sheet.png) | [Reading text](visual-review/fleet/text.txt) | [SRC-004 receipt](visual-review/fleet/receipt.json) |

The fleet deck gives separate frames to native identity, event continuity and
passive viewing versus fenced control. The cost slides preserve the original
accounting definitions, including the undefined unit-cost case at zero accepted
outcomes. The paper retains the synthetic economics illustration and its
applicable source disposition.

The first render showed body prose starting on the line occupied by several
slide tables. The updated editable fragments end those table paragraphs before
applying vertical spacing. The archived ReportLab deck exports remain at their
original paths. The authored-source receipts still distinguish them from these
offline TeX candidates.

## Rebuild and compare

Use macOS arm64 and the exact local binaries and prepared Tectonic cache bound
by [the render profile](document-visual-toolchain.json), with Python 3.13 and
Pillow 12.2.0. The prepared cache is a prerequisite. The command checks every
file digest and uses a private scratch copy. The third-party bundle, cache and
fonts are external dependencies.

```sh
python3 tools/document_visual_baselines.py \
  --cache-home /path/to/prepared-tectonic-home \
  --output /path/to/new/review-output \
  --compare docs/marketing/visual-review
```

Compilation uses Tectonic's cached, untrusted mode inside the macOS sandbox.
Network access is denied, the source and cache are read-only, and writes go
to disposable build output. The command emits each compiled PDF, PNG for
every page, contact sheet, extracted text and evidence receipt. It compares
the hashes and recorded results against the retained reference set.
Keep any locally generated PDFs required for a review, then remove the
scratch output.

## Review state

The captured pages and slides fit their native geometry. The lane verifies
text bounds, records minimum extracted word-box heights for review, inventories
embedded fonts and validates the exact external link targets against the source
citations. It records untagged PDFs separately; the extracted text offers a
review aid and carries no reading-order conformance claim.

The notes on the paper's Latin Modern fonts also identify the applicable
font package license. The decks also embed a Computer Modern subset from the
prepared bundle. The committed reference set contains raster images and text.
The local PDF bytes are bound in the receipts.
[Latin Modern notices](SRC-002-NOTICES.md) · [Computer Modern package](https://ctan.org/pkg/cm)

These references await independent baseline approval and dependency-notice review.
Document migration, artifact publication approval and runtime acceptance remain
open.
