# Executable synthetic accounting

This is an original accounting implementation supporting issue #7, not a lift of
historical equations, measured prices, performance, savings or financial advice.
It supplements the existing paper/economics narrative without changing its claims.
The historical source-section disposition and full SRC-005 migration remain open.

## Units and assumptions

For one explicitly chosen workload and accounting period, supply seven disjoint
cost totals: model, tools, human effort, verification, maintenance, recovery and
fixed integration. Each is a nonnegative integer in **millionths of one currency
unit**. All seven fields are required. Zero means an explicit zero assumption,
not missing/unknown cost. If any amount is unknown, do not construct a scenario.
Currency codes are declared labels, not validated exchange-rate data; never mix
currencies. No exchange conversion or price lookup occurs.

Include every failed, rejected and unauthorized attempt's incurred costs in the
appropriate category. Categorize each cost exactly once, including repair/cleanup
and allocated fixed integration cost. Human time must be converted externally using
an explicitly documented rate; time saved is not automatically cash saved. The
model cannot authenticate cost inputs, authorization or acceptance observations.
Record their provenance before using it beyond invented examples.

Let C be the sum of the seven period totals, in millionths of currency, and A be
the number of **accepted authorized completions**, not attempts or mere execution
successes. Unit cost is C / (1,000,000 × A), in currency per completion. Counts
must satisfy 0 ≤ A ≤ authorized completions ≤ attempts. Retries count as attempts;
count each accepted outcome once. When A = 0, unit cost is undefined, even if C = 0;
report the total incurred cost and zero completions, never infinity or a free task.

The implementation uses exact integer summation and rational division. The report
retains the exact numerator/denominator and separately rounds display to six
currency decimals using half-even rounding in an isolated Decimal context. Do not
use rounded display strings as input to further accounting. Inputs are bounded at
10^18 per count/category; this is a validation bound, not a spending allowance.

## Bounded invocation and sensitivity

From the repository root, run `python3 tools/economics.py`. It prints four synthetic
JSON scenarios, does not read credentials or write files, and makes no network or
provider calls. Its invented totals are 20 USD over ten attempts, including 10 USD
fixed integration cost. Holding **all costs fixed**, accepted counts 0, 1, 5 and 10
produce undefined, 20, 4 and 2 USD per accepted authorized completion. This is an
arithmetic sensitivity exercise, not an acceptance-rate forecast or a break-even
claim. A real volume change would usually change variable and maintenance costs.
Comparisons require the same workload, period, currency, acceptance criteria and
explicit fixed-cost allocation; this tool does not certify comparability.

Run `python3 -m unittest discover -s tests -p test_economics.py -v` and the same
command with `python3 -O`. Tests cover dimensional conversion, every cost category,
zero outcomes, acceptance-vs-attempt denominator, invalid types/counts, exact
fractions, rounding and synthetic sensitivity. Full composition/native/live
acceptance is independent of these arithmetic checks.
