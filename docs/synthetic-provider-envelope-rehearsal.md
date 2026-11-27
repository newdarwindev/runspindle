# Offline provider-envelope rehearsal

From the repository root:

```sh
for case in exact wrong-model expired missing-cap over-cost_cents over-calls over-tokens over-runtime_ticks; do
  python3 tests/test_synthetic_provider_envelope.py "$case" || exit
done
python3 -m unittest discover -s tests -p 'test_synthetic_provider_envelope.py' -v
```

All provider, project, model, payload and target IDs are invented. They must
match an unexpired envelope for a disposable target with explicit independent
cost, call, token and runtime limits. An incorrect identity, missing/invalid
cap or excess in any limit cannot invoke the local stub. The exact fixture
invokes it once. Stub counts do not represent external calls or actual spend.

No service, credential, model, network or external client is used. This
receipt does not authorize a real run. Live testing still needs separately
approved exact inputs and limits, an independently verified disposable target
and the other execution prerequisites for that lane.
