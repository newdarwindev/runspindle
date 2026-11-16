# Browser SRC-009 composition mirror

This source-only derivative adopts the reviewed Browser product page from
[Browser PR 48](https://github.com/newdarwindev/runspindle-browser/pull/48), merged
at `dfc9ac3e51abba8e84ab217a5eec5358b2088a3f`, tree
`81ae9a5ea4dd310c89e537f551ca2465730d7eac`. The
[canonical HTML](https://github.com/newdarwindev/runspindle-browser/blob/dfc9ac3e51abba8e84ab217a5eec5358b2088a3f/docs/product/browser.html)
and its original source-accounting records remain owned by Browser. Independent
source review found no blocker to this canonical heading-wrap change; that review
did not inspect the private original or approve visual baselines. The earlier
Browser CI receipt in the mapping is explicitly historical, not qualification of
this candidate. Browser issue 5 remains open. This root derivative requires
independent review before publication, and does not change any component Gitlink
or runtime pin.

## Precisely bounded transformation

The root [browser.html](browser.html) is **not byte-identical** to the canonical
page. [SRC-009-mirror.json](SRC-009-mirror.json) records both hashes, every exact
replacement, expected occurrence count and verified public target identity.

- L01–L06 change the six Browser specification links to immutable Browser blob
  URLs. Root specifications with similar names are not substituted.
- L07–L08 link the source review and notices to their immutable Browser originals.
  Their document closures are not broadly copied into this repository.
- L09 replaces the snapshot's pending composition-mirror sentence with an
  explicit source-only mirror statement. Root-derivative rendered and keyboard
  gates remain open.
- L10 fixes the canonical-location footer and adds this transformation disclosure.
- The three product-page links remain local: index.html, browser.html and
  vision.html. Their destinations are present and checked. Page-fragment links
  remain unchanged and resolve to existing unique anchors.

All nine immutable external destinations, including the canonical HTML, were read
from the clean Browser checkout at the recorded merge commit. Their content
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
mirror checks. The canonical Browser page has a separately recorded local Chrome
candidate at 320/390/768/1440 CSS pixels and a keyboard focus probe; its reference
images are not approved baselines. A separate local Chrome DOM probe of this
normalized root derivative at 195/320/390/768/1440 CSS pixels found no document
or inspected-element overflow, missing fragment targets or hidden diagram stages;
the first Tab reached the visible outlined skip link. It used disposable synthetic
browser state and did not establish visual baseline approval, actual browser zoom,
manual keyboard navigation or assistive technology behavior. Its rendered/keyboard
acceptance therefore remains **not run** in the source-mapping receipt. Source
synchronization does not complete those gates or close Browser issue 5. The exact final root
commit/tree and check results belong in the separate review/publication receipt.
