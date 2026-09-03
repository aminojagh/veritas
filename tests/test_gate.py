"""What a verdict records, and the two holes in the certified-route rule.

Two claims. The **composition claim**: an allowing verdict names the Certified Metrics
the statement's expressions traced to, the axes it sliced by and the Join Paths its
route was certified by, and a refusing verdict names none of them — which is what a
Lineage of what the statement *used* is read off
([DEBT-034](../.claude/docs/debt-ledger.md#debt-034--lineage-records-what-the-model-was-shown-not-what-the-statement-used)).

The **route claim**:
[DEBT-021](../.claude/docs/debt-ledger.md#debt-021--two-joins-to-one-table-under-different-aliases-are-not-told-apart)
and
[DEBT-022](../.claude/docs/debt-ledger.md#debt-022--the-gate-compares-joins-without-their-kind-so-an-outer-join-passes-as-an-inner-one)
both name the Sub-step that builds Grounding as their Trigger, and both owe the same
thing: a probe that writes the statement, declares it, and prints the numbers it and
the certified statement return. The tests under the second divider are that probe for
each.

Every statement here is written out rather than generated, because both shapes need a
writer that means to write them: no model is asked to cross two conversions or to
widen a join, and the Gate has to refuse them anyway.

Run it with `-s` to read the numbers:

    uv run pytest tests/test_gate.py -s
"""

import pytest

from veritas.validation import (
    ANALYST,
    RejectionReason,
    ValidationGate,
    ValidationGateOutcome,
)

# The one statement in this project that has to join `fct_fx_rate` twice: `Gross
# Revenue` converts on the Trade's own Denomination Currency and `Traded Notional` on
# the Instrument's Quotation Currency, so a question asking for both needs both rates
# and the aliases are the only thing telling them apart.
TWO_RATES = """
FROM fct_trade
JOIN fct_fx_rate AS denom_rate
  ON denom_rate.rate_date = fct_trade.trade_date
 AND denom_rate.from_currency = fct_trade.denomination_currency
 AND denom_rate.to_currency = 'EUR'
JOIN dim_instrument ON dim_instrument.instrument_id = fct_trade.instrument_id
JOIN fct_fx_rate AS quote_rate
  ON quote_rate.rate_date = fct_trade.trade_date
 AND quote_rate.from_currency = dim_instrument.quotation_currency
 AND quote_rate.to_currency = 'EUR'
JOIN dim_account ON dim_account.account_id = fct_trade.account_id
JOIN dim_client ON dim_client.client_id = dim_account.client_id
WHERE dim_client.client_region = 'EU'
"""

# The two certified expressions, with the rate they convert through left open. Written
# here rather than read from `semantic/` on purpose: crossing them means writing an
# expression the corpus does not publish, and a probe that built it out of the corpus
# would be a probe that could not.
GROSS_REVENUE = "sum(fct_trade.commission * {rate}.fx_rate)"
TRADED_NOTIONAL = (
    "sum(CAST(fct_trade.quantity AS DECIMAL(38, 6)) "
    "* fct_trade.execution_price * {rate}.fx_rate)"
)

# `Gross Revenue` alone, over the route it certifies, with the kind of join left open.
GROSS_REVENUE_ALONE = (
    "SELECT sum(fct_trade.commission * fct_fx_rate.fx_rate) AS answer "
    "FROM fct_trade "
    "{kind} fct_fx_rate "
    "  ON fct_fx_rate.rate_date = fct_trade.trade_date "
    " AND fct_fx_rate.from_currency = fct_trade.denomination_currency "
    " AND fct_fx_rate.to_currency = 'EUR' "
    "JOIN dim_account ON dim_account.account_id = fct_trade.account_id "
    "JOIN dim_client ON dim_client.client_id = dim_account.client_id "
    "WHERE dim_client.client_region = 'EU'"
)


def both_metrics(gross_rate: str, notional_rate: str) -> str:
    """One statement computing both metrics, each through the rate it is given."""
    return (
        f"SELECT {GROSS_REVENUE.format(rate=gross_rate)} AS gross_revenue, "
        f"{TRADED_NOTIONAL.format(rate=notional_rate)} AS traded_notional "
        f"{TWO_RATES}"
    )


