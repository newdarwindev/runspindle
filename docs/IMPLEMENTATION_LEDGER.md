# Implementation issue ledger

Initial inventory: **51 open issues and no open PRs**, observed 2026-11-13.
All 51 initial issues remain open with concrete unmet gates; none is closed by a
bounded synthetic slice. New live/provider issues created after this inventory
are outside this batch; no live calls or paid evaluation were performed.

The [machine-readable ledger](implementation-ledger.json) records every issue,
branch, exact reviewed head, PR, executed checks, merge commit and blocker.
Editing agents worked in isolated branches/clones inside the ignored workspace
`local/implementation/` directory. Only the coordinator merged.

## Review, checks and merge rules

The initial fourteen focused implementation/test/fix PRs merged after separate
exact-head review and required local checks. GitHub reports no required branch
status contexts or branch protections; normal exact-head squash merges used no
bypass. No visible qualified isolated runner exists, so GitHub Actions stays
unverified. Optional refinery CI wiring was rejected by the connected app's
workflow scope and removed without expanding credentials. Existing isolated
self-hosted workflows and fail-closed operational gates are unchanged.

Review found and corrected inherited console identity fields, stale pending
viewer admission, and Python bytecode substitution in fixture loaders. Final
regressions exercise each defect. Source and fixture revisions are distinct
from deployment evidence; every operational negative control remains blocked/78.

## Composition and sequencing

