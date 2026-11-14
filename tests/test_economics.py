"""Synthetic dimensional checks; no provider, prices, or measured workloads."""

import unittest
from dataclasses import replace
from decimal import ROUND_DOWN, DefaultContext, Inexact, localcontext
from fractions import Fraction
from typing import Any, cast

from tools.economics import Costs, Scenario, synthetic_sensitivity


class EconomicsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.costs = Costs(
            1_000_000, 2_000_000, 3_000_000, 4_000_000, 5_000_000, 6_000_000, 7_000_000
        )
        self.scenario = Scenario(
            "USD", 10, 8, 4, self.costs, "Invented complete period totals"
        )

    def test_all_cost_categories_count_once(self) -> None:
        self.assertEqual(self.costs.total(), 28_000_000)
        self.assertEqual(self.scenario.unit_cost(), Fraction(7))

    def test_denominator_is_accepted_and_authorized_not_attempts(self) -> None:
        self.assertEqual(replace(self.scenario, attempts=100).unit_cost(), Fraction(7))
        self.assertEqual(
            replace(self.scenario, authorized_completions=9).unit_cost(), Fraction(7)
        )
        self.assertEqual(
            replace(self.scenario, accepted_authorized_completions=2).unit_cost(),
            Fraction(14),
        )

    def test_zero_completions_preserve_cost_not_free_work(self) -> None:
        report = replace(self.scenario, accepted_authorized_completions=0).report()
        self.assertEqual(report["total_cost"], 28_000_000)
        self.assertIsNone(report["unit_cost_exact"])
        self.assertIsNone(report["unit_cost_display"])
        self.assertEqual(report["unit_cost_status"], "undefined_zero_completions")

    def test_zero_attempts_can_have_fixed_costs(self) -> None:
        scenario = replace(
            self.scenario,
            attempts=0,
            authorized_completions=0,
            accepted_authorized_completions=0,
        )
        self.assertIsNone(scenario.unit_cost())
        self.assertEqual(scenario.report()["total_cost"], 28_000_000)

    def test_exact_ratio_and_declared_rounding(self) -> None:
        scenario = replace(self.scenario, accepted_authorized_completions=3)
        self.assertEqual(scenario.unit_cost(), Fraction(28, 3))
        self.assertEqual(scenario.report()["unit_cost_display"], "9.333333")
        with localcontext() as context:
            context.prec = 2
            context.traps[Inexact] = True
            self.assertEqual(scenario.report()["unit_cost_display"], "9.333333")

    def test_global_decimal_defaults_cannot_change_report(self) -> None:
        original = DefaultContext.copy()
        try:
            DefaultContext.prec = 2
            DefaultContext.rounding = ROUND_DOWN
            DefaultContext.Emin = -2
            DefaultContext.Emax = 2
            DefaultContext.clamp = 1
            DefaultContext.capitals = 0
            for signal in DefaultContext.traps:
                DefaultContext.traps[signal] = True
                DefaultContext.flags[signal] = True
            scenario = replace(self.scenario, accepted_authorized_completions=3)
            self.assertEqual(scenario.report()["unit_cost_display"], "9.333333")
            largest = Scenario("USD", 1, 1, 1, Costs(*([10**18] * 7)), "Boundary")
            self.assertEqual(
                largest.report()["unit_cost_display"], "7000000000000.000000"
            )
            self.assertTrue(all(DefaultContext.traps.values()))
        finally:
            for name in ("prec", "rounding", "Emin", "Emax", "capitals", "clamp"):
                setattr(DefaultContext, name, getattr(original, name))
            DefaultContext.traps = original.traps.copy()
            DefaultContext.flags = original.flags.copy()

    def test_half_even_and_zero_total(self) -> None:
        costs = Costs(1, 0, 0, 0, 0, 0, 0)
        scenario = replace(
            self.scenario, costs=costs, accepted_authorized_completions=2
        )
        self.assertEqual(scenario.report()["unit_cost_display"], "0.000000")
        self.assertEqual(scenario.unit_cost(), Fraction(1, 2_000_000))
        self.assertEqual(
            replace(scenario, costs=replace(costs, model=3)).report()[
                "unit_cost_display"
            ],
            "0.000002",
        )
        self.assertEqual(
            replace(scenario, costs=replace(costs, model=0)).unit_cost(), 0
        )
        self.assertIsNone(
            replace(
                scenario,
                costs=replace(costs, model=0),
                accepted_authorized_completions=0,
            ).unit_cost()
        )

    def test_invalid_costs_rejected(self) -> None:
        for value in (True, -1, 0.1, "1", 10**18 + 1):
            with self.subTest(value=value), self.assertRaises(ValueError):
                replace(
                    self.scenario, costs=replace(self.costs, recovery=cast(Any, value))
                ).report()

    def test_invalid_counts_rejected(self) -> None:
        for value in (True, -1, 0.5, 10**18 + 1):
            with self.subTest(value=value), self.assertRaises(ValueError):
                replace(self.scenario, attempts=cast(Any, value)).report()
        for kwargs in ({"authorized_completions": 3}, {"attempts": 7}):
            with self.assertRaises(ValueError):
                replace(self.scenario, **cast(dict[str, Any], kwargs)).report()

    def test_currency_and_assumptions_required(self) -> None:
        cases: tuple[dict[str, Any], ...] = (
            {"currency": "usd"},
            {"currency": "USD/EUR"},
            {"currency": "ＵＳＤ"},
            {"assumption": ""},
            {"costs": {}},
        )
        for kwargs in cases:
            with self.assertRaises(ValueError):
                replace(self.scenario, **kwargs).report()

    def test_sensitivity_preserves_numerator_and_labels(self) -> None:
        rows = synthetic_sensitivity()
        self.assertEqual(
            [r["unit_cost_exact"] for r in rows], [None, [20, 1], [4, 1], [2, 1]]
        )
        for row in rows:
            self.assertEqual(row["total_cost"], 20_000_000)
            self.assertEqual(row["measurement"], "not_run")
            self.assertEqual(row["evidence_class"], "synthetic_accounting")

    def test_large_values_remain_exact(self) -> None:
        costs = Costs(*([10**18] * 7))
        scenario = Scenario("USD", 10**18, 10**18, 10**18, costs, "Boundary test")
        self.assertEqual(scenario.unit_cost(), Fraction(7, 1_000_000))
        self.assertEqual(scenario.report()["unit_cost_display"], "0.000007")


if __name__ == "__main__":
    unittest.main()