# `Trade Count` sliced by a certified axis: the one shape whose verdict has something to
# put in all three lists — a metric, the axis it grouped by, and a route that is the
# axis's hop plus the two the Access Profile's predicate is reached through.
TRADE_COUNT_BY_INSTRUMENT_TYPE = (
    "SELECT dim_instrument.instrument_type AS slice, count(fct_trade.trade_id) AS answer "
    "FROM fct_trade "
    "JOIN dim_account ON dim_account.account_id = fct_trade.account_id "
    "JOIN dim_client ON dim_client.client_id = dim_account.client_id "
    "JOIN dim_instrument ON dim_instrument.instrument_id = fct_trade.instrument_id "
    "WHERE dim_client.client_region = 'EU' "
    "GROUP BY dim_instrument.instrument_type"
)


@pytest.fixture(scope="module")
def gate(warehouse):
    """The Gate over the built Warehouse and the corpus on disk."""
    return ValidationGate(warehouse)


# -- the composition claim -------------------------------------------------------


def test_an_allowed_verdict_names_what_the_statement_was_composed_from(gate):
    """The metric the expression traced to, and the Join Paths the route was certified
    by — including the two that scope it.

    `Gross Revenue` and `Net Revenue` are one join and one arithmetic operator apart and
    both are in the corpus; the verdict names the one this statement computes. The two
    access hops are in the route because every statement Veritas runs is scoped, so they
    are part of how these rows were reached and not an aside.
    """
    outcome = gate.judge(GROSS_REVENUE_ALONE.format(kind="JOIN"), ANALYST)
    assert outcome.allowed, outcome.explanation
    assert outcome.metrics == ("Gross Revenue",)
    assert outcome.dimensions == ()
    assert outcome.join_paths == (
        "trade_to_fx_rate_on_denomination_currency",
        "trade_to_account",
        "account_to_client",
    )


def test_a_sliced_statement_names_the_axis_and_not_the_one_that_scopes_it(gate):
    """The axis a statement grouped by is what it sliced by; `by region` is what every
    statement is scoped along, whether or not it asked to be.

    Its Join Paths are in the route all the same. An *axis usage* chart in which every
    answer named `by region` would be a chart of the Access Profile.
    """
    outcome = gate.judge(TRADE_COUNT_BY_INSTRUMENT_TYPE, ANALYST)
    assert outcome.allowed, outcome.explanation
    assert outcome.metrics == ("Trade Count",)
    assert outcome.dimensions == ("by instrument type",)
    assert outcome.join_paths == (
        "trade_to_instrument",
        "trade_to_account",
        "account_to_client",
    )


def test_a_statement_computing_two_metrics_names_both_and_both_their_routes(gate):
    """Each metric's own Join Paths, named once and in the order they extend the route."""
    outcome = gate.judge(both_metrics("denom_rate", "quote_rate"), ANALYST)
    assert outcome.allowed, outcome.explanation
    assert outcome.metrics == ("Gross Revenue", "Traded Notional")
    assert outcome.join_paths == (
        "trade_to_fx_rate_on_denomination_currency",
        "trade_to_account",
        "account_to_client",
        "trade_to_instrument",
        "instrument_to_fx_rate_on_quotation_currency",
    )


def test_a_refused_statement_composed_nothing(gate):
    """The widened join traces to `Gross Revenue` and is refused for its route — and a
    statement that never ran produced nothing, so the verdict names nothing it reached
    for."""
    outcome = gate.judge(GROSS_REVENUE_ALONE.format(kind="LEFT JOIN"), ANALYST)
    assert not outcome.allowed
    assert (outcome.metrics, outcome.dimensions, outcome.join_paths) == ((), (), ())


def test_a_verdict_cannot_refuse_and_name_what_it_composed():
    """The contract, as a construction error: *"metric-usage frequency"* counts what was
    computed, and a refused statement's entries were attempted rather than used."""
    with pytest.raises(ValueError, match="composed nothing"):
        ValidationGateOutcome(
            allowed=False,
            reasons=(RejectionReason.SHADOW_METRIC,),
            metrics=("Gross Revenue",),
        )


# -- the route claim -------------------------------------------------------------


def test_two_metrics_may_convert_through_two_rates_in_one_statement(gate, warehouse):
    """The honest two-metric statement is allowed, or the rule below refuses everything.

    The half that has to pass. Each expression converts through the join its own Metric
    Definition names, and the two joins are to one table under two aliases — which is
    the shape the corpus certifies and the shape DEBT-021 could not tell from the
    crossed one.
    """
    straight = both_metrics("denom_rate", "quote_rate")
    outcome = gate.judge(straight, ANALYST)
    assert outcome.allowed, outcome.explanation
    [(gross, notional)] = warehouse.query(straight)
    print(f"\n  certified   Gross Revenue {gross:>22,.2f}   Traded Notional {notional:>22,.2f}")


