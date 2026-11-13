# runspindle

Composition and release boundary for seven pinned component repositories.

**Status: public scaffold, not a deployed or production-ready implementation.**

The core component includes a bounded in-memory identity/artifact contract model.
Its local synthetic tests do not establish runtime activation, durable effects or
system acceptance. See [implementation evidence and remaining gaps](docs/IMPLEMENTATION.md).

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
