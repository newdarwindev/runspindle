# Runspindle system contract

Adapted from the selected core-product map. See `provenance.json` for the opaque source reference; the exact original revision and hash are retained in the private provenance record. This document describes requirements, not completed functionality.

## Two connected paths

Execution: authorized request → normalized intent → Temporal workflow → explicitly selected host → native agent/browser session → reconciled effect or artifact → validation and acceptance → delivery receipt.

Learning: immutable permitted input/output/feedback → replayable task-specific examples → leakage-safe split → bounded DSPy experiment → held-out evaluation → exact approved candidate digest → attributed serving version and rollback. Feedback cannot expand action authority.

## Repository owners

| Repository/submodule | Responsibility |
|---|---|
| runspindle-core | Rust coordination, Temporal activities, identity mapping and artifact receipts |
| runspindle-host | Native Codex app-server sessions, selected hosts, reconnect and capture capabilities |
| runspindle-browser | Central OpenBao-scoped credentials, encrypted profiles, PinchTab operation, KasmVNC viewing and fenced handoff |
| runspindle-tether | Extend existing Tether for supported session events, sanitization and Slack delivery reconciliation |
| runspindle-refinery | Python DSPy, exact-output reaction/reply gold rules, conflict quarantine, candidate evaluation/approval |
| runspindle-console | Actual fleet/session/desktop/trace views and truthful freshness |
| runspindle-platform | Pinned upstream composition, local CI, installation bundles and target-specific deploy/rollback |

These are source/release boundaries, not seven mandatory microservices. Retain supported upstream functionality rather than reimplementing Temporal, OpenBao, PinchTab, KasmVNC, Collectors, Langfuse or DSPy. Do not introduce Slack Bolt, Presidio, Argilla or a separate new Playwright automation service.

## Identity and authority

Correlate request revision, delivery ID, semantic intent, policy revision, job, selected host/workspace/action and actual native session. Repeated delivery is not repeated intent. Offline host pins queue rather than migrate silently. Reconcile lost launch acknowledgements and unknown website submissions before retry.

Credentials use account/origin/operation references, not secret values in orchestration histories. Trusted runtime observations verify top-level and target-frame origins before retrieval and field use. Profile restoration is not proof of login or permission to submit. Keep durable retention and explicit forgetting independent from cookie expiry and target-site revocation.

A passive viewer never receives control merely by opening a view. Fence stale agent commands before takeover. Authenticated release, current epoch and fresh account/browser observations are required for handback. Persist authority across restart.

Artifacts progress through produced, validated, accepted and delivered states bound to exact bytes. A mutable URL cannot stand in for a digest. Restart may resume delivery of accepted bytes without regenerating work.

Telemetry preserves producer/configuration version, task/session/trace/event IDs and privacy policy. Report emitted, queued, rejected and persisted separately, plus known duplication/loss. Local HTTP success is not backend readback. The schema-URL masking gap remains an explicit acceptance blocker; no all-credentials-masked claim.

Feedback refers to an exact output revision, attributable actor and task-specific rule. Incomplete context or conflicting feedback is quarantined. Related revisions stay in one partition. Automatic gold promotion does not authorize candidate deployment. Compare quality, latency, actual cost and safety against a baseline with locked test data. Failed candidate loading preserves the prior approved version.

## First integrated acceptance slice

1. Admit one synthetic Slack task with duplicate and scope checks.
2. Preserve host pin and verify the actual native session.
3. Open the scoped synthetic browser account; wrong origin/account fails before secret read.
4. Observe passively, take over, reject stale commands and verify handback.
5. Reconcile one deliberately uncertain synthetic submission without blind retry.
6. Validate and accept one exact artifact; reconcile delivery after restart.
7. Read back the same identity in telemetry and a freshness-aware console.
8. Build one replayable example with immutable provenance and leakage-safe partition.
9. Evaluate a candidate and demonstrate exact approval, serving attribution and rollback.

Every gate records not-run/passed/failed/blocked/unknown, exact revisions, timestamp and evidence class. None is reported passed in this scaffold.
