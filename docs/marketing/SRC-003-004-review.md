# SRC-003 and SRC-004 presentation source review

Status: source preparation complete for independent review; native build and
all-page output acceptance **not run**. Issues 5 and 6 remain open. Overall
selected-source migration is partial.

## Selected scope and rights

Both selected historical PDFs contain ten slides built from a shared deck.
The fleet presentation replaces the mechanism and experiment fragments. All
20 original page instances, all five fragment files and the full 28-file retained
paper/presentation bundle are accounted for in SRC-003-004-disposition.json.
The exact source revision, original hashes, extracted text/links and private
review images remain outside this public repository.

No project-wide reuse license was established for the selected bundle. This
candidate does not import historical prose, diagram expression, plot coordinates,
style, binaries, embedded fonts or private navigation. Original prose and editable
native TeX tables retain the concepts, claim limits and evidence progression.
The completion, amortization and durability curves become explicit test questions
and scenarios rather than measured-looking charts. These are resolved expression
exclusions, not a claim that the original material has acquired a new license.
The selected paper-only inputs remain with the separately reviewed SRC-002 lift.

Every historical slide maps to named frames. The argument has 12 authored frames.
The fleet has 14 because its mechanism becomes separate identity, observation and
control frames. Both add two visible reference frames. These counts describe
editable source structure; they are not observed PDF page counts or new minimum
page requirements. No substantive source slide is silently dropped.

## Claims and dependencies

All six original deck method references were checked against primary pages.
SRC-003-004-citations.json retains their scope limits and bibliographic attribution.
The fleet study additionally cites the same repeated-trial methodology. Twelve
paper-only references are explicitly outside the deck citation set. Citation does
not authorize reproduction of the papers' figures or prose.

Economics remains consistent with the frozen SRC-005/SRC-002 narrative:
C = M + T + H + V + K + R + F, disjoint same-currency period costs, U = C/A only
for A > 0, and undefined unit cost at A = 0 even if C = 0. Failed work incurs cost.
No measurement, price, ROI or forecast is asserted. Native session identity and
explicit host/workspace pins remain distinct from process observation. Passive
viewing grants no control; interactive handoff needs fencing on the same browser.
A snapshot cannot prove continuous event mirroring. Unknown effects require
reconciliation. Seven repositories describe responsibilities rather than seven
mandatory network services. Live system acceptance remains not run.

The source uses stock Beamer, fontenc and Latin Modern. No executable package,
font file or binary image is imported. The new sources have not been compiled.
Installed Beamer/transitive dependencies and notices still need read-only
inventory and exact pins. SRC-003-004-build-plan.json identifies these gates and
required confinement; it contains no executable wrapper and grants no permission.
Existing paper toolchain inventories cannot certify this different dependency set.

## Preservation and generator behavior

The dependent base is public paper58 commit
bbc3b06fd0528ae604687dc84683a10b4304eede, tree
ed428ef02b9d3be35bced3a5c305def22dccdba1. All existing canonical SRC-010/SRC-013
mirrors, paper source/schematics, economics outputs and receipts remain unchanged.
The old argument.pdf and fleet.pdf remain byte-identical ReportLab derivatives;
they are **not renderings of the new argument.tex and fleet.tex**. Their old
uncompiled sources are preserved in presentations/legacy with exact hashes.

build_documents.py now generates only the two Markdown narratives, two static HTML
pages and the notices. It never renders a PDF or writes any authored TeX. Its old
ReportLab code and imports have been removed, without altering any preserved PDF.
The existing mirror and paper guards still run before writes, followed by the new
presentation guard. Positive tests execute the real generator twice with Python
site packages disabled. An import trap separately proves ReportLab is unnecessary;
negative mutations require rejection before any file changes in normal and
optimized Python. No check is skipped or replaced with unconditional success.
This dependency removal does not retroactively validate any earlier CI head.

## Reproducible source checks and remaining acceptance

From the repository root:

```
python3 -B -S tools/check_presentation_source.py
python3 -B -S tools/check_paper_source.py
python3 -B -S tools/check_economics_source.py
python3 -B -S -m unittest discover -s tests -p 'test_marketing_*.py' -v
python3 -B -S -O -m unittest discover -s tests -p 'test_marketing_*.py' -v
python3 tools/check_scaffold.py
python3 tools/validate.py
```

The checker is a bounded source/accounting preflight, not a TeX parser or security
sandbox. Exact source review and a separately approved confined native build are
still required. Record all loaded dependency hashes and exact build inputs; inspect
every resulting page image, extracted text, font and PDF link annotation. Preserve
prior receipts and record actual page count, toolchain and output hashes in new
evidence. Neither issue can close from source-only tests or the old PDFs.
