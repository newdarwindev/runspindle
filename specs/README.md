# Composition specification

Status: planned contract, implementation and live acceptance not verified.

## Responsibility

Composition and release boundary for seven pinned component repositories.

## Shared identifiers

Correlate task, intent revision, selected host, native session, browser instance, lease epoch, trace/span, artifact digest and Slack destination without placing credentials or raw private content in public receipts.

## Required behavior

Preserve explicit authority and unknown outcomes. Distinguish request admission, execution, validation, acceptance and delivery. Exact state transitions belong in component-specific specs added beside this file.

## Acceptance

1. Unit/contract tests with synthetic data.
2. Isolated integration tests against pinned upstream dependencies.
3. Bounded live acceptance in an authorized target.
4. Failure, restart, uncertain-effect reconciliation and rollback evidence.

Full integrated product gates remain not run. Local bounded component and
fixture tests are recorded separately from integrated acceptance.

See [system contract](system.md).

A provisional [synthetic fixture contract](../docs/FIXTURE_KIT.md) now has a
stdlib validator, versioned bundle and local conformance tests. It is test-only;
standalone Python consumers are adopted in all seven pinned repositories.
Runtime mappings, cross-language parity, upstream qualification and system
acceptance remain unverified.

The separate [Runtime v1 development contract](runtime-v1.md) specifies bounded
admission, operation, reconciliation, cancellation, host and evaluation seams.
Runtime implementation/qualification evidence is recorded separately.

## Engineering direction

[Desired intent](desired-intent.md) connects this component to scoped access,
managed sessions, explicit human exceptions and evaluated maintained workflows.
It adds design and verification obligations without changing runtime schemas,
existing acceptance results or operational permissions.
