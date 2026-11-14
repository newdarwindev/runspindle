# Runspindle system contract

This is the complete reviewed SRC-001 requirement adaptation, not a report
of implemented or deployed behavior. Original source identity and hashes stay
in the private source record. [Coverage and rights review](../docs/core-product/README.md)
records the per-unit dispositions and reproducible artifact checks.

## Current repository boundaries

| Component | Responsibility |
|---|---|
| core | Rust/Temporal admission, durable coordination and accepted artifact receipts |
| host | Explicit machine/workspace binding and actual native sessions |
| browser | OpenBao-scoped secrets, encrypted profiles, PinchTab and fenced KasmVNC control |
| tether | Existing sanitized event/delivery and feedback integration |
| refinery | Python DSPy, replayable lineage, evaluation and approved serving |
| console | Actual observed views and freshness-aware projections, never authority |
| platform | Pinned upstream composition, local CI and target-specific distribution/rollback |

These are seven ownership/release boundaries, not seven required microservices.
Reuse Temporal, OpenBao, PinchTab, KasmVNC, standard Collectors, Langfuse and DSPy.
Do not introduce Slack Bolt, Presidio, Argilla or a separate Playwright service.
Versioned fixture, runtime, integration and maintained-evidence contracts retain
their existing meanings; the identifiers below introduce no runtime wire enums.

## Requirement and disposition inventory

Every source requirement and navigation reference has one stable opaque unit.
The JSON inventory is canonical; this section is a deterministic readable projection.
Owning specs are the pinned component versions in composition.lock.json, not
unqualified remote main branches. Full-slice gates below are not_run; related
bounded evidence retains its original scope and does not transfer to this lift.

### I01: Requirements index, not implementation

Disposition: **adapted**. Rewritten as current Runspindle requirements; original expression and legacy architecture are not imported.

Owners: core, platform.

- This contract assigns responsibility and acceptance obligations. Component specifications remain authoritative for their implementations; neither this index nor its validation grants execution authority or establishes runtime readiness.

Targets: [specs/system.md](../specs/system.md).

### B01: Product outcome

Disposition: **adapted**. Rewritten as current Runspindle requirements; original expression and legacy architecture are not imported.

Owners: core, host, browser, tether, refinery, console, platform.

- An authorized workflow must preserve the selected computer, account scope, control ownership and exact deliverable identity through completion and separately permitted learning.
- Credentials and account browsers are product capabilities. Packaging, CI, onboarding and public demonstrations support the workflow but cannot substitute for acceptance evidence.

Targets: [specs/system.md](../specs/system.md).

### B02: Shared identity, separate permission

Disposition: **adapted**. Rewritten as current Runspindle requirements; original expression and legacy architecture are not imported.

Owners: core, refinery.

- Connect execution and learning through immutable causal references. A grant for one path never supplies the approval needed by the other.

Targets: [specs/system.md](../specs/system.md).

### B03: Execution path

Disposition: **adapted**. Rewritten as current Runspindle requirements; original expression and legacy architecture are not imported.

Owners: core, host, browser, tether, console.

- Bind the authorized request to normalized intent, durable coordination, the explicitly selected host and leased native/browser session. Reconcile effects or artifact creation, validate and accept exact results, then retain delivery receipts and freshness-aware status.

Targets: [specs/system.md](../specs/system.md).

### B04: Learning path

Disposition: **adapted**. Rewritten as current Runspindle requirements; original expression and legacy architecture are not imported.

Owners: refinery, tether.

- Start with authorized immutable inputs and attributable outputs/feedback; produce replayable examples and locked splits, evaluate a bounded candidate, approve its exact digest, verify the serving version, and retain attribution into subsequent dataset revisions.

Targets: [specs/system.md](../specs/system.md).

### B05: No implicit authority

Disposition: **adapted**. Rewritten as current Runspindle requirements; original expression and legacy architecture are not imported.

Owners: core, browser, refinery, tether.

- Feedback, learned programs, issue descriptions and page content are inputs, not grants for another machine, account, operation, publication or provider transmission.

Targets: [specs/system.md](../specs/system.md).

### O01: Stable capability labels

Disposition: **adapted**. Rewritten as current Runspindle requirements; original expression and legacy architecture are not imported.