The initial tranche component changes merged in their own repositories first. Separate
[composition PR27](https://github.com/newdarwindev/runspindle/pull/27) advances
seven gitlinks and `composition.lock.json` together (merged as
`e3ece9b8a5d910c65a3754903519a621d440ed03`) after refreshing and rerunning
the exact component pins. Its `docs/composition-pin-checks.json` records commands,
versions, hashes and outcomes. No unmerged component pin is used.

The shared kit and all seven standalone Python consumers are available. Runtime
producer-consumer mappings, authenticated authority/store/retention interfaces
and qualified upstream protocols remain unresolved. Related F issue links name
interface owners; they do not require every related issue to finish before any
independent work can proceed. Complete component suites precede one-real-component
hero lanes; pinned integration and live acceptance remain separate gates.
Source-lift completeness separately needs exact private selected-source/dependency
and rights dispositions. Those records have not been imported or disclosed.

## Merged work

| PR | Exact reviewed head | Merge commit | Local checks / reviewer |
|---|---|---|---|
| [runspindle#20](https://github.com/newdarwindev/runspindle/pull/20) | `8f42ed515155` | `19171525f2df` | scaffold; 19 artifact hashes; attribution and AST checks; core |
| [runspindle#21](https://github.com/newdarwindev/runspindle/pull/21) | `019f3827fe43` | `e8cd5779968f` | 17 Python tests; fixture CLI; scaffold; 19 artifacts; core |
| [runspindle-core#6](https://github.com/newdarwindev/runspindle-core/pull/6) | `b50403338912` | `9f6c94d64aec` | 20 Rust tests; fmt; offline clippy; 3 detected mutations; scaffold; coordinator |
| [runspindle-refinery#7](https://github.com/newdarwindev/runspindle-refinery/pull/7) | `0fa93bf3b910` | `1c35a7bf77ff` | 22 Python lineage tests; scaffold; input hashes; console |
| [runspindle-console#4](https://github.com/newdarwindev/runspindle-console/pull/4) | `5430f4d78c67` | `fc9d046c42c4` | 14 Node tests; 3 detected mutations; scaffold; two review findings fixed; refinery |
| [runspindle-core#7](https://github.com/newdarwindev/runspindle-core/pull/7) | `b411ee5c4cc3` | `43d71d43fb91` | 11 Python + 20 Rust tests; fmt/clippy; 9 vectors; 3 mutations; scaffold; console and shared |
| [runspindle-host#3](https://github.com/newdarwindev/runspindle-host/pull/3) | `471e7597b197` | `ab34c149c613` | 7 Python + 1 Rust stub tests; fixture CLI; scaffold; core |
| [runspindle-browser#10](https://github.com/newdarwindev/runspindle-browser/pull/10) | `457129b030f2` | `a311af0dda71` | 7 Python + 1 Rust stub tests; fixture CLI; scaffold; core |
| [runspindle-refinery#8](https://github.com/newdarwindev/runspindle-refinery/pull/8) | `849b6f452578` | `94282d8246ff` | 33 Python tests; pre-execution source snapshot/cache regressions; scaffold; console |
| [runspindle-console#5](https://github.com/newdarwindev/runspindle-console/pull/5) | `2cb13692509a` | `dd4753aa05fe` | 7 Python + 14 Node tests; 3 mutations; scaffold; refinery |
| [runspindle-tether#4](https://github.com/newdarwindev/runspindle-tether/pull/4) | `f5a0b0996533` | `723ce9eb7fca` | 5 Python tests; fixture CLI; scaffold; shared |
| [runspindle-platform#5](https://github.com/newdarwindev/runspindle-platform/pull/5) | `aa3bb4981f6d` | `9afd8a5aa9dd` | 5 Python tests; fixture CLI; scaffold; shared |
| [runspindle-tether#5](https://github.com/newdarwindev/runspindle-tether/pull/5) | `b8fc2911ed4d` | `6003f2315146` | 6 Python tests; matching cache negative control; fixture CLI; scaffold; shared |
| [runspindle-platform#6](https://github.com/newdarwindev/runspindle-platform/pull/6) | `b2ce91a2b6d5` | `5d3f99931075` | 6 Python tests; matching cache negative control; fixture CLI; scaffold; shared |

## Temporal-first runtime tranche

This tranche starts at composition `4dd2ef1030b20c7a2061d2e23b0266935f508c58`.
The reviewed [runtime.v1 contract](../specs/runtime-v1.md) merged first in
[PR31](https://github.com/newdarwindev/runspindle/pull/31), as `4b700269be9a4feab7b955faf0229fbdd77d8aa9`.
The fixture format remains separate. Four editing agents use isolated clones;
review rotates platform → core → host → refinery → platform. The coordinator
alone performs normal exact-head merges after refreshed rules and required checks.
Independent agent recommendations are recorded as GitHub comments, not separate
GitHub-account approvals.

- [Host PR5](https://github.com/newdarwindev/runspindle-host/pull/5): reviewed
  `c5c3e981468441fc4e1d6ea8b8d6384e755672c2`, merged
  `3d329c68605a0e484592ede74493c615e6b90f8c`. Core independently checked
  19 Rust tests, 7 Python tests, formatting, offline Clippy and 3 mutations.
  Scripted transport evidence covers lost launch/reconnect/cancel and bounded queues;
  actual native protocol and durable host recovery remain blocked.
- [Refinery PR12](https://github.com/newdarwindev/runspindle-refinery/pull/12):
  reviewed `a7ba873dad0cc9b75f6f385cb64ecb103d2c0a94`, merged
  `355ad581e79f4cfce37e3d82192adb55da9b7669`. Host independently checked
  53 Python tests and 3 mutations. Review fixed passing with unresolved shared
  budget reservations and noninteger currency scale. Actual DSPy/provider/optimizer,
  durable storage, approval and serving remain absent.
- [Platform PR7](https://github.com/newdarwindev/runspindle-platform/pull/7):
  reviewed `959cd23959b758fa54f35d92ca410d053c6c3d62`, merged
  `96eb567ef32c68c52c19ea8fd77f11e5340e291b`. Refinery independently checked
  18 tests including 5 real Temporal lane cases, 2 mutations, license/source hashes
  and scaffold. Review fixed mutable prepared-image substitution and failed client
  deletion ownership. Linux arm64 development persistence, denied egress and
  cleanup are exercised; other dependencies/telemetry/distribution/CI are unqualified.

- [Core PR9](https://github.com/newdarwindev/runspindle-core/pull/9): reviewed
  `5d7e614c9e40690d83b0e7508fd861841743da41`, merged
  `d50e219c8df21b06bfdc2eba75e6a58ed9b4596e`. Platform independently checked
  27 Rust and 11 Python tests plus 18 real Temporal assertions and four history
  replays. Formatting, strict offline Clippy and three registry-code mutations pass.
  Review replaced a time-dependent cancellation test with a bounded atomic peer
  barrier; real history proves cancellation acceptance precedes the held Online
  completion, with zero launches for that race. It also fixed shared spy append
  atomicity, historical operation-ID reuse and mutable builder selection. Native
  freshness/wire, browser fencing, multi-registry/upgrade and production authority
  remain unqualified. The branch includes the concurrent reviewed guidance update.

[Exact-pin rechecks](temporal-pin-checks.json) are performed in a clean isolated
composition clone. Unrelated runner-fleet changes in the original platform
submodule are preserved and excluded. No runner provisioning, new credentials,
paid evaluation, external posting, production activation or source migration is
part of this tranche. Full issue acceptance remains open.

## Real-core composition development lane

[Pin PR32](https://github.com/newdarwindev/runspindle/pull/32) merged as
`3f8a1c683b0a9a7ca5dad41c2f5757bd5ff16a7d` after Host reviewed exact
`642be3865bd597cddb33ecd616e41f5687ebfd55`. [Scenario PR33](https://github.com/newdarwindev/runspindle/pull/33)
then exercises those exact pins. Its [two-run evidence](core-temporal-scenario-evidence.json)
records the real Rust core/Temporal boundary, scripted host and unexercised
browser/delivery/provider/console/refinery boundaries. One launch/one cancel,
worker/server recovery, real history replay and independent resource absence
passed twice. Normalized outcome, source, toolchain and fault-script hashes match.
Both commands return 78 because required system gates remain blocked/not-run.
The unrelated-image negative control blocks before execution. Twenty-nine
composition tests reject fabricated identity/session/effect/order/state/replay
and gate claims, poisoned bytecode, partial records and unavailable preparation.
This is partial issue #2 evidence, not full nine-step/system acceptance.

## Initial inventory disposition

“Partial merged” means the listed bounded work merged while the full issue
remains open. Each remaining blocker identifies an input/interface/qualification
that is required to complete the issue. All initial issues are listed once.

| Issue | Disposition and remaining blocker |
|---|---|
| [runspindle#1](https://github.com/newdarwindev/runspindle/issues/1) | partial merged. Native runtime mappings/qualification and full issue criteria remain incomplete. |
| [runspindle#2](https://github.com/newdarwindev/runspindle/issues/2) | blocked. Shared fixture-format conformance exists in all seven pinned repositories, but full component adapter suites and required one-real-component functions remain incomplete. Durable/authority/native/browser/Tether/telemetry/serving interfaces and upstream pins are unqualified, so required real-component/all-component lanes remain blocked/not-run. |
| [runspindle#3](https://github.com/newdarwindev/runspindle/issues/3) | blocked. Exact privately retained SRC-001 source-section/dependency closure and cleared rights/content dispositions are absent from these public checkouts; cannot verify completeness or import additional material. |
| [runspindle#4](https://github.com/newdarwindev/runspindle/issues/4) | blocked. Exact privately retained SRC-002 source-section/dependency closure and cleared rights/content dispositions are absent from these public checkouts; cannot verify completeness or import additional material. Actual TeX/Beamer source build is unverified; current ReportLab PDFs do not satisfy source-build acceptance. |
| [runspindle#5](https://github.com/newdarwindev/runspindle/issues/5) | blocked. Exact privately retained SRC-003 source-section/dependency closure and cleared rights/content dispositions are absent from these public checkouts; cannot verify completeness or import additional material. Actual TeX/Beamer source build is unverified; current ReportLab PDFs do not satisfy source-build acceptance. |
| [runspindle#6](https://github.com/newdarwindev/runspindle/issues/6) | blocked. Exact privately retained SRC-004 source-section/dependency closure and cleared rights/content dispositions are absent from these public checkouts; cannot verify completeness or import additional material. Actual TeX/Beamer source build is unverified; current ReportLab PDFs do not satisfy source-build acceptance. |
| [runspindle#7](https://github.com/newdarwindev/runspindle/issues/7) | partial merged. Attribution mismatch corrected; full source-section/citation disposition still needs exact private SRC-005 record and rights review. |
| [runspindle#8](https://github.com/newdarwindev/runspindle/issues/8) | blocked. Required functional dependencies remain incomplete: runspindle-tether#3, runspindle-core#2, runspindle-host#2, runspindle-core#5. Real-component and pinned integration lanes cannot be claimed from model fixtures; runtime contract agreement and composition #2 remain prerequisites. Shared test-only fixtures are available. |
| [runspindle#9](https://github.com/newdarwindev/runspindle/issues/9) | blocked. Required functional dependencies remain incomplete: runspindle-core#2, runspindle-core#3, runspindle-host#2. Real-component and pinned integration lanes cannot be claimed from model fixtures; runtime contract agreement and composition #2 remain prerequisites. Shared test-only fixtures are available. |
| [runspindle#10](https://github.com/newdarwindev/runspindle/issues/10) | blocked. Required functional dependencies remain incomplete: runspindle-browser#6, runspindle-core#2, runspindle-core#3, runspindle-host#2. Real-component and pinned integration lanes cannot be claimed from model fixtures; runtime contract agreement and composition #2 remain prerequisites. Shared test-only fixtures are available. |
| [runspindle#11](https://github.com/newdarwindev/runspindle/issues/11) | blocked. Required functional dependencies remain incomplete: runspindle-browser#7, runspindle-browser#6, runspindle-core#3. Real-component and pinned integration lanes cannot be claimed from model fixtures; runtime contract agreement and composition #2 remain prerequisites. Shared test-only fixtures are available. |
| [runspindle#12](https://github.com/newdarwindev/runspindle/issues/12) | blocked. Required functional dependencies remain incomplete: runspindle-browser#8, runspindle-core#3, runspindle-browser#6, runspindle-host#2. Real-component and pinned integration lanes cannot be claimed from model fixtures; runtime contract agreement and composition #2 remain prerequisites. Shared test-only fixtures are available. |
| [runspindle#13](https://github.com/newdarwindev/runspindle/issues/13) | blocked. Required functional dependencies remain incomplete: runspindle-browser#9, runspindle-console#3, runspindle-core#3, runspindle-browser#6. Real-component and pinned integration lanes cannot be claimed from model fixtures; runtime contract agreement and composition #2 remain prerequisites. Shared test-only fixtures are available. |
| [runspindle#14](https://github.com/newdarwindev/runspindle/issues/14) | blocked. Required functional dependencies remain incomplete: runspindle-core#4, runspindle-core#5, runspindle-tether#3. Real-component and pinned integration lanes cannot be claimed from model fixtures; runtime contract agreement and composition #2 remain prerequisites. Shared test-only fixtures are available. |
| [runspindle#15](https://github.com/newdarwindev/runspindle/issues/15) | blocked. Required functional dependencies remain incomplete: runspindle-platform#3, runspindle-host#2, runspindle-core#2, runspindle-core#3, runspindle-console#3. Real-component and pinned integration lanes cannot be claimed from model fixtures; runtime contract agreement and composition #2 remain prerequisites. Shared test-only fixtures are available. |
| [runspindle#16](https://github.com/newdarwindev/runspindle/issues/16) | blocked. Required functional dependencies remain incomplete: runspindle-console#3, runspindle-host#2, runspindle-browser#9, runspindle-platform#3, runspindle-core#4, runspindle-core#5. Real-component and pinned integration lanes cannot be claimed from model fixtures; runtime contract agreement and composition #2 remain prerequisites. Shared test-only fixtures are available. |
| [runspindle#17](https://github.com/newdarwindev/runspindle/issues/17) | blocked. Required functional dependencies remain incomplete: runspindle-refinery#4, runspindle-tether#3. Real-component and pinned integration lanes cannot be claimed from model fixtures; runtime contract agreement and composition #2 remain prerequisites. Shared test-only fixtures are available. |
| [runspindle#18](https://github.com/newdarwindev/runspindle/issues/18) | blocked. Required functional dependencies remain incomplete: runspindle-refinery#4, runspindle-refinery#5, runspindle-refinery#6, runspindle-core#3. Real-component and pinned integration lanes cannot be claimed from model fixtures; runtime contract agreement and composition #2 remain prerequisites. Shared test-only fixtures are available. |
| [runspindle#19](https://github.com/newdarwindev/runspindle/issues/19) | blocked. Required functional dependencies remain incomplete: runspindle-platform#4, runspindle-platform#3. Real-component and pinned integration lanes cannot be claimed from model fixtures; runtime contract agreement and composition #2 remain prerequisites. Shared test-only fixtures are available. |
| [runspindle-core#1](https://github.com/newdarwindev/runspindle-core/issues/1) | partial merged. One bounded registry authority per development namespace and simplified scripted host ports. Production identity/expiry, trusted native freshness/wire, browser fencing, artifact/delivery/provider adapters, multiple registries, upgrades, GitHub CI and live acceptance remain unqualified. |
| [runspindle-core#2](https://github.com/newdarwindev/runspindle-core/issues/2) | partial merged. One bounded registry authority per development namespace and simplified scripted host ports. Production identity/expiry, trusted native freshness/wire, browser fencing, artifact/delivery/provider adapters, multiple registries, upgrades, GitHub CI and live acceptance remain unqualified. |
| [runspindle-core#3](https://github.com/newdarwindev/runspindle-core/issues/3) | partial merged. One bounded registry authority per development namespace and simplified scripted host ports. Production identity/expiry, trusted native freshness/wire, browser fencing, artifact/delivery/provider adapters, multiple registries, upgrades, GitHub CI and live acceptance remain unqualified. |
| [runspindle-core#4](https://github.com/newdarwindev/runspindle-core/issues/4) | blocked. Trusted validator/approver and destination-policy adapter contracts are unresolved; model only compares supplied digests and cannot hash/authenticate bytes. Requires unresolved interfaces described in runtime contracts from #1/core #1. |
| [runspindle-core#5](https://github.com/newdarwindev/runspindle-core/issues/5) | blocked. Atomic durable delivery outbox/epoch contract and existing Tether transport are missing; accepted-byte recovery cannot be tested. Requires unresolved interfaces described in core #4/tether #3. |
| [runspindle-host#1](https://github.com/newdarwindev/runspindle-host/issues/1) | partial merged. Native app-server compatibility, platform capabilities and durable recovery remain unqualified. |
| [runspindle-host#2](https://github.com/newdarwindev/runspindle-host/issues/2) | partial merged. Native app-server compatibility, platform capabilities and durable recovery remain unqualified. |
| [runspindle-browser#1](https://github.com/newdarwindev/runspindle-browser/issues/1) | partial merged. Pinned standalone fixture conformance is implemented/merged; full component suite remains open. Authenticated principal/observation and durable lease-store/native-session interfaces plus qualified OpenBao/PinchTab/KasmVNC pins are unresolved; vault/profile/handoff mocks cannot qualify those interfaces. |
| [runspindle-browser#2](https://github.com/newdarwindev/runspindle-browser/issues/2) | blocked. Exact privately retained SRC-006 source-section/dependency closure and cleared rights/content dispositions are absent from these public checkouts; cannot verify completeness or import additional material. |
| [runspindle-browser#3](https://github.com/newdarwindev/runspindle-browser/issues/3) | blocked. Exact privately retained SRC-007 source-section/dependency closure and cleared rights/content dispositions are absent from these public checkouts; cannot verify completeness or import additional material. Public inert reference exists, but does not resolve the exact dependency/rights review or required trusted runtime/store interfaces. |
| [runspindle-browser#4](https://github.com/newdarwindev/runspindle-browser/issues/4) | blocked. Exact privately retained SRC-008 source-section/dependency closure and cleared rights/content dispositions are absent from these public checkouts; cannot verify completeness or import additional material. Public inert reference exists, but does not resolve the exact dependency/rights review or required trusted runtime/store interfaces. |
| [runspindle-browser#5](https://github.com/newdarwindev/runspindle-browser/issues/5) | blocked. Exact privately retained SRC-009 source-section/dependency closure and cleared rights/content dispositions are absent from these public checkouts; cannot verify completeness or import additional material. |
| [runspindle-browser#6](https://github.com/newdarwindev/runspindle-browser/issues/6) | blocked. No reviewed authenticated principal/origin-observation/durable lease interface or qualified OpenBao/PinchTab pins. Caller-provided scope is insufficient. Requires unresolved interfaces described in runtime contracts from #1/browser #1/core #2/host #2. |
| [runspindle-browser#7](https://github.com/newdarwindev/runspindle-browser/issues/7) | blocked. Encrypted checkpoint/key-store, integrity and exclusive writer/forgetting adapter contracts are unselected; qualified browser/session observation is absent. Requires unresolved interfaces described in browser #6/#9. |
| [runspindle-browser#8](https://github.com/newdarwindev/runspindle-browser/issues/8) | blocked. Durable effect-journal/readback contract and trusted browser native observation binding are absent. Unknown submissions cannot be retried safely. Requires unresolved interfaces described in browser #6/host #2/core #3. |
| [runspindle-browser#9](https://github.com/newdarwindev/runspindle-browser/issues/9) | blocked. Reviewed durable epoch/lease store, authenticated release authority and viewer-input closure/fencing acknowledgements are absent; no qualified KasmVNC/PinchTab pins. Requires unresolved interfaces described in browser #6/core #3. |
| [runspindle-tether#1](https://github.com/newdarwindev/runspindle-tether/issues/1) | partial merged. Pinned standalone fixture conformance is implemented/merged; full component suite remains open. Existing Tether selected source/dependency closure and runtime transport/event contract are unavailable; durable journal and trusted sanitization/authority interfaces are unresolved. |
| [runspindle-tether#2](https://github.com/newdarwindev/runspindle-tether/issues/2) | blocked. Exact privately retained SRC-014 source-section/dependency closure and cleared rights/content dispositions are absent from these public checkouts; cannot verify completeness or import additional material. |
| [runspindle-tether#3](https://github.com/newdarwindev/runspindle-tether/issues/3) | blocked. Existing selected Tether source/revision/runtime contract is not present in this repository; importing its exact dependency closure requires private source/rights review. No authenticated actor/native event/durable transport adapter. Requires unresolved interfaces described in core #2/host #2. |
| [runspindle-refinery#1](https://github.com/newdarwindev/runspindle-refinery/issues/1) | partial merged. Real DSPy/provider/optimizer/durable-store/approval/serving remain unqualified. |
| [runspindle-refinery#2](https://github.com/newdarwindev/runspindle-refinery/issues/2) | blocked. Exact privately retained SRC-012 source-section/dependency closure and cleared rights/content dispositions are absent from these public checkouts; cannot verify completeness or import additional material. Public inert reference exists, but does not resolve the exact dependency/rights review or required trusted runtime/store interfaces. |
| [runspindle-refinery#3](https://github.com/newdarwindev/runspindle-refinery/issues/3) | blocked. Exact privately retained SRC-013 source-section/dependency closure and cleared rights/content dispositions are absent from these public checkouts; cannot verify completeness or import additional material. Actual TeX/Beamer source build is unverified; current ReportLab PDFs do not satisfy source-build acceptance. |
| [runspindle-refinery#4](https://github.com/newdarwindev/runspindle-refinery/issues/4) | partial merged. Process-local lineage candidate; trusted Tether collection adapter, durable store and runtime wire agreement remain missing. |
| [runspindle-refinery#5](https://github.com/newdarwindev/runspindle-refinery/issues/5) | partial merged. Real DSPy/provider/optimizer/durable-store/approval/serving remain unqualified. |
| [runspindle-refinery#6](https://github.com/newdarwindev/runspindle-refinery/issues/6) | blocked. No independently authenticated approval authority, target serving-load acknowledgement contract or durable concurrent registry/store. Requires unresolved interfaces described in refinery #5/platform #4. |
| [runspindle-console#1](https://github.com/newdarwindev/runspindle-console/issues/1) | partial merged. Pinned standalone fixture conformance is implemented/merged; full component suite remains open. Actual UI and authorized stream/desktop backend adapters are absent; rendered keyboard/focus/a11y and JavaScript wire mapping remain untested. |
| [runspindle-console#2](https://github.com/newdarwindev/runspindle-console/issues/2) | blocked. Exact privately retained SRC-010 source-section/dependency closure and cleared rights/content dispositions are absent from these public checkouts; cannot verify completeness or import additional material. |
| [runspindle-console#3](https://github.com/newdarwindev/runspindle-console/issues/3) | partial merged. Process-local projection candidate; actual desktop/authority adapters and rendered keyboard/focus tests remain missing. |
| [runspindle-platform#1](https://github.com/newdarwindev/runspindle-platform/issues/1) | partial merged. Linux arm64 bounded development lane only. Other platform dependency/telemetry/distribution/runner/CI/live/production acceptance remains blocked. |
| [runspindle-platform#2](https://github.com/newdarwindev/runspindle-platform/issues/2) | blocked. Exact privately retained SRC-011 source-section/dependency closure and cleared rights/content dispositions are absent from these public checkouts; cannot verify completeness or import additional material. |
| [runspindle-platform#3](https://github.com/newdarwindev/runspindle-platform/issues/3) | blocked. Pinned native/Collector/Langfuse compatibility and permitted telemetry surfaces are unselected. Schema-URL masking gap remains unresolved; no real backend readback adapter. Requires unresolved interfaces described in runtime contracts from #1/host #2. |
| [runspindle-platform#4](https://github.com/newdarwindev/runspindle-platform/issues/4) | blocked. No qualified upstream source/image/toolchain digest set, target compatibility/license inventory or accepted component release. Disposable installed-byte/rollback adapter cannot be qualified. Requires unresolved interfaces described in platform #3. |
