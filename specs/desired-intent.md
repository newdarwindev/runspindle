# Desired intent: Composition and maintained workflows

Status: engineering direction and acceptance obligations, not a new implementation
claim, grant of authority, or replacement for existing versioned contracts.

## System intent and evidence boundary

Runspindle is intended to turn an authorized one-off task into a repeatable,
maintained workflow by composing scoped access, managed native/browser sessions,
explicit human takeover, and evaluated workflow candidates. The useful capability
is the composition: cross-application execution can retain identity and evidence
across interruptions, while approved examples can inform later DSPy experiments.
This is a design objective, not evidence of emergent intelligence, autonomous
self-improvement, deployed integration, or measured gains.

A workflow revision must identify its inputs, permitted effects, target bindings,
exception policy, acceptance criteria and resource budget. Repetition does not
create a recurring schedule or expand permission. Human intervention is first an
execution event; only a separately reviewed, consented and sanitized example may
enter a dataset. A successful evaluation is evidence for review, not authority to
promote, serve, spend, publish or act in another account.

## Component responsibility

The composition boundary should make a workflow revision reproducible across
core admission, a pinned host/native session, an account-isolated browser, human
exceptions, delivery and candidate evaluation. Maintain causal references rather
than copying private session contents between components. A connector/API and a
UI adapter are alternative execution surfaces, not interchangeable evidence or
permission sources.

A desired end-to-end lifecycle is: authorize a bounded revision; admit a stable
operation identity; execute on the selected target; pause and fence for human
exceptions; reconcile uncertain effects; validate the exact output; deliver only
to the authorized destination; separately curate eligible feedback; evaluate a
locked candidate against a baseline; and obtain approval before promotion.
Recurring execution additionally needs an explicit trigger, ownership, stop
condition and bounded budget. These lifecycle terms are explanatory, not new
runtime wire enums. The versioned runtime contract remains authoritative.

## Interfaces and acceptance obligations

- Preserve task/revision/operation/policy bindings and host/workspace/lease identity
  across every seam; bind browser account/origin and artifact/candidate digests
  where relevant. A trace correlation ID is not an authorization token.
- Keep execution, validation, acceptance and delivery separate. A produced file,
  local HTTP response or accepted message is not proof of the intended outcome.
- Exercise a synthetic cross-app scenario with an interrupted human takeover,
  lost submission response, duplicate delivery, stale observation and explicit
  cancellation. Independently observe adapter calls and effects; do not prove
  correctness using only the coordinator's own reported status.
- A release must pin compatible component commits and contract mappings. Fixture
  conformance does not establish runtime interoperability. A docs-only commit
  does not qualify unrelated newer implementation commits for composition.
- Compare baseline and candidate on the same held-out workflow families, including
  exception and failure cases; require safety, quality, cost and latency evidence
  before any claim of improvement. Define gates before seeing evaluation results.

## Present scope

The integrated system is not implemented. Existing contract/fixture and bounded
component evidence remains distinct from production durable orchestration, live session
control, qualified cross-app execution and product acceptance. See
[Runtime v1](runtime-v1.md) and [implementation evidence](../docs/IMPLEMENTATION.md).