Owners: core, platform.

- P01–P10 label requirements, not tracker issue numbers or success states. Component owners maintain their own stories and tests; the source map replaces legacy links with the seven current repository boundaries.

Targets: [specs/system.md](../specs/system.md).

### P01: Scoped secret resolution

Disposition: **adapted**. Rewritten as current Runspindle requirements; original expression and legacy architecture are not imported.

Owners: browser, platform.

- Resolve only the secret required by the approved principal, account, exact origin, operation and current session/lease.
- A trusted injector verifies the observed top-level and target-frame origins before retrieval and again before use; supplied origin strings cannot authorize resolution.
- Wrong account/origin, stale lease, redirects, missing identity or vault failure deny access without fallback credentials.
- Keep secret values in the authorized helper, outside histories, telemetry, screenshots and public receipts. Use OpenBao rather than a replacement credential service.

Targets: [components/browser/specs/credentials-handoff.md](../components/browser/specs/credentials-handoff.md); [components/platform/specs/native-monitoring.md](../components/platform/specs/native-monitoring.md).

### P02: Isolated encrypted profiles

Disposition: **adapted**. Rewritten as current Runspindle requirements; original expression and legacy architecture are not imported.

Owners: browser.

- Account profile checkpoints require authenticated encryption and account isolation, with exclusive ownership of the active profile lease.
- Verify the restored account/browser identity before further use. Successful decryption or restoration is not proof of authentication and is not submission permission.
- Keep approved retention and explicit forgetting separate from cookie expiration, credential rotation and target-site revocation; none silently performs the others.

Targets: [components/browser/specs/credentials-handoff.md](../components/browser/specs/credentials-handoff.md).

### P03: Account-bound browser work

Disposition: **adapted**. Rewritten as current Runspindle requirements; original expression and legacy architecture are not imported.

Owners: browser, core.

- Associate observations and actions with the approved intent, account, browser instance, tab/target and current epoch.
- Keep an ambiguous submission unknown until independently observed outcome reconciliation; do not repeat it just because the response was lost.
- Use the selected PinchTab boundary for automation and do not create another Playwright automation service.

Targets: [components/browser/specs/credentials-handoff.md](../components/browser/specs/credentials-handoff.md); [components/core/specs/contracts.md](../components/core/specs/contracts.md).

### P04: Fenced human control

Disposition: **adapted**. Rewritten as current Runspindle requirements; original expression and legacy architecture are not imported.

Owners: browser, console.

- Acknowledge the fence on agent commands before granting interactive human control. A passive KasmVNC view carries no control capability.
- Resume only after the current holder authenticates release, all viewer inputs close, the expected epoch matches and fresh trusted account/target observations agree.
- Stale commands, forged release and missing observations grant no authority; interrupted ownership must survive restart without silent takeover.

Targets: [components/browser/specs/credentials-handoff.md](../components/browser/specs/credentials-handoff.md); [components/console/specs/fleet-view.md](../components/console/specs/fleet-view.md).

### P05: Pinned dispatch and sessions

Disposition: **adapted**. Rewritten as current Runspindle requirements; original expression and legacy architecture are not imported.

Owners: core, host.

- An explicit unavailable host remains queued; do not silently substitute a different host.
- Preserve durable job and operation identities and the actual native session/host binding across reconnect and restart.
- Reconcile a lost launch acknowledgement before another launch.
- Keep cancellation request, acknowledgement and observed termination separate. A cancelled request is not fabricated native completion.

Targets: [components/core/specs/host-runtime.md](../components/core/specs/host-runtime.md); [components/host/specs/durable-lifecycle.md](../components/host/specs/durable-lifecycle.md); [components/host/specs/native-sessions.md](../components/host/specs/native-sessions.md).

### P06: Exact accepted deliverables

Disposition: **adapted**. Rewritten as current Runspindle requirements; original expression and legacy architecture are not imported.

Owners: core, tether, console.

- Track produced, validated, accepted and delivered separately, including rejection, failure and unknown outcomes.
- Validation and acceptance refer to exact artifact bytes, digest, schema, revision and evidence; a mutable location cannot identify accepted content.
- After restart, deliver already accepted bytes without regenerating completed work; reconcile uncertain delivery before retry.
- Use existing Tether for authorized sanitized delivery, binding the receipt to the exact destination and artifact. Do not replace it with Slack Bolt.

