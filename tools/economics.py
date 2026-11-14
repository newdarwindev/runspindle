"""Original synthetic accounting model, not measurements or a cost forecast."""

from dataclasses import dataclass, fields
from decimal import ROUND_HALF_EVEN, Context, Decimal, localcontext
from fractions import Fraction

LIMIT = 10**18


def integer(value: int) -> None:
    if type(value) is not int or not 0 <= value <= LIMIT:
        raise ValueError("expected bounded nonnegative integer")


@dataclass(frozen=True)
class Costs:
    """Disjoint total period costs in millionths of one declared currency unit."""

    model: int
    tools: int
    human: int
    verification: int
    maintenance: int
    recovery: int
    fixed_integration: int

    def total(self) -> int:
        values = [getattr(self, field.name) for field in fields(self)]
        for value in values:
            integer(value)
        return sum(values)


@dataclass(frozen=True)
class Scenario:
    currency: str
    attempts: int
    authorized_completions: int
    accepted_authorized_completions: int
    costs: Costs
    assumption: str

    def validate(self) -> None:
        if (
            type(self.currency) is not str
            or len(self.currency) != 3
            or not all("A" <= c <= "Z" for c in self.currency)
        ):
            raise ValueError("declare one three-letter currency code")
        for count in (
            self.attempts,
            self.authorized_completions,
            self.accepted_authorized_completions,
        ):
            integer(count)
        if not (
            self.accepted_authorized_completions
            <= self.authorized_completions
            <= self.attempts
        ):
            raise ValueError("inconsistent completion counts")
        if type(self.costs) is not Costs:
            raise ValueError("invalid costs")
        self.costs.total()
        if type(self.assumption) is not str or not 1 <= len(self.assumption) <= 1000:
            raise ValueError("declare bounded synthetic assumptions")

    def unit_cost(self) -> Fraction | None:
        """Exact currency units per accepted authorized completion; None at zero."""
        self.validate()
        count = self.accepted_authorized_completions
        return Fraction(self.costs.total(), count * 1_000_000) if count else None

    def report(self) -> dict[str, object]:
        unit = self.unit_cost()
        display = None
        if unit is not None:
            # Fixed local precision/rounding makes output independent of callers.
            with localcontext(
                Context(
                    prec=60,
                    rounding=ROUND_HALF_EVEN,
                    Emin=-999999,
                    Emax=999999,
                    capitals=1,
                    clamp=0,
                    flags=[],
                    traps=[],
                )
            ):
                display = str(
                    (Decimal(unit.numerator) / Decimal(unit.denominator)).quantize(
                        Decimal("0.000001")
                    )
                )
        return {
            "evidence_class": "synthetic_accounting",
            "currency": self.currency,
            "cost_unit": "millionths_of_currency_unit",
            "costs": {
                field.name: getattr(self.costs, field.name)
                for field in fields(self.costs)
            },
            "total_cost": self.costs.total(),
            "attempts": self.attempts,
            "authorized_completions": self.authorized_completions,
            "accepted_authorized_completions": self.accepted_authorized_completions,
            "unit_cost_exact": None
            if unit is None
            else [unit.numerator, unit.denominator],
            "unit_cost_display": display,
            "unit_cost_status": "undefined_zero_completions"
            if unit is None
            else "defined",
            "assumption": self.assumption,
            "measurement": "not_run",
        }


def synthetic_sensitivity() -> list[dict[str, object]]:
    """Hold total costs fixed while varying hypothetical acceptance only."""
    costs = Costs(
        2_000_000, 1_000_000, 4_000_000, 1_000_000, 1_000_000, 1_000_000, 10_000_000
    )
    return [
        Scenario(
            "USD",
            10,
            10,
            count,
            costs,
            "Invented 20 USD total for ten attempts; vary acceptance only. "
            "All failed-attempt costs remain included; no prediction or measured savings.",
        ).report()
        for count in (0, 1, 5, 10)
    ]


if __name__ == "__main__":
    import json

    print(json.dumps(synthetic_sensitivity(), indent=2, sort_keys=True))
