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
