# Build and verification

Status: newly authored Runspindle design documents, not implemented services.

The four PDF files here were rendered with ReportLab from the same narrative used to author the editable LaTeX and Beamer sources. They are **not** TeX-compiled or Beamer-rendered output. The static HTML pages need no dependencies or build service.

To reproduce the 14 generated narrative, HTML, LaTeX, PDF and notice outputs, use Python 3 with ReportLab installed and run `python build_documents.py` in this directory. This script does not fetch sources, access accounts, or make network requests. Retain BUILD, README, source license notice files and artifact/provenance manifests alongside the generated materials; the renderer does not regenerate those support files.

For a complete local TeX installation, the intended optional build is `pdflatex -no-shell-escape -interaction=nonstopmode -halt-on-error runspindle-paper.tex`, repeated for `workflow-refinery.tex`, `argument.tex`, and `fleet.tex`. Required packages include geometry, fontenc, lmodern, microtype, hyperref, enumitem, and Beamer for the decks. These TeX builds have not succeeded in the migration environment: installed binaries lack their format definitions and pdflatex initialization file. Do not describe these sources as compile-verified.

Verification completed: all 19 ReportLab PDF pages were rendered with Poppler and visually reviewed; text/HTML/TeX candidates were scanned for legacy repository references and operational identifiers. The documents describe planned components and do not transfer historical test results to Runspindle. No original source application or build script was executed. No JavaScript framework install was required for the new static pages. HTML browser-level visual verification remains pending.

## Reproducibility and migration status

Installed renderer: Python 3.12.14, ReportLab 4.4.9. ReportLab invariant mode is enabled to stabilize PDF metadata and identifiers. Determinism applies to these installed versions; cross-version byte identity is not asserted.

All materials remain partial migrations and new adaptations, not faithful re-renders of historical artifacts. The four PDFs are ReportLab outputs, not compiled TeX/Beamer.