def test_a_crossed_conversion_is_refused_and_the_numbers_say_why(gate, warehouse):
    """[DEBT-021](../.claude/docs/debt-ledger.md#debt-021--two-joins-to-one-table-under-different-aliases-are-not-told-apart)
    paid: the same statement with the two rates swapped.

    Every earlier rule is satisfied — both expressions trace, both joins are in the
    union of the two metrics' routes, nothing is missing and the statement is scoped.
    The projections are identical to the certified ones once written on base tables, so
    the tracing rule cannot see it either. What separates them is which alias each
    expression reads through, and both numbers move.
    """
    straight = both_metrics("denom_rate", "quote_rate")
    crossed = both_metrics("quote_rate", "denom_rate")

    outcome = gate.judge(crossed, ANALYST)
    assert not outcome.allowed
    assert outcome.reasons == (RejectionReason.UNCERTIFIED_ROUTE,)
    assert "Gross Revenue through" in outcome.explanation

    [(right_gross, right_notional)] = warehouse.query(straight)
    [(wrong_gross, wrong_notional)] = warehouse.query(crossed)
    assert right_gross != wrong_gross and right_notional != wrong_notional
    print(f"\n  certified   Gross Revenue {right_gross:>22,.2f}   Traded Notional {right_notional:>22,.2f}")
    print(f"  crossed     Gross Revenue {wrong_gross:>22,.2f}   Traded Notional {wrong_notional:>22,.2f}")


@pytest.mark.parametrize("kind", ["JOIN", "INNER JOIN"])
def test_the_two_spellings_of_an_inner_join_are_one_join(gate, kind):
    """`JOIN` and `INNER JOIN` are the same join, and the corpus writes the first."""
    outcome = gate.judge(GROSS_REVENUE_ALONE.format(kind=kind), ANALYST)
    assert outcome.allowed, outcome.explanation


@pytest.mark.parametrize("kind", ["LEFT JOIN", "LEFT OUTER JOIN", "FULL JOIN"])
def test_an_outer_join_over_a_certified_condition_is_refused(gate, kind):
    """[DEBT-022](../.claude/docs/debt-ledger.md#debt-022--the-gate-compares-joins-without-their-kind-so-an-outer-join-passes-as-an-inner-one)
    paid: the condition is the certified one and the join is not.

    A Join Path is a route between two tables — the rows on both sides — so an outer
    join over its condition reaches rows the route does not certify. The rejection
    spells the kind, because *"dim_client"* would not tell a reader what to fix.
    """
    outcome = gate.judge(GROSS_REVENUE_ALONE.format(kind=kind), ANALYST)
    assert not outcome.allowed
    assert outcome.reasons == (RejectionReason.UNCERTIFIED_ROUTE,)
    assert "OUTER JOIN fct_fx_rate" in outcome.explanation


def test_the_outer_join_returns_the_same_number_on_this_warehouse(gate, warehouse):
    """The measurement DEBT-022 owes, and it moves nothing — which the entry predicted.

    `Gross Revenue` multiplies by `fct_fx_rate.fx_rate`, so a Trade an outer join kept
    without a rate contributes `NULL` and `sum` skips it. On this Warehouse not even
    that happens: every Trade has a rate on its own Trade Date, so the two statements
    read the same rows. The hole is real and its cost here is zero, which is a property
    of these nine expressions and of this data rather than of the rule — and the reason
    the entry was small.
    """
    inner = GROSS_REVENUE_ALONE.format(kind="JOIN")
    outer = GROSS_REVENUE_ALONE.format(kind="LEFT JOIN")
    counted = "count(*)"
    metric = "sum(fct_trade.commission * fct_fx_rate.fx_rate)"

    [(certified,)] = warehouse.query(inner)
    [(widened,)] = warehouse.query(outer)
    [(certified_rows,)] = warehouse.query(inner.replace(metric, counted))
    [(widened_rows,)] = warehouse.query(outer.replace(metric, counted))
    assert (certified, certified_rows) == (widened, widened_rows)
    print(f"\n  JOIN        Gross Revenue {certified:>22,.2f}   over {certified_rows:>6} rows")
    print(f"  LEFT JOIN   Gross Revenue {widened:>22,.2f}   over {widened_rows:>6} rows")