Targets: [components/core/specs/durable-artifacts.md](../components/core/specs/durable-artifacts.md); [components/core/specs/durable-delivery.md](../components/core/specs/durable-delivery.md); [components/tether/specs/slack-events.md](../components/tether/specs/slack-events.md); [components/console/specs/fleet-view.md](../components/console/specs/fleet-view.md).

### P07: Attributable native telemetry

Disposition: **adapted**. Rewritten as current Runspindle requirements; original expression and legacy architecture are not imported.

Owners: platform, host.

- Retain producer/version, installed configuration digest, privacy-policy revision and task/native-session/trace/span/event identity.
- Distinguish emission, buffering, export, rejection, replay, duplication, loss and backend persistence. A successful local receiver response proves no backend record.
- Qualify privacy across the complete envelope, including schema URLs; unsupported sanitization blocks the path. Use native export and standard Collectors with qualified Langfuse readback, not a reconstruction receiver or uploader.

Targets: [components/platform/specs/native-monitoring.md](../components/platform/specs/native-monitoring.md); [components/host/specs/native-sessions.md](../components/host/specs/native-sessions.md).

### P08: Truthful observed status

Disposition: **adapted**. Rewritten as current Runspindle requirements; original expression and legacy architecture are not imported.

Owners: console, core, host, browser, platform.

- Project exact task, selected host, actual session, browser, trace and artifact references with observation timestamps and explicit stale, offline and unknown values.
- Show the operated desktop/browser only when that view is qualified; a simulation is not live integration evidence.
- Read models and passive views never authorize execution, credential retrieval or takeover.

Targets: [components/console/specs/fleet-view.md](../components/console/specs/fleet-view.md); [components/core/specs/contracts.md](../components/core/specs/contracts.md); [components/platform/specs/native-monitoring.md](../components/platform/specs/native-monitoring.md).

### P09: Replayable feedback lineage

Disposition: **adapted**. Rewritten as current Runspindle requirements; original expression and legacy architecture are not imported.

Owners: refinery, tether.

- Each usable example needs immutable source/input/output/context revisions and hashes, completeness, exact feedback target and attributable actor/provenance.
- Quarantine missing context, non-replayable labels and conflicting feedback instead of treating them as training examples.
- Keep related threads and revisions in one leakage-safe family partition.
- Existing Tether supplies separately permitted sanitized observations; collection does not authorize training or provider transmission. Do not introduce Argilla or Presidio as a replacement boundary.

Targets: [components/refinery/specs/experiments.md](../components/refinery/specs/experiments.md); [components/refinery/specs/durable-offline.md](../components/refinery/specs/durable-offline.md); [components/tether/specs/slack-events.md](../components/tether/specs/slack-events.md).

### P10: Evaluated approved serving

Disposition: **adapted**. Rewritten as current Runspindle requirements; original expression and legacy architecture are not imported.

Owners: refinery.

- Use Python DSPy within explicit data/provider authority and cumulative budgets. Compare baseline and candidate on the same locked held-out cases with quality, safety, latency and measured cost; missing measurements remain unknown.
- Promotion requires approval for the exact candidate bytes, evaluation evidence, policy and serving target. A passing score or caller-provided actor string is not approval.
- Verify the serving process actually loaded the approved digest; rejected loading preserves the previous approved candidate.
- Rollback verifies a compatible approved predecessor and changes future serving without rewriting the attribution of earlier outputs.

Targets: [components/refinery/specs/experiments.md](../components/refinery/specs/experiments.md); [components/refinery/specs/durable-offline.md](../components/refinery/specs/durable-offline.md).

### C01: Request to native session

Disposition: **adapted**. Rewritten as current Runspindle requirements; original expression and legacy architecture are not imported.

Owners: core, host, tether.

- Carry request revision, delivery ID, semantic intent ID, policy revision, job/operation identity and authorized host/workspace/action. Delivery duplication cannot create another intent.
- Core retains the selected host; host records the observed native session. Offline pins queue and unknown launch acknowledgements reconcile before effect retry.
- Preserve requested, acknowledged and verified cancellation/termination as different facts, including after restart.

