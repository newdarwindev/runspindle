# Runtime envelopes v1

This separate JSON wire contract is `runspindle.envelope.v1`. It does not alter
Runtime v1, integration v1, fixture JSON, Rust library types or historical Temporal
payloads. No implicit negotiation or fallback is permitted. The original contract
tranche had user-waived independent review; later producer evidence is recorded
separately.

Every envelope contains exactly `version`, `message_type`, `message_id`, `binding`
and `payload`. Message identity is an opaque stable producer ID, not authority.
Binding contains exactly task_id, revision, operation_id, policy_revision, host_id,
workspace_id and lease_epoch. All identifier fields use runtime v1's ASCII pattern
`[A-Za-z0-9][A-Za-z0-9._:-]{0,127}`. Digests are 64 lowercase hex characters.
Counters are JSON unsigned integer tokens, at most 2^64-1; revision, lease_epoch,
artifact_revision and observation sequence are positive. Booleans, floats and
negative numbers are not integers. Maximum input size is 1 MiB. Reject duplicate
keys at every depth, absent/extra fields, unknown versions/types and invalid
values before invoking any adapter. Required nullable fields must be present.

The four mappings are intentionally explicit:

| message_type | Exact payload fields | Component mapping |
| --- | --- | --- |
| admission_request | delivery_namespace, delivery_id, predecessor_revision, normalized_digest, grant_ref | runtime::Admission: version becomes runspindle.runtime.v1; binding is copied field for field; each payload field maps to its namesake. revision 1 requires null predecessor; subsequent revisions require revision-1. |
| host_observation | native_session_id, sequence, observed_at_ms, state | host::lifecycle::Observation: binding maps field for field; session, sequence and timestamp copy unchanged; running maps terminal=None; completed/failed/cancelled map the corresponding Terminal variant. |
| delivery_request | artifact_id, artifact_revision, sha256, validator_revision, account_id, destination_id, delivery_operation_id | outbox::DeliveryRequest: version becomes runspindle.integration.v1; accepted.validation.artifact contains binding and artifact fields; validation.policy_revision copies binding.policy_revision; validation.passed=true; other fields copy unchanged. Delivery operation must differ from artifact operation. |
| delivery_receipt | request, receipt_id | request is exactly the delivery_request payload, maps as above with the envelope binding; receipt_id copies unchanged into outbox::DeliveryReceipt. |

No other component values are representable. Inverse mappings must reject invalid
component values, including failed validations or mismatched validation policy.
Repeated bindings are excluded from payloads, so attempts to supply a second
binding are unknown-field errors. Consumers must additionally compare the entire
binding against their trusted expected operation before invoking an adapter.
Observation consumers compare the exact expected native session and require
sequence greater than their retained sequence. Delivery consumers compare exact
account and destination. These comparisons are not signature verification.

`conformance/envelope-v1/vectors.json` contains synthetic positive vectors and
expected existing component JSON representations. The independent Python codec
and Rust codec share the contract/vectors, never implementation serializers.
Conformance applies only to these four exercised mappings, not a native provider,
Tether transport, browser, console or full system.

The Python producer entrypoint is `produce(value, message_type, message_id) -> bytes`
in `conformance/envelope-v1/codec.py`. `value` is the exact component JSON object
shown in the vectors; message type and stable message identity are explicit caller
inputs. It returns canonical UTF-8 envelope bytes without modifying the input.
Every nested component object has an exact field set. Delivery validation requires
`passed` to be the boolean `true` (not integer `1`) and the validation policy to
equal the artifact binding policy. All other component-only versions and terminal
values must be representable by the table above. The final wire validator also
checks identifiers, counters, predecessor relationships and distinct operations.
The producer accepts decoded component objects, not component JSON text: lexical
negative integer tokens remain a wire-decoder check. Mapping `passed=true` is not
proof of actual artifact validation, acceptance, signature or delivery authority.
See [bounded producer evidence](../docs/ENVELOPE_PRODUCER.md).

Canonical encoding for authenticated admission is UTF-8 JSON with object keys
sorted lexicographically, no insignificant whitespace, no escapes for ASCII
except JSON-required escaping, and decimal integer tokens. Every string in this
contract is ASCII. Authenticated entrypoints require input bytes to equal this
encoding; SHA-256 binds those exact versioned bytes. Reformatting requires a new
assertion. The message ID and grant reference are included in this digest.
