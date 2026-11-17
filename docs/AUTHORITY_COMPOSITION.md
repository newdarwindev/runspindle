# Bounded Core, Tether and Platform composition qualification

[PR #76](https://github.com/newdarwindev/runspindle/pull/76) qualifies a specific
three-component slice, not a production release or full-system acceptance.
The tested composition source is `317d175fec0693e1b36ae5aa2848332e6be8340a`.
[Machine-readable receipt](authority-composition-qualification.json) preserves
original report/log hashes, runtime/source hashes and explicit exclusions.

## Exact merged pins

| Component | Pin |
| --- | --- |
| Core #33 | `18b5d65392b176e1ab6c4b65ac27e941f530956c` |
| Tether #39 | `5e5fdb73422926d015657166e9ef60b293c01e50` |
| Platform | `398c74766b9ec9f7203256e17dea34f1b15cac4c` |

Host, Browser, Refinery and Console pins are unchanged. The qualifier checks the
actual merged checkouts, not an uncommitted source approximation. Tether #40 and
later changes are not covered. These merge trees equal the reviewed component
heads; the runtime manifest independently checks the exact compiled source bytes.

## Results

| Check | Result |
| --- | --- |
| Exact-pin aggregate | All 7 top-level checks passed, including 13 nested legacy/component checks |
| Core Python / verified-authority Rust | 108 / 100 passed |
| Composition normal / optimized | 364 discovered each, 3 existing skips each |
| Tether normal / optimized | 425 discovered each, 1 existing renderer skip each |
| Core formatting / strict Clippy | Passed |
| Deliberate authority/state mutations | All 5 killed; sources restored |
| Authenticated and exact-destination authority | Two actual Temporal/SQLite runs each passed |
| Semantic journal bridge | Two 7-phase runs passed, each 6 launches / 3 cancels and cleanup |
| Python/Rust intent and batch conformance | Passed exact independent fixture digests |
| Composition static gate | Failed identically on base and candidate: 399 existing debt plus 62 unbaselined findings; no new candidate diagnostics, baseline unchanged |

The three composition skips and renderer skip do not count as integration or
visual acceptance. The bounded aggregate does not replace the broader mandatory
quality/release gates or claim those failing gates passed. External host and
provider effects remain scripted, while Core, Tether SQLite journal, current
Ed25519/SQLite authority and disposable Temporal are real components.

## Core #2 criterion reconciliation

[The Core audit](https://github.com/newdarwindev/runspindle-core/blob/18b5d65392b176e1ab6c4b65ac27e941f530956c/docs/AUTHENTICATED_CHECKPOINTS.md)
maps every original F02 acceptance criterion. This composition run adds exact
merged pins to that evidence; it does not reclassify the original checkpoint run.

- Duplicate/conflict/revision behavior is exercised by real authority integrations
  and the actual Tether atomic journal feeding the Rust semantic consumer.
- Real fresh-process Temporal/SQLite restart and history replay retain identity;
  independent scripted ledgers reject a second or alternate-host effect.
- A caller's actor string or approval flag does not replace current signed
  authority; forged, expired, revoked and misbound inputs are tested.
- The separately retained Core #33 matrix exercises 44 interruption cases and six
  actual old-executable upgrades at its exact tested source. It is **historical
  component evidence**, not 50 additional executions by this composition command.
- Five behavioral mutations, exact independent conformance fixtures and forbidden
  effect assertions are retained alongside the repeated integration observations.

The Core F02 issue concerns bounded admission and identity, not live provider
activation. Any closure decision must cite this exact reviewed/merged slice and
retain its limits; H10, Tether #8 and production/full-system gates remain separate.
Revoked pre-dispatch Unknown is unresolved, not completed execution or terminal
cancellation. No atomic revocation-versus-external-effect guarantee is claimed.

## H10 remains deliberately blocked

The unchanged Refinery component requires Tether `c3fbfb9…`, not the new `5e5fdb7…`
pin. Historical H10 manifests, evidence and runtime `verify_sources` remain
unchanged. A regression explicitly checks that the mismatch still rejects before
import. We did not rewrite a prior H10 pass as evidence for new component bytes.
A separately reviewed dependency upgrade and actual H10 qualification are needed.
Current core-product artifact reference pins/hash metadata were reconciled only;
that artifact still says runtime acceptance is not run.

## Reproduction

Prepare all seven exact gitlinks, the approved pinned builder and the verified
Core/Platform runtime manifests. The retained legacy Tether fixture source is
required at its existing exact pin; use the component instructions. With clean
sources and a new report directory:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 tools/qualify_authority_pins.py \
  --core-prepared "$CORE_PREPARED" \
  --platform-prepared "$PLATFORM_PREPARED" \
  --report-dir "$NEW_REPORT_DIRECTORY"
```

The harness never fetches a replacement image, changes host security settings or
uses a live provider. Prepared manifest hashes and clean exact source pins are
checked before and after. Earlier failed preflight receipts are retained in the
machine-readable evidence; the final entire aggregate reran after setup and
metadata corrections. Independent final receipt review is recorded separately.