Targets: [specs/runtime-v1.md](../specs/runtime-v1.md); [specs/runtime-integration-v1.md](../specs/runtime-integration-v1.md); [components/core/specs/host-runtime.md](../components/core/specs/host-runtime.md); [components/host/specs/durable-lifecycle.md](../components/host/specs/durable-lifecycle.md).

### C02: Browser and credential scope

Disposition: **adapted**. Rewritten as current Runspindle requirements; original expression and legacy architecture are not imported.

Owners: browser, core, host, console.

- Core passes scoped references, never secret values; browser resolves them only for the approved principal/account/origin/operation and active lease.
- Trusted top-level and frame-origin observations precede secret retrieval and injection.
- Preserve account, browser instance, tab/target, holder and epoch across handoff. Fence agent effects before interactive control; authenticate release and reobserve identity before return.
- Neither stored credentials, restored profiles nor passive viewing grants submission or control authority.

Targets: [components/browser/specs/credentials-handoff.md](../components/browser/specs/credentials-handoff.md); [specs/runtime-v1.md](../specs/runtime-v1.md); [components/console/specs/fleet-view.md](../components/console/specs/fleet-view.md).

### C03: Artifacts to delivery receipts

Disposition: **adapted**. Rewritten as current Runspindle requirements; original expression and legacy architecture are not imported.

Owners: core, tether, console.

- Separate production, validation, acceptance and delivery. Bind schema, validation evidence and acceptance to exact immutable bytes and revision.
- Tether receipts preserve accepted digest, delivery operation and authorized destination; Console only projects observed status.
- Resume delivery from accepted stored bytes after restart; independently reconcile ambiguous effects before any permitted retry, never regenerate or blindly resend.

Targets: [specs/runtime-integration-v1.md](../specs/runtime-integration-v1.md); [components/core/specs/durable-artifacts.md](../components/core/specs/durable-artifacts.md); [components/core/specs/durable-delivery.md](../components/core/specs/durable-delivery.md); [components/tether/specs/slack-events.md](../components/tether/specs/slack-events.md).

### C04: Telemetry to projections

Disposition: **adapted**. Rewritten as current Runspindle requirements; original expression and legacy architecture are not imported.

Owners: host, platform, console, tether.

- Carry source/producer version, installed configuration, policy revision and native-session/task/trace/span/event references without private content.
- Keep emission, queued/exported, rejected, persisted, replayed, duplicate and lost measurements distinct. Backend readback must correlate the same identities.
- Preserve observation time, freshness and unknowns in Console and sanitized Tether projections. Neither a process listing nor local HTTP success authorizes a completion claim.

Targets: [components/platform/specs/native-monitoring.md](../components/platform/specs/native-monitoring.md); [components/console/specs/fleet-view.md](../components/console/specs/fleet-view.md); [specs/maintained-evidence-v1.md](../specs/maintained-evidence-v1.md).

### C05: Dataset to serving attribution

Disposition: **adapted**. Rewritten as current Runspindle requirements; original expression and legacy architecture are not imported.

Owners: tether, refinery.

- Preserve source/input/output revisions and hashes, completeness, exact feedback target and actor/provenance; unusable context stays quarantined.
- Keep related revisions within one partition and bind approved candidate bytes to locked evaluation evidence.
- Require observed serving digest and output attribution; failed loading preserves the prior approved version, and rollback never changes earlier attribution.

Targets: [components/refinery/specs/experiments.md](../components/refinery/specs/experiments.md); [components/refinery/specs/durable-offline.md](../components/refinery/specs/durable-offline.md); [specs/maintained-evidence-v1.md](../specs/maintained-evidence-v1.md).

### A00: Synthetic slice, not a run

Disposition: **adapted**. Rewritten as current Runspindle requirements; original expression and legacy architecture are not imported.

Owners: core, platform.

- Exercise these obligations only through separately authorized bounded tests with invented records, synthetic accounts and controlled targets.
- Reuse the composition test work in issue #1 and existing lanes. This artifact lift adds documentation validation, not a second runtime harness.

