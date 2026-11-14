# Scenario oracle checks under optimized Python

The core/Temporal scenario's 29 observation assertions are now explicit
`_require_observation` calls. Invalid observations still raise AssertionError,
including when Python runs with `-O`. Valid observation predicates and returned
summary values are unchanged. This prevents optimization from silently accepting
extra launches, incorrect bindings, premature terminal states or replay effects.

The existing synthetic positive and negative oracle tests are exercised in fresh
normal and optimized subprocesses by `tests/test_scenario_optimization.py`.
This is component evidence, not a new real Temporal run. Existing source-bound
runtime evidence must not be treated as qualification of this changed driver.

Pinned formatter/type checks required formatting and annotations in the touched
legacy module. Dynamic JSON and imported lane interfaces remain explicitly
typed boundaries. No baseline, workflow, timeout, system gate, image or component
pin changes are included. A normalized AST comparison found the 29 explicit
checks and helper as the only executable change after removing annotations and
identity casts. The helper uses a fixed failure message rather than raw values.
