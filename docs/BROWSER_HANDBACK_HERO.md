# H06 Browser takeover and handback recovery

Composition #13 and #45. This lane exercises the pinned Browser control lease
and guarded input journal with real SQLite and fresh Python processes. The
actor grants, release attestation, viewer fence, viewer readback and input
site are synthetic. Console, Core, KasmVNC, PinchTab and live desktop input
remain unqualified.

Use a prepared checkout of the Browser gitlink and Python 3.13. Run:

```sh
python3 -B tools/browser_handback_hero.py
python3 -B -O tools/browser_handback_hero.py
python3 -B -m unittest discover -s tests -p test_browser_handback_hero.py
```

The harness checks all seven composition lock entries against the index,
requires exact Browser checkout identity and stages only the six reviewed
Python files from Git objects. The versioned manifest records their individual
SHA-256 digests. Each worker runs with isolated Python, bytecode disabled and
an audit hook that rejects socket and process operations. The parent owns
bounded worker lifetimes and the temporary source and store directory.

| Stage | Independent observation |
| --- | --- |
| Agent initialization and takeover | One fence for each transition. An observation-only ticket, the old agent epoch and a wrong holder all produce zero input effects. |
| Human input and forged release | The helper ledger retains exactly one human input. The forged handback adds zero fence calls. |
| Interrupted handback | The worker exits inside the first handback fence call. A separate SQLite reader sees the next epoch retained as pending. Both holders are denied after restart. Duplicate delivery produces zero new fences. |
| Uncertain or stale recovery | Incomplete closure, changed transfer identity, stale observation and missing release leave the same pending row. |
| Confirmed recovery | The exact complete synthetic readback restores the agent at epoch 3 once. The old human lease is denied and the only additional input reaches the resumed agent. |

Each invocation runs two independent copies of the scenario and compares
normalized outcomes. A third run removes the complete-closure check from a
disposable copy of the Browser source. The campaign rejects that run when
incomplete closure activates the lease. The original checkout remains clean.
The JSON receipt records the exact composition revision, seven component pins,
fixture digest and per-lane result. Its system acceptance field remains blocked.

Local verification used Python 3.13.18 on macOS arm64, based on composition
`fc68cb72528922217d50663c6761a148e1a3cb35`. The Browser pin was
`595dd6e75b85ce2069e8aa8a8adb5a9271ab67e3`. The three focused tests passed in
normal and optimized Python. Static quality, scaffold and library pin alignment
passed. Physical overlap prevention, authenticated issuer and real viewer
closure still require separate evidence.

```text
c42564215bfa5a8eab659c01196a3727e30787355dadd593f3f9a3b6f69ea1b0  composition.lock.json
fe5374f4bd24b616e5b6464a78abbfe8ad34c17cce3e2f4527f9f38f227025ff  scenarios/browser-handback-v1.json
69909bbba417a334d8638b47b0ab3771f1887c794785020d71d9463b1abb3247  tools/browser_handback_hero.py
67300ecea7bc16ea8eea6d43ce849728626dfe0e798c5caf025df51ca5fc9223  tests/test_browser_handback_hero.py
```
