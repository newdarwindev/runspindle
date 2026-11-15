# Bounded Python envelope producer

Issue: [composition #43](https://github.com/newdarwindev/runspindle/issues/43).
Base: `4509fe4ae127b1097c1241b3bacc532cc06b7b8a` (remote main checked before coding).
This completes the missing Python inverse mappings in the existing
`runspindle.envelope.v1` contract; it does not qualify Core's separate Rust work.
No composition pins, wire versions, CI runners or authority gates change.

## Entrypoint and boundary

`conformance/envelope-v1/codec.py::produce(value, message_type, message_id)` takes
an exact component JSON object and explicit metadata, returning canonical UTF-8
wire bytes. It supports admission, host observations, delivery requests and
receipts. Each delivery's validation must carry exact boolean `true` and the same
policy as its artifact binding. Unknown fields, nonrepresentable values, missing
nullable fields, bad versions/counters/identifiers and conflicting delivery
operations fail before bytes are returned. Inputs are not modified.

This is stateless, in-process synthetic conformance, not authentication, validation
of artifact bytes, acceptance or a transport. The existing consumer still checks
trusted binding, session/sequence and account/destination before adapter calls.
No native provider, browser, Tether, console, persistence, durability or full-system
acceptance is exercised or inferred. A decoded Python integer cannot retain a
negative-zero token; wire decoding still rejects negative tokens before effects.

## Independent observations

- Existing committed vectors independently pin all fields and canonical bytes;
  producer results are compared directly using stdlib JSON, then round-tripped
  through the consumer. Four terminal variants and u64 boundary cases are covered.
- Every nested component field is deleted in turn, every mapping receives an extra
  field, and non-object values are rejected. Scalar negatives cover bool/int aliases,
  overflow, floats, invalid identifiers/digests, failed validation, policy mismatch,
  invalid terminals, predecessor mismatch and conflicting operations.
- Rejection is required at the producer itself, not merely at the consumer. A
  separate adapter-call list must remain empty. Consumer context-fence negatives
  cover all seven binding fields, stale sessions/sequences and wrong destinations.
- Two deliberately altered in-memory codec modules are detected: substituting
  policy for validator identity fails the independent fixture oracle; removing
  the failed-validation guard triggers a forbidden adapter effect. The real source
  is not changed during these tests. Both also run under optimized Python.

## Reproduction and results

On a prepared isolated local runner, with no network needed by the focused suite:

```sh
python3 -m unittest discover -s tests -p '*envelope*' -v
```

Observed with CPython 3.12.14: **18 tests passed**, including the subprocess
optimized-interpreter suites. `python3 tools/check_scaffold.py` passed. Targeted
Ruff 0.14.5 lint/format checks and mypy 1.18.2 `--strict` passed for the codec and
new producer tests. No new dependency was installed; implementation/tests use
only the standard library. Full aggregate validation is recorded separately in
the exact-head review/publication receipt, not inferred from focused tests.

Source/fixture/test SHA-256 at the reviewed candidate:

- `conformance/envelope-v1/codec.py`:
  `0118d3d85a4bc8149b9eebe9aafbfdcc405a09d1410596040ca1e9885356f320`
- `conformance/envelope-v1/vectors.json` (unchanged):
  `fcebde87ffb2273e430de1115e809b0c8bee4efb02497f6a5dbfde3ebed02941`
- `tests/test_envelope_producer.py`:
  `1d61e9de76d6a5affac1d61a248b2d564c734da94eefc6d9518af3f321c28602`

The exact commit/tree is supplied with the review receipt.

Independent final-tree review and remote CI remain pending at this evidence
record's creation. Issue #43 and its parent remain open for their broader runtime
and authority criteria; this local source result does not close them.


## Typed consumer context follow-up

The consumer now applies the existing seven-field binding validator to its
expected binding before decoding the message or invoking an adapter. This closes
Python equality aliases where boolean `true` or floating-point `1.0` previously
matched the wire integer `1`. It does not add a new authority policy or change
wire mappings. Expected revision and lease epoch must be positive u64 integers;
all five expected identifiers retain the existing ASCII identifier rules.

Consumer regressions exercise every mapping with malformed, missing and extra
expected fields, boolean/float counter aliases and invalid identifiers. Each
rejection independently observes zero adapter calls and unchanged caller context.
Valid contexts preserve their component mappings. A deliberate in-memory mutation
removes only the expected-binding guard and must trigger the forbidden-effect
oracle. These cases also run through the existing optimized-interpreter suite.

Run the focused command above to reproduce. This is synthetic stateless consumer
conformance, not runtime authority, persistence, full aggregate or live acceptance.
The retained-sequence comparison is unchanged; this fix does not introduce a new
sequence-context schema. Historical producer hashes/results above identify their
original candidate, not this follow-up's source tree.
