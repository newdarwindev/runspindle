# Browser SRC-009 composition mirror

This source-only derivative adopts the reviewed Browser product page from
[Browser PR 24](https://github.com/newdarwindev/runspindle-browser/pull/24), merged
at `a5446d9fab1f2384b0d2ea0a051b7fd56a8af00b`, tree
`03f5e9d2f0388ea8f948de2b0c85e065eef877ba`. The
[canonical HTML](https://github.com/newdarwindev/runspindle-browser/blob/a5446d9fab1f2384b0d2ea0a051b7fd56a8af00b/docs/product/browser.html)
and its original source-accounting records remain owned by Browser. Its exact-head
push CI passed; that result is not rendered, mobile, keyboard or runtime acceptance.
Browser issue 5 remains open. This root candidate requires independent review
before publication, and does not change any component Gitlink or runtime pin.

## Precisely bounded transformation

The root [browser.html](browser.html) is **not byte-identical** to the canonical
page. [SRC-009-mirror.json](SRC-009-mirror.json) records both hashes, every exact
replacement, expected occurrence count and verified public target identity.

- L01–L06 change the six Browser specification links to immutable Browser blob
  URLs. Root specifications with similar names are not substituted.
- L07–L08 link the source review and notices to their immutable Browser originals.
  Their document closures are not broadly copied into this repository.
- L09 replaces the snapshot's pending composition-mirror sentence with an
  explicit source-only mirror statement. Rendered and keyboard gates remain open.
- L10 fixes the canonical-location footer and adds this transformation disclosure.
- The three product-page links remain local: index.html, browser.html and
  vision.html. Their destinations are present and checked. Page-fragment links
  remain unchanged and resolve to existing unique anchors.

All nine immutable external destinations, including the canonical HTML, were read
through the connected repository API at the recorded merge commit. Their content
and Git blob hashes are recorded. That read verifies repository-file existence,
not browser navigation or permanent hosting availability. Opening those links
requires network access; they are ordinary navigation, not automatic page assets.

Reversing only the ten recorded substitutions reconstructs the exact canonical
HTML hash. All prose outside the two location/status sentences, every diagram
relationship, ordered stage, style byte and evidence limitation remain unchanged.
No historical expression, dependency or private-source locator is added. Rights
and exclusions remain described by the canonical Browser notices; no blanket
license is inferred from GitHub visibility or the unrelated MIT notices here.

## Generator guard and preservation

The obsolete browser.html writer is removed from build_documents.py. Its four
other outputs remain economics.md, overview.md, index.html and
THIRD_PARTY_NOTICES.md, with unchanged content and behavior. The existing Console,
Refinery, paper and presentation source guards remain in order before the Browser
guard and before any generated-file write. The Browser check requires fixed
canonical and derivative hashes, the exact transformation receipt, safe regular
local targets and unchanged pending evidence status. Rehashing a modified page
or receipt cannot approve a new canonical source or a new transformation.

The generator never rebuilds Browser HTML, paper inputs, authored decks, PDFs,
canonical Console files or the canonical Refinery closure. Two-run tests execute
only temporary copied folders and require every preexisting byte to stay identical.
Negative tests include missing/tampered/repinned source records, CSS/network
injection, wrong links, missing local destinations, symlinks and fake acceptance;
they must fail before touching even unrelated generated-output sentinels.

## Reproduction and remaining gates

Run from the repository root:

    python3 -B -S tools/check_browser_mirror.py
    python3 -O -B -S tools/check_browser_mirror.py
    python3 -m unittest discover -s tests -p 'test_marketing_browser.py' -v
    python3 -O -m unittest discover -s tests -p 'test_marketing_browser.py' -v
    python3 tools/check_scaffold.py
    python3 tools/check_artifacts.py
    python3 tools/validate.py

The full source suite and separately prepared pinned H10 seam remain required;
H10 is existing bounded integration evidence and does not exercise this page.
No browser/native renderer, live account, service or deployment is invoked by the
mirror checks. Actual desktop/mobile rendering, keyboard navigation, zoom and
assistive-technology acceptance are still not run. Source synchronization does
not complete those gates or close Browser issue 5. The exact final root
commit/tree and check results belong in the separate review/publication receipt.
