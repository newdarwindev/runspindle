# Offline composition restart rehearsal

From the repository root:

```sh
for case in verified incompatible-pin missing-adapter missing-effect mismatched-effect; do
  python3 tests/test_composition_resume_rehearsal.py "$case" || exit
done
python3 -m unittest discover -s tests -p 'test_composition_resume_rehearsal.py' -v
```

The fixture pins two invented adapters and a known input. The first disposable
process returns a stand-in effect without acknowledgment. A separate ledger
records that effect; a fresh process reconciles the independent fixture receipt
without calling the adapter again. Each case is repeated in two independent
temporary directories and those directories are removed.

A locally passing component can coexist with unknown or mismatched integration
evidence. An absent or incompatible adapter stops before the effect. None of
those paths earns an aggregate pass. The rehearsal uses no repository
submodules, providers, network, credential, or changes to actual component pins.
Real acceptance still needs reviewed compatible code, actual adapters, an
approved isolated runtime, independently observed effects and cleanup.
