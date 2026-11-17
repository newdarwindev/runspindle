# RUNSPINDLE

## Persistent work across applications, machines and time

A request should become a continuing piece of work: explicit authority, a selected
machine, recoverable execution and a result its owner can inspect. **RUNSPINDLE**
connects those boundaries instead of replacing the specialist software beneath them.

**Current status:** implemented component libraries and bounded local integrations,
not a deployed or production-qualified system. Ordinary text below describes the
implemented boundaries; *italics mark upcoming work or qualification*. A conceptual
screen is not evidence that its depicted workflow is implemented.

[![Conceptual recurring-work gallery: authorized inputs, intervention and reviewed results](https://newdarwindev.github.io/runspindle_for_bloomberg/gallery/01.webp)](https://newdarwindev.github.io/runspindle_for_bloomberg/assets/Runspindle_Gallery_Index.html#page-01)

Concept illustration from [Runspindle for Bloomberg](https://github.com/newdarwindev/runspindle_for_bloomberg),
page 1: fictional jobs and proposed UI, not a screenshot of a deployed console.

## User journeys: what the boundaries are for

These examples connect the seven responsibilities to work an owner can recognize.
**Verified building blocks** means the named bounded behavior was tested, not that
the entire live journey works. *Italic text marks missing implementation or qualification.*
The Bloomberg examples are paper/concept workflows, not trading instructions or
claims of licensed data access.

### Keep ongoing work continuous and correctable

| What the owner does | Intended experience and responsible boundary | Evidence boundary |
| --- | --- | --- |
| “Continue my coding task on the same machine.” | **CORE + HOST** reconcile the existing task/native-session mapping after a disconnect instead of starting a duplicate or silently changing machines. The result is continuity, or an explicit unresolved outcome. | [Bounded recovery qualification](docs/COMPOSITION_PIN_FOLLOWTHROUGH.md) uses a scripted host. *Actual native-runtime/OS qualification remains.* |
| “Stop this task.” | **CORE + HOST + TETHER** stop newly authorized effects and distinguish confirmed, failed and unknown effects already sent. Cancellation is not represented as an undo. | Controlled-peer revocation/interruption evidence exists. *Live provider cancellation is separate.* |
| “Actually, use the corrected figures.” | **TETHER + CORE** bind an edit to a new exact revision and reject duplicates/conflicts; stale work gains no new permission. | Durable bridge and constrained same-author signed-edit paths exist. *Complete live ingress and deletion-actor handling remain.* |
| “Send me the finished report.” Its confirmation disappears. | **TETHER + CORE** keep the attempted delivery identity and reconcile independent readback before any retry; an unknown upload does not become an automatic duplicate. | [Durable upload contract](https://github.com/newdarwindev/runspindle-tether/blob/main/specs/durable-slack-upload-v1.md) has controlled-peer evidence. *Full live Slack delivery/readback remains.* |
| “Continue reconciling this invoice.” The account session needs restoring. | **BROWSER + CORE** check the intended account, origin and current authority before using a profile; resume or request intervention. | Local encrypted-profile and guarded-effect components exist. *The complete real-account restoration journey is unqualified.* |
| “Show me the work; let me take over.” | **CONSOLE + HOST + BROWSER** associate observation with the exact task/session, keep watching separate from control, and require current authority for handback. | Projection/passive-status components exist. *Authenticated live viewing and full rendered takeover/handback integration remain.* |

### Turn recurring business work into reviewable results

| What the owner asks | Intended experience and responsible boundary | Evidence boundary |
| --- | --- | --- |
| “Make tomorrow's bakery prep sheet from paid orders.” | **TETHER + CORE + BROWSER** carry approved orders through pack-size/quantity checks into a source-linked prep sheet; incomplete coverage becomes a review item. | [Gallery page 3](https://newdarwindev.github.io/runspindle_for_bloomberg/assets/Runspindle_Gallery_Index.html#page-03) is illustrative. *Commerce ingestion, business rules and live acceptance are upcoming.* |
| “Match invoice #107 to the order and payment.” | **CORE + BROWSER + CONSOLE** preserve exact record identity, compare values, pause on ambiguity and reconcile an uncertain write rather than repeat it. | [Gallery page 4](https://newdarwindev.github.io/runspindle_for_bloomberg/assets/Runspindle_Gallery_Index.html#page-04) is a concept built around implemented identity/effect primitives. *Accounting adapters and live readback remain.* |
| “That pack size was wrong. Use six next time.” | **TETHER + REFINERY** attach the correction to the exact output/source, check permitted use, then evaluate a candidate on held-out examples. A correction is not automatic production promotion. | Feedback lineage, consent, budgets and candidate identity are implemented. *Representative model evaluation and approved live serving remain.* |
| “Upgrade the component, but preserve my feedback history.” | **REFINERY + TETHER** keep the old receipt immutable and require fresh source/consent checks before creating a current-pin receipt. | [Actual old/new-source qualification](https://github.com/newdarwindev/runspindle-refinery/pull/50) passed. Live use still needs its own authorization. |

### Explore data-dependent workflows without confusing concepts with live products

| Illustrative question | Proposed workflow and reviewable outcome | Current limit |
| --- | --- | --- |
| “Did this stock really break its price threshold?” | **CORE + CONSOLE** would bind comparable closes and a dividend event, expose the adjustment, and produce a paper decision or pause, never an order. | [Case 10 synthetic contract/prototype](https://github.com/newdarwindev/runspindle_for_bloomberg/blob/main/pilot/case-10-contract-v0.1.md). *Terminal access, financial-domain validation and live integration are unqualified.* |
| “Find a genuinely independent backup supplier.” | **CORE + BROWSER + CONSOLE** would use supplier relationships to flag alternatives sharing an upstream producer, then compare approved stock and evidence. | [Catalog case 2](https://github.com/newdarwindev/runspindle_for_bloomberg/blob/main/assets/runspindle_bloomberg_workflows.csv), using Bloomberg SPLC, is fictional. *Data rights, procurement adapters and inventory verification remain.* |
| “Was this royalty converted at the contracted FX rate?” | **CORE + BROWSER** would match fixing date, benchmark and deductions, draft a discrepancy for approval, and close it only against verified credit. | [Catalog case 5](https://github.com/newdarwindev/runspindle_for_bloomberg/blob/main/assets/runspindle_bloomberg_workflows.csv), using BFIX, is fictional. *Entitled/licensed data access, portals and settlement readback remain.* |
| “Trace the dividend missing after my custody transfer.” | **CORE + BROWSER + TETHER** would match the security/event and both custody records, prepare an approved inquiry and distinguish actual recovery from an unrelated credit. | [Catalog case 8](https://github.com/newdarwindev/runspindle_for_bloomberg/blob/main/assets/runspindle_bloomberg_workflows.csv), using CACT/DVD, is fictional. *Account access, entitlement, approval and credit verification remain.* |

### Make the infrastructure uphold the same standard

When a developer starts another verification run after a crash, **PLATFORM** checks
durable capacity state. A damaged database is rejected instead of rebuilding empty
occupancy tables and falsely reporting free capacity. This [bounded implemented
scenario](https://github.com/newdarwindev/runspindle-platform/pull/42) protects the
work above; *deployed-fleet and remaining architecture qualification are separate*.

## One workflow, seven responsibilities

**TETHER — COMMUNICATION WITH PROVENANCE.** Slack supplies the conversation surface;
[TETHER](https://github.com/newdarwindev/runspindle-tether) supplies versioned events,
sanitation, durable journal coordination and exact output/destination identities.
Its Core bridge reconciles revisions without treating a duplicate as permission to
repeat an effect. *Authenticated live ingress and complete provider-backed delivery
remain separately qualified work.*

**CORE — DURABLE INTENT AND EFFECTS.** [Temporal](https://temporal.io/) supplies durable
workflow progression; SQLite supplies local durable records. [CORE](https://github.com/newdarwindev/runspindle-core)
adds scoped admission, immutable operation/host bindings and explicit uncertain
outcomes. Its [bounded F02 acceptance](https://github.com/newdarwindev/runspindle-core/issues/2)
includes interruption/revocation and pinned old-to-new upgrade evidence, not a
whole-system sign-off. *Live issuers, native peers, arbitrary upgrades and power-loss
qualification remain outside that acceptance.*

**HOST — CONTINUITY ON THE SELECTED MACHINE.** [Codex CLI](https://github.com/openai/codex)
remains an agent runtime. [HOST](https://github.com/newdarwindev/runspindle-host) wraps
session lifecycle and durable identity mappings; scripted-peer tests cover lost
launch replies, reconnects and cancellation races. *Actual native protocol and
per-operating-system compatibility still need their own qualification.*

**BROWSER — ACCOUNT CONTINUITY AND CONTROL.** [OpenBao](https://openbao.org/) and
[PinchTab](https://github.com/pinchtab/pinchtab) provide the selected secret-management
and browser-control foundations. [BROWSER](https://github.com/newdarwindev/runspindle-browser)
adds credential-reference checks, control leases, guarded effects and encrypted
profile components. *The full real-account lifecycle, production key custody and
live takeover/handback remain qualification work.*

**CONSOLE — TRUTHFUL OPERATOR OBSERVATION.** [CONSOLE](https://github.com/newdarwindev/runspindle-console)
implements a bounded state projection that rejects stale or mismatched observations.
[KasmVNC](https://github.com/kasmtech/KasmVNC) is the selected viewing route, not a
replacement desktop server built here. *Rendered fleet UI, authenticated live feeds
and actual supported desktop viewers are not established by projection tests.*

**REFINERY — MEASURED IMPROVEMENT.** [DSPy](https://dspy.ai/) supplies optimization;
[REFINERY](https://github.com/newdarwindev/runspindle-refinery) supplies lineage,
feedback-use controls, budgets, candidate identity and serving admission. Its
scripted/local lanes do not establish real model-quality gains. *Representative
workload evaluation and approved live serving remain separate gates.*

**PLATFORM — REPRODUCIBLE OPERATION.** [QEMU](https://www.qemu.org/), systemd,
[OpenTelemetry](https://opentelemetry.io/) and [Langfuse](https://langfuse.com/) provide
execution and observability foundations. [PLATFORM](https://github.com/newdarwindev/runspindle-platform)
adds pinned preparation, runner-state checks, monitoring contracts and evidence
accounting. *Fleet deployment and live backend readback need explicit qualification.*

## Explore the product idea, then inspect the evidence

The [visual product library](https://newdarwindev.github.io/runspindle_for_bloomberg/)
expresses the product thesis as “Observe → decide → verify”: useful work leaves a
checkable record. The following materials explain the ambition, not production results:

- [16-page product concept](https://github.com/newdarwindev/runspindle_for_bloomberg/blob/main/assets/runspindle_bloomberg_product.pdf): two proposed workflow modes.
- [37-page gallery](https://github.com/newdarwindev/runspindle_for_bloomberg/blob/main/assets/Runspindle_Revised_Gallery.pdf) and [page/source index](https://newdarwindev.github.io/runspindle_for_bloomberg/assets/Runspindle_Gallery_Index.html): conceptual interfaces and fictional cases.
- [40-workflow catalog](https://github.com/newdarwindev/runspindle_for_bloomberg/blob/main/assets/runspindle_bloomberg_workflows.csv): source-linked scenarios, not measured outcomes.
- [Research proposal](https://github.com/newdarwindev/runspindle_for_bloomberg/blob/main/assets/runspindle-paper.pdf) and [full-cost model](https://github.com/newdarwindev/runspindle_for_bloomberg/tree/main/economics): evaluation questions, not claimed savings.
- [Asset provenance and claim boundaries](https://github.com/newdarwindev/runspindle_for_bloomberg/blob/main/ASSETS.md). Assets remain linked at their source; no new license grant or Bloomberg affiliation is implied.

For implementation evidence, start with the [exact composition-pin qualification](docs/COMPOSITION_PIN_FOLLOWTHROUGH.md),
[authority integration](docs/AUTHORITY_COMPOSITION.md) and [current status](STATUS.json).
The Core–Tether–Platform slice is bounded; H10 and live/full-system acceptance remain
separate. Standalone component main branches can be newer than the pinned composition.

This repository is one boundary of [Runspindle](https://github.com/newdarwindev/runspindle). Repository boundaries do not require one microservice each.

- Read [specifications](specs/README.md), [agent guidance](AGENTS.md), [provenance](provenance.json), [status](STATUS.json) and [legal status](LEGAL.md).
- Run `python3 tools/check_scaffold.py` for structural validation only.
- Operational entrypoints and acceptance gates deliberately fail closed until implemented.
- GitHub Actions use isolated **self-hosted local runners only**. No GitHub-hosted fallback. Runner capacity is not established by publishing workflows.
- No credentials, real sessions, messages, datasets, browser profiles or live host inventory belong here.

No old repository is retired by this scaffold. Migration and archival are separate verified gates.

## Composition layout

```text
runspindle/
  components/
    core/       # runspindle-core submodule
    host/       # runspindle-host submodule
    browser/    # runspindle-browser submodule
    tether/     # runspindle-tether submodule
    refinery/   # runspindle-refinery submodule
    console/    # runspindle-console submodule
    platform/   # runspindle-platform submodule
  specs/
  docs/
  composition.lock.json
```

Clone with `git clone --recurse-submodules https://github.com/newdarwindev/runspindle.git`. Component Git links and `composition.lock.json` must agree.

See the [per-repository workflow table](docs/CI_PLAN.md) and [migration gates](docs/MIGRATION.md).

The [technical coverage map](docs/migration/technical-coverage.md) distinguishes preserved requirements and references from unverified implementation.

New conceptual documentation is in [docs/marketing](docs/marketing/README.md). Its published PDFs are ReportLab adaptations; TeX compilation and runtime acceptance are not established.

## Implemented validation

Run `python3 tools/validate.py` for all implemented structural, language, fixture, artifact and mutation checks in this repository. The same entrypoint runs on trusted `main` and `ci/*` pushes and manual qualification using disposable Strix x64 guests. Logs include the checkout SHA, image/tool identities, command results and applicable artifact checksums. Unimplemented builds and product acceptance remain explicit in `STATUS.json`; blocked acceptance workflows retain their failing conclusions. ARM64 and native macOS qualification remain pending.

## Desired technical direction

Composition and maintained workflows: this component contributes to turning authorized one-off work into
repeatable, maintained cross-application workflows. Scoped access, managed
sessions, explicit human exceptions and evaluated DSPy candidates are intended
to compose into that capability; no automatic improvement or live integration
is implied.

Read [the component-specific technical intent](specs/desired-intent.md) for its
interfaces, privacy boundaries, failure cases and acceptance obligations. Current
implementation and evidence limits above remain unchanged.

The [H02/H07 runtime integration lanes](docs/RUNTIME_INTEGRATION.md) now exercise
real core/host/Temporal and durable accepted-byte delivery through scripted peers.
Repeated offline passes remain separate from blocked native/Tether/full-system
and live acceptance. Exact reviewed pins and remaining gaps are in the
[implementation ledger](docs/IMPLEMENTATION_LEDGER.md).

## Offline development bundle

The separately qualified [Linux arm64 development bundle](docs/OFFLINE_BUNDLE.md)
packages core, its Temporal prerequisite, refinery/DSPy dependencies and platform
helpers. A saved launcher verifies and executes installed bytes with disposable
upgrade/rollback recovery and denied external egress. This manual offline lane is
separate from fleet architecture qualification. [Exact evidence](docs/offline-finish-evidence.json)
retains blocked Langfuse/native/Tether/full-system gates and the user-waived
independent review; no review or production activation is implied.

## Bounded evidence reconciliation

The composition includes an offline [exact-source evidence reconciler](docs/EVIDENCE_RECONCILIATION.md)
for issue criteria, component pins, capabilities, receipts and README/STATUS claim
mappings. Local synthetic tests cover invalid evidence and independent effect
observations. Private campaign packet reconciliation returned non-success for draft, historical,
dirty and incomplete observations. Isolated runner qualification remains blocked. Integrated system implementation and live acceptance remain absent.
