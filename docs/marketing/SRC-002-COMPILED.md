# SRC-002 compiled paper candidate

This candidate binds the actual two-pass PDF to six exact edited-source inputs:
the master and five original schematic fragments. It is not a historical paper
re-render. The source was taken from local reviewed commit
`9844e5af51d03d7d1cd9e4284ce591ea2a00feff` (tree
`5ce7fe57377918aeba09d3ac6dfcea873a6d5440`). This is a local review identity, not a
fetchable public ref. Use the containing checkout and the six hashes in
[SRC-002-source-receipt.json](SRC-002-source-receipt.json) to reproduce.

Later integration with public main
`60759ff3564ed1e61d6596edfe4a864d7989d2ab` preserves those six bytes. The integrated
repository tree was not compiled as a whole. Its Browser/mirror guards and
registration changes do not require another native compilation of unchanged
inputs. The additive integration validation records the final containing tree.

## Build and document evidence

[SRC-002-build-evidence.json](SRC-002-build-evidence.json) records the actual
output hash, size, two-pass audit and sanitized review results.
[SRC-002-toolchain.json](SRC-002-toolchain.json) distinguishes 121 known pins from
104 observed loaded stock inputs per pass, six authored inputs and two expected
auxiliary inputs. A known-pin inventory is not proof that every pin was loaded.
No unreviewed dependency was admitted.

The native review covered all 12 pages, nine sections and five schematics;
citations and figure references resolve. It checked 54 annotations: 22 URI
rectangles representing 18 exact bibliography URLs, and 32 internal GoTo links.
Nine Latin Modern Type 1 fonts are embedded and subset with Unicode maps. No
flagged active-content keys were found; the ordinary page-navigation OpenAction
is not a script. Five Underfull warnings remain, visually readable in the
page 3/4 tables and bibliography entry 13 on page 11. There are no Overfull or
unresolved-reference warnings in the final pass. These observations do not
establish a generally safe PDF parser or future external URL availability.

Independent cloud review of the exact transferred PDF also passed: all 12 pages
were rendered and inspected, with the same annotation counts. Final review of the
integrated source/evidence tree remains pending. This does not close an issue,
publish the candidate, establish runtime acceptance,
or grant any operational authority. Overall source migration remains partial.

## Reproduction, not the private executed wrapper

The exact executed confinement wrapper and raw logs remain privately retained.
Public evidence identifies their hashes without disclosing native home paths,
process observations or namespace identities. No new executable builder is
introduced by this integration. The earlier SRC-002-build-plan.json remains an
unchanged historical proposal, not a receipt of the later execution.

The following is a public reproduction recipe for an independently reviewed
installation matching the recorded stock toolchain. It is not the exact private
executed command, does not reproduce its confinement/resource supervision, and
must not be used to process unreviewed TeX. No installation, network access or
permission change is part of this recipe. Use a fresh private output directory,
keep all logs, and stop on any unexpected dependency, input, write or error.
From docs/marketing, prepare two empty output directories and run the command
below for pass 1, replacing OUTPUT_DIR with the first directory. After checking
its log and FLS against the exact source and stock pins, copy only
runspindle-paper.aux and runspindle-paper.out to the second directory and run
pass 2 with that directory. Do not overwrite repository artifacts automatically.

```sh
env MKTEXFMT=0 MKTEXTFM=0 MKTEXPK=0 MKTEXMF=0 MKTEXTEX=0 MKTEXOFM=0 \
  shell_escape=0 openin_any=p openout_any=p \
  SOURCE_DATE_EPOCH=1794614400 FORCE_SOURCE_DATE=1 TZ=UTC \
  LANG=C.UTF-8 LC_ALL=C.UTF-8 \
  pdflatex -no-shell-escape -no-parse-first-line \
  -no-mktex=tex -no-mktex=tfm -no-mktex=pk \
  -interaction=nonstopmode -halt-on-error -file-line-error -recorder \
  -output-directory=OUTPUT_DIR runspindle-paper.tex
```

This short recipe inherits the caller's search paths and differs from the clean
fixed-path environment in the actual private wrapper. Pin and review those paths
before a reproduction; portable output and byte-for-byte identity are not
promised. The actual build used pdfTeX 1.40.29 / TeX Live 2026 Debian, stock article,
geometry, fontenc, lmodern, amsmath, amssymb, graphicx and hyperref, with
shell escape, first-line parsing and automatic generation disabled. No BibTeX,
TikZ, historical figure binary or additional package install was used.

For repository consistency, run from the repository root:

```sh
python3 -B -S tools/check_paper_source.py
python3 -B -S tools/check_economics_source.py
python3 -B -S tools/check_presentation_source.py
python3 -B -S tools/check_browser_mirror.py
python3 -B -S tools/check_scaffold.py
python3 -B -S tools/check_artifacts.py
```

These are static checks, not re-execution of the native build or its visual audit.
The text generator runs all current paper, presentation, Browser and canonical
mirror preflights before any writes and never writes a PDF or authored TeX.
The prior ReportLab paper is retained at paper/legacy/reportlab-paper.pdf.
See [font/source notices](SRC-002-NOTICES.md), original [dispositions](SRC-002-disposition.json)
and [citation limits](SRC-002-citations.json). Excluded original expression is a
resolved adaptation choice, not an outstanding requirement to acquire reuse rights.