Targets: [docs/FIXTURE_KIT.md](../docs/FIXTURE_KIT.md); [specs/runtime-integration-scenarios-v1.json](../specs/runtime-integration-scenarios-v1.json).

### G01: Admit and dispatch

Disposition: **adapted**. Rewritten as current Runspindle requirements; original expression and legacy architecture are not imported.

Owners: core, host, tether.

- Require policy/admission decision, immutable intent, authorized selected host and an actual native/session receipt.
- Reject scope expansion, queue an offline host pin and reconcile unknown launch acknowledgement without duplicate launch.

Targets: [docs/H02-integration-evidence.json](../docs/H02-integration-evidence.json); [specs/runtime-integration-v1.md](../specs/runtime-integration-v1.md).

Full-slice status: **not_run**; evidence class: requirement_not_execution. Existing lane reference: H02.

Requirements: P05, C01. Reuse [composition issue #1](https://github.com/newdarwindev/runspindle/issues/1). Existing bounded results remain at their own exact revisions; they do not establish this full slice or transfer to newer code.

### G02: Open the scoped account

Disposition: **adapted**. Rewritten as current Runspindle requirements; original expression and legacy architecture are not imported.

Owners: browser, core.

- Require a non-secret scoped-reference receipt and current trusted account, origin, browser and lease observations.
- Wrong account or origin must fail before secret resolution; restored profiles do not bypass identity checks.

Targets: [components/browser/specs/credentials-handoff.md](../components/browser/specs/credentials-handoff.md).

Full-slice status: **not_run**; evidence class: requirement_not_execution. Existing lane reference: no qualified integrated lane.

Requirements: P01, P02, P03, C02. Reuse [composition issue #1](https://github.com/newdarwindev/runspindle/issues/1). Existing bounded results remain at their own exact revisions; they do not establish this full slice or transfer to newer code.

### G03: Transfer control safely

Disposition: **adapted**. Rewritten as current Runspindle requirements; original expression and legacy architecture are not imported.

Owners: browser, console.

- Require observed agent fencing, the human control lease, authenticated release and fresh account/browser identity.
- Reject stale commands and forged release. Restart preserves unresolved ownership, rather than restoring agent authority.

Targets: [components/browser/specs/credentials-handoff.md](../components/browser/specs/credentials-handoff.md).

Full-slice status: **not_run**; evidence class: requirement_not_execution. Existing lane reference: no qualified integrated lane.

Requirements: P04, C02. Reuse [composition issue #1](https://github.com/newdarwindev/runspindle/issues/1). Existing bounded results remain at their own exact revisions; they do not establish this full slice or transfer to newer code.

### G04: Reconcile a synthetic submission

Disposition: **adapted**. Rewritten as current Runspindle requirements; original expression and legacy architecture are not imported.

Owners: browser, core.

- Record the exact approved intent and an independently observed target outcome.
- A response timeout remains unknown until reconciliation; no blind duplicate submission.

Targets: [components/browser/specs/credentials-handoff.md](../components/browser/specs/credentials-handoff.md).

Full-slice status: **not_run**; evidence class: requirement_not_execution. Existing lane reference: no qualified integrated lane.

Requirements: P03, C02. Reuse [composition issue #1](https://github.com/newdarwindev/runspindle/issues/1). Existing bounded results remain at their own exact revisions; they do not establish this full slice or transfer to newer code.

### G05: Accept and deliver exact bytes

Disposition: **adapted**. Rewritten as current Runspindle requirements; original expression and legacy architecture are not imported.

Owners: core, tether, console.

- Require actual artifact digest, validation and acceptance identities, exact authorized destination and observed delivery receipt.
- Changed bytes cannot inherit acceptance; coordinator restart resumes delivery without regenerating already accepted work.

Targets: [docs/H07-integration-evidence.json](../docs/H07-integration-evidence.json); [specs/runtime-integration-v1.md](../specs/runtime-integration-v1.md).

Full-slice status: **not_run**; evidence class: requirement_not_execution. Existing lane reference: H07.

Requirements: P06, C03. Reuse [composition issue #1](https://github.com/newdarwindev/runspindle/issues/1). Existing bounded results remain at their own exact revisions; they do not establish this full slice or transfer to newer code.

### G06: Read back the same task

Disposition: **adapted**. Rewritten as current Runspindle requirements; original expression and legacy architecture are not imported.

Owners: platform, host, console.

- Correlate exact task/session/event identity with synthetic backend readback and fresh Console observations.
- Process existence, export claims and local HTTP acknowledgement cannot substitute for backend persistence or a fresh projection.

Targets: [docs/MAINTAINED_OFFLINE.md](../docs/MAINTAINED_OFFLINE.md); [specs/maintained-evidence-v1.md](../specs/maintained-evidence-v1.md).

Full-slice status: **not_run**; evidence class: requirement_not_execution. Existing lane reference: H08.

Requirements: P07, P08, C04. Reuse [composition issue #1](https://github.com/newdarwindev/runspindle/issues/1). Existing bounded results remain at their own exact revisions; they do not establish this full slice or transfer to newer code.

### G07: Build replayable examples

Disposition: **adapted**. Rewritten as current Runspindle requirements; original expression and legacy architecture are not imported.

Owners: tether, refinery.

- Verify immutable input/output/context, exact feedback revision and actor, lineage hashes and usable-row validation.
- Missing or contradictory context is quarantined and related revisions cannot leak between splits.

Targets: [docs/FEEDBACK_HERO.md](../docs/FEEDBACK_HERO.md); [docs/MAINTAINED_OFFLINE.md](../docs/MAINTAINED_OFFLINE.md).

Full-slice status: **not_run**; evidence class: requirement_not_execution. Existing lane reference: H10.

Requirements: P09, C05. Reuse [composition issue #1](https://github.com/newdarwindev/runspindle/issues/1). Existing bounded results remain at their own exact revisions; they do not establish this full slice or transfer to newer code.

### G08: Evaluate, approve and serve

Disposition: **adapted**. Rewritten as current Runspindle requirements; original expression and legacy architecture are not imported.

Owners: refinery.

- Require locked split, paired baseline/candidate metrics, exact approval, observed serving digest, versioned outputs and rollback evidence.
- Missing metrics, altered bytes, unauthorized promotion or worse quality block promotion; failed loading keeps the earlier approved artifact.

Targets: [docs/MAINTAINED_OFFLINE.md](../docs/MAINTAINED_OFFLINE.md); [specs/maintained-evidence-v1.md](../specs/maintained-evidence-v1.md).

Full-slice status: **not_run**; evidence class: requirement_not_execution. Existing lane reference: H11.

Requirements: P10, C05. Reuse [composition issue #1](https://github.com/newdarwindev/runspindle/issues/1). Existing bounded results remain at their own exact revisions; they do not establish this full slice or transfer to newer code.

### A09: Per-gate evidence, never a blanket pass

Disposition: **adapted**. Rewritten as current Runspindle requirements; original expression and legacy architecture are not imported.

Owners: core, platform.

- Record not_run, passed, failed, blocked and unknown separately, with exact source/config/artifact revisions, timestamp, environment and evidence class.
- Distinguish synthetic, component, isolated integration and live acceptance. Document completeness is a separate artifact result, not a successful product gate.

Targets: [docs/IMPLEMENTATION.md](../docs/IMPLEMENTATION.md).

### M01: Owner specifications

Disposition: **adapted**. Rewritten as current Runspindle requirements; original expression and legacy architecture are not imported.

Owners: core, platform.

- Component repositories own detailed stories, tests and implementation semantics; this index owns responsibility and cross-boundary requirements.

Targets: [AGENTS.md](../AGENTS.md); [specs/desired-intent.md](../specs/desired-intent.md).

### M02: Change-to-evidence trace

Disposition: **adapted**. Rewritten as current Runspindle requirements; original expression and legacy architecture are not imported.

Owners: core, platform.

- Each implementation change names its story, updates exact evidence and states the remaining gap. A commit alone does not complete a feature.

Targets: [AGENTS.md](../AGENTS.md); [specs/desired-intent.md](../specs/desired-intent.md).

### M03: No historical result transfer

Disposition: **adapted**. Rewritten as current Runspindle requirements; original expression and legacy architecture are not imported.

Owners: core, platform.

- Bind every result to the source, configuration and artifact actually tested. Isolated success does not prove authenticated use, live recovery, full source migration or independently verified restoration.

Targets: [AGENTS.md](../AGENTS.md); [specs/desired-intent.md](../specs/desired-intent.md).

### M04: Separate observations

Disposition: **adapted**. Rewritten as current Runspindle requirements; original expression and legacy architecture are not imported.

Owners: core, platform, console.

- Keep source checks, installed state, invocation, backend readback and user acceptance as separate claims.

Targets: [AGENTS.md](../AGENTS.md); [specs/desired-intent.md](../specs/desired-intent.md).

### M05: Private operational material

Disposition: **adapted**. Rewritten as current Runspindle requirements; original expression and legacy architecture are not imported.

Owners: core, platform.

- Exclude real credentials, runtime ledgers, private source expression, recovery material and machine-specific identities from public specifications, fixtures and evidence.

Targets: [AGENTS.md](../AGENTS.md); [specs/desired-intent.md](../specs/desired-intent.md).

### M06: No activation through documentation

Disposition: **adapted**. Rewritten as current Runspindle requirements; original expression and legacy architecture are not imported.

Owners: core, platform.

- Preserve disabled workflows and existing approval boundaries. Requirements grant no permission to deploy, activate services, enroll telemetry, incur spending, publish data or schedule recurring work.

Targets: [AGENTS.md](../AGENTS.md); [specs/desired-intent.md](../specs/desired-intent.md).

### M07: Archived applications remain archived

Disposition: **adapted**. Rewritten as current Runspindle requirements; original expression and legacy architecture are not imported.

Owners: core, platform.

- Historical archived applications are outside this product boundary. This lift neither reopens nor activates them.

Targets: [AGENTS.md](../AGENTS.md); [specs/desired-intent.md](../specs/desired-intent.md).

### X01: Historical product coordination

Disposition: **excluded**. Replace the legacy product issue link with the current intent; no historical issue body is selected or imported.

Owners: core, platform.

- Use the listed current target; the historical navigation destination is retained privately for review only.

Targets: [specs/desired-intent.md](../specs/desired-intent.md).

### X02: Historical dispatch coordination

Disposition: **excluded**. Replace the legacy dispatch issue link with the current core/host contract; no historical discussion or runtime record is imported.

Owners: core, platform.

- Use the listed current target; the historical navigation destination is retained privately for review only.

Targets: [specs/runtime-integration-v1.md](../specs/runtime-integration-v1.md).

### X03: Historical learning coordination

Disposition: **excluded**. Replace the legacy lineage issue link with the current Refinery seam; linked source expression is not selected.

Owners: core, platform.

- Use the listed current target; the historical navigation destination is retained privately for review only.

Targets: [specs/maintained-evidence-v1.md](../specs/maintained-evidence-v1.md).

### X04: Historical repository-session index

Disposition: **excluded**. Omit the legacy relative index and its device/session details; current host ownership supplies the requirement boundary.

Owners: core, platform.

- Use the listed current target; the historical navigation destination is retained privately for review only.

Targets: [components/host/specs/native-sessions.md](../components/host/specs/native-sessions.md).

### X05: Historical execution-workflow index

Disposition: **excluded**. Omit the legacy relative workflow page; current explicit lifecycle requirements replace its navigation role.

Owners: core, platform.

- Use the listed current target; the historical navigation destination is retained privately for review only.

Targets: [specs/desired-intent.md](../specs/desired-intent.md).

### X06: Historical private infrastructure context

Disposition: **excluded**. Exclude private infrastructure navigation and operational context. Current sanitized platform requirements replace only its boundary role.

Owners: core, platform.

- Use the listed current target; the historical navigation destination is retained privately for review only.

Targets: [components/platform/specs/native-monitoring.md](../components/platform/specs/native-monitoring.md).

### X07: Historical reports are not current proof

Disposition: **adapted**. Rewritten as current Runspindle requirements; original expression and legacy architecture are not imported.

Owners: core, platform.

- Verify current exact revisions and evidence before changing a completion claim. Preserve earlier failures and limitations even when later work improves the implementation.

Targets: [docs/IMPLEMENTATION.md](../docs/IMPLEMENTATION.md).
