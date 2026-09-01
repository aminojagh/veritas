"""The Gold Question Set: what it holds, what it derives, and what it must separate.

Four claims. The **statement claim**: every gold SQL is one the Validation Gate allows
and executes to the gold result written beside it. The **coverage claim**: every
Certified Metric, every Ambiguous Term and every ending a question can have is in the
set, and every gold statement keys on its own metric's date column. The **derivation
claim**: a Relevant Set is read off the statement rather than written beside it, and the
Join Paths it names are exactly the joins the statement carries. The **separation
claim**: a Gold Question turning on a Glossary Section C pair separates the two sides of
that pair by more than `RESULT_TOLERANCE`, which is what
[DEBT-004](../.claude/docs/debt-ledger.md#debt-004--the-fx-date-distinction-is-too-small-to-be-a-reliable-evaluation-signal)
and [DEBT-011](../.claude/docs/debt-ledger.md#debt-011--execution-price-against-market-price-cancels-at-book-level)
require of it.

Nothing here calls a model. The rewrite step's matcher is read directly, because which
Ambiguous Terms a question says is a property of the words and the corpus.
"""

from decimal import Decimal

import pytest

from veritas.evaluation import (
    RESULT_TOLERANCE,
    Expectation,
    GoldQuestion,
    GoldQuestionError,
    PhrasingClass,
    axes_touched,
    load_gold_questions,
    metrics_touched,
    read_gold_question,
    reading_of,
    relevant_entries,
    same_result,
)
from veritas.orchestrator import ambiguous_terms_in
from veritas.semantic import (
    AmbiguousTerm,
    DimensionDefinition,
    JoinPath,
    MetricDefinition,
)
from veritas.validation import (
    ANALYST,
    RejectionReason,
    ValidationGate,
    date_columns_filtered,
    route_of_resolved,
)

# The one Gold Question whose statement the Validation Gate refuses. `Account Value` is
# *"Cash Balance plus all Positions marked to market"* and the corpus says so with
# `derives_from`, which the Gate does not read — so the only correct statement for it is
# an addition the Gate calls a Shadow Metric. Named here rather than marked in the file,
# so that paying
# [DEBT-035](../.claude/docs/debt-ledger.md#debt-035--a-composed-certified-metric-has-no-statement-the-gate-allows)
# breaks this test and the exemption goes with it.
REFUSED_TODAY = {"Account Value as of 10 August 2026": (RejectionReason.SHADOW_METRIC,)}

# The Gold Question each Section C pair below is measured on, by name.
KEYED_ON_TRADE_DATE = "Gross Revenue in the second quarter of 2026"
VALUED_AT_EXECUTION_PRICE = "Traded Notional on 18 March 2025"

# The join that reaches the day's close for an Instrument a Trade names — the Market
# Price half of the Execution Price / Market Price pair. It is not in `semantic/joins/`
# and deliberately so: no Metric Definition is certified across it, and the Gate refuses
# a statement that carries it. It exists here to be executed as the wrong answer.
AT_THE_CLOSE = (
    "JOIN fct_instrument_price "
    "ON fct_instrument_price.price_date = fct_trade.trade_date "
    "AND fct_instrument_price.instrument_id = fct_trade.instrument_id\n"
)


@pytest.fixture(scope="module")
def gold():
    """The Gold Question Set, loaded once."""
    return load_gold_questions()


@pytest.fixture(scope="module")
def gate(warehouse, semantic):
    """One Gate over the built Warehouse and the corpus the gold SQL is written against."""
    return ValidationGate(warehouse, semantic=semantic)


def answerable(gold):
    """The Gold Questions that should come back as a number."""
    return [question for question in gold if question.answerable]


def substituted(sql: str, before: str, after: str) -> str:
    """`sql` with one substring replaced, refusing to return it unchanged.

    A wrong-half statement built by replacing text that is no longer there would be the
    gold statement compared with itself, which is a separation test that always passes.
    """
    assert before in sql, f"{before!r} is not in this statement any more"
    return sql.replace(before, after)


# -- the statement claim ---------------------------------------------------------


def test_every_gold_sql_is_allowed_by_the_gate(gold, gate):
    """Ground truth is what Veritas is allowed to run, except where the Ledger says not.

    Both directions in one assertion: a gold statement the Gate starts refusing appears,
    and the one it refuses today disappears when that stops being true.
    """
    refused = {
        question.name: gate.judge(question.sql, ANALYST).reasons
        for question in answerable(gold)
        if not gate.judge(question.sql, ANALYST).allowed
    }
    assert refused == REFUSED_TODAY


def test_every_gold_sql_executes_to_its_gold_result(gold, gate, warehouse):
    """The gold result is what the gold statement returns, at today's tolerance."""
    for question in answerable(gold):
        rows = warehouse.query(question.sql)
        assert same_result(question.result, rows), (
            f"{question.name}: {question.result} against {rows}"
        )
        print(f"\n  {question.name} -> {rows}")


# -- the coverage claim ----------------------------------------------------------


def test_every_certified_metric_reaches_the_gold_question_set(gold, gate, semantic):
    """[DEBT-033](../.claude/docs/debt-ledger.md#debt-033--the-generators-live-evidence-is-five-self-written-questions-and-four-certified-metrics-never-reach-it)'s
    coverage, read off the statements rather than off a list."""
    computed = {
        metric.name
        for question in answerable(gold)
        for metric in metrics_touched(reading_of(question.sql, gate), gate)
    }
    assert computed == set(semantic.metrics)


def test_every_gold_statement_keys_on_its_own_metrics_date_column(gold, gate):
    """A period is filtered on the metric's own `date_column` and on no other date.

    The Gate's date rule refuses any other, so a set whose statements key on none of
    them would leave that rule with nothing to have judged — which is what DEBT-033
    records about the five questions this set replaces.
    """
    for question in answerable(gold):
        reading = reading_of(question.sql, gate)
        certified = {
            tuple(metric.date_column.split(".", 1))
            for metric in metrics_touched(reading, gate)
        }
        filtered = date_columns_filtered(reading.resolved, reading.schema)
        assert filtered == certified, question.name


def test_every_ambiguous_term_is_asked_about_by_a_gold_question(gold, semantic):
    """Each Section D row is said by a question whose correct ending is a Clarifying
    Question."""
    said = {
        term.name
        for question in gold
        if question.expects is Expectation.CLARIFYING_QUESTION
        for term in ambiguous_terms_in(question.question, semantic)
    }
    assert said == set(semantic.ambiguous_terms)


def test_the_set_holds_every_ending_a_question_can_have(gold):
    """A set of nothing but answerable questions measures nothing about refusing."""
    endings = {question.expects for question in gold}
    assert endings == set(Expectation)


def test_the_set_holds_a_breakdown_for_more_than_one_axis(gold, gate):
    """A slice is where the axis routes and the `GROUP BY` rules are exercised at all."""
    sliced = {
        axis.name
        for question in answerable(gold)
        for axis in axes_touched(reading_of(question.sql, gate).resolved, gate)
    }
    assert {"by region", "by instrument type"} <= sliced


def test_debt_029s_four_phrasing_classes_are_in_the_set_and_detected(gold, semantic):
    """[DEBT-029](../.claude/docs/debt-ledger.md#debt-029--ambiguous-term-detection-is-literal-so-every-other-phrasing-of-a-registered-word-passes-silently),
    paid and scored over the Gold Question Set rather than over four strings.

    Every question whose correct ending is a Clarifying Question says a term Veritas
    finds — the four spelled some other way included, which is what `phrasing_class`
    is carried on the question to say.
    """
    asks_back = [
        question for question in gold
        if question.expects is Expectation.CLARIFYING_QUESTION
    ]
    missed = [
        f"{question.name} ({question.phrasing_class or 'as registered'})"
        for question in asks_back
        if not ambiguous_terms_in(question.question, semantic)
    ]
    assert not missed, f"said an Ambiguous Term and were detected as saying none: {missed}"
    assert {question.phrasing_class for question in asks_back} == {
        None, *PhrasingClass
    }


def test_no_gold_question_that_names_its_meaning_is_asked_back_about(gold, semantic):
    """The other direction of DEBT-029's repayment, and the one a wider alias breaks.

    A spelling registered too loosely turns a question Veritas should answer into one
    it stops to ask about. So every Gold Question whose correct ending is *not* a
    Clarifying Question is checked for the terms it says, and each of them must have
    one of its own meanings named in the question — which is what the rewrite step
    resolves it by, and is why the question is answerable at all.
    """
    for question in gold:
        if question.expects is Expectation.CLARIFYING_QUESTION:
            continue
        for term in ambiguous_terms_in(question.question, semantic):
            named = [
                meaning for meaning in term.disambiguates
                if meaning.casefold() in question.question.casefold()
            ]
            assert named, (
                f"{question.name}: expects {question.expects} and says the Ambiguous "
                f"Term {term.name!r} without naming any of {list(term.disambiguates)}"
            )


# -- the derivation claim --------------------------------------------------------


def test_the_derived_join_paths_are_the_joins_the_statement_carries(gold, gate):
    """The Relevant Set is read off the statement, and this is what says so.

    The Join Paths are derived from the entries the statement traces to rather than from
    its parse tree, so this compares the two: the Route assembled from the derived names
    against the Route the statement itself carries.
    """
    for question in answerable(gold):
        reading = reading_of(question.sql, gate)
        metrics = metrics_touched(reading, gate)
        axes = axes_touched(reading.resolved, gate)
        declared = gate.assembled_route(metrics, axes, reading.schema, access=False)
        assert route_of_resolved(reading.resolved).joins == declared.joins, question.name


def test_a_relevant_set_names_metrics_axes_and_the_join_paths_they_reach(gold, gate):
    """Three entry types and never a fourth: an Ambiguous Term publishes no SQL, so no
    statement can touch one."""
    for question in answerable(gold):
        entries = relevant_entries(question, gate)
        assert entries, question.name
        assert not any(isinstance(entry, AmbiguousTerm) for entry in entries)
        assert {type(entry) for entry in entries} <= {
            MetricDefinition, DimensionDefinition, JoinPath
        }
        assert len(entries) == len({entry.name for entry in entries}), question.name
        print(f"\n  {question.name}\n    {[entry.name for entry in entries]}")


def test_a_question_with_no_gold_sql_has_an_empty_relevant_set(gold, gate):
    """There is no statement to read, which is the honest answer rather than a guess."""
    for question in gold:
        if not question.answerable:
            assert relevant_entries(question, gate) == []


# -- the separation claim --------------------------------------------------------


def test_the_trade_date_period_is_not_the_settlement_date_period(gold, warehouse):
    """[DEBT-004](../.claude/docs/debt-ledger.md#debt-004--the-fx-date-distinction-is-too-small-to-be-a-reliable-evaluation-signal):
    the period question separates the Section C pair by more than the tolerance.

    Keying the same quarter on Settlement Date moves the number twice — it shifts which
    Trades fall inside the period, and it takes each Trade's FX Rate on a different day.
    The rate half alone is printed beside it, because that is the half the entry was
    opened about.
    """
    [question] = [g for g in gold if g.name == KEYED_ON_TRADE_DATE]
    settled = substituted(question.sql, "fct_trade.trade_date", "fct_trade.settlement_date")
    rate_only = substituted(
        question.sql,
        "fct_fx_rate.rate_date = fct_trade.trade_date",
        "fct_fx_rate.rate_date = fct_trade.settlement_date",
    )
    [(gold_figure,)] = warehouse.query(question.sql)
    [(both_moves,)] = warehouse.query(settled)
    [(rate_move,)] = warehouse.query(rate_only)
    assert not same_result(((gold_figure,),), ((both_moves,),))
    print(
        f"\n  {question.name}  (tolerance {RESULT_TOLERANCE:.6%})"
        f"\n    on Trade Date      {gold_figure:.6f}"
        f"\n    on Settlement Date {both_moves:.6f}"
        f"  ({_apart(gold_figure, both_moves):.6%})"
        f"\n    rate alone         {rate_move:.6f}"
        f"  ({_apart(gold_figure, rate_move):.6%})"
    )


def test_traded_notional_is_scoped_narrowly_enough_to_separate_from_the_close(
    gold, warehouse
):
    """[DEBT-011](../.claude/docs/debt-ledger.md#debt-011--execution-price-against-market-price-cancels-at-book-level):
    the notional question is scoped to one day, and this is why.

    Valuing the same Trades at the day's close instead of at what they filled at is a
    wrong answer. Over one day it is outside the tolerance; over the whole book the
    fills either side of the close cancel and it is **inside** it, which is the entry's
    claim measured rather than asserted — and the reason a book-level notional question
    is not in this set.
    """
    [question] = [g for g in gold if g.name == VALUED_AT_EXECUTION_PRICE]
    day = substituted(
        substituted(
            question.sql,
            "fct_trade.execution_price",
            "fct_instrument_price.market_price",
        ),
        "WHERE ",
        AT_THE_CLOSE + "WHERE ",
    )
    book = substituted(question.sql, " AND fct_trade.trade_date = '2025-03-18'", "")
    book_at_close = substituted(day, " AND fct_trade.trade_date = '2025-03-18'", "")

    [(gold_figure,)] = warehouse.query(question.sql)
    [(at_close,)] = warehouse.query(day)
    [(whole_book,)] = warehouse.query(book)
    [(whole_book_at_close,)] = warehouse.query(book_at_close)

    assert not same_result(((gold_figure,),), ((at_close,),))
    assert same_result(((whole_book,),), ((whole_book_at_close,),)), (
        "the book-level cancellation DEBT-011 records has gone, so a book-level "
        "notional question would now be admissible"
    )
    print(
        f"\n  {question.name}  (tolerance {RESULT_TOLERANCE:.6%})"
        f"\n    one day,    at Execution Price {gold_figure:.6f}"
        f"\n    one day,    at the close       {at_close:.6f}"
        f"  ({_apart(gold_figure, at_close):.6%})"
        f"\n    whole book, at Execution Price {whole_book:.6f}"
        f"\n    whole book, at the close       {whole_book_at_close:.6f}"
        f"  ({_apart(whole_book, whole_book_at_close):.6%})"
    )


# -- the comparison and the loader -----------------------------------------------


def test_two_result_sets_are_the_same_answer_in_any_order():
    """A breakdown sorted the other way answered the same question."""
    assert same_result(
        (("EU", Decimal("1.5")), ("UK", Decimal("2.5"))),
        (("UK", Decimal("2.5")), ("EU", Decimal("1.5"))),
    )


def test_a_difference_beyond_the_tolerance_is_a_different_answer():
    """The tolerance is a fraction of the larger figure, so it scales with the metric."""
    assert same_result(((Decimal("1000000"),),), ((Decimal("1000000.05"),),))
    assert not same_result(((Decimal("1000000"),),), ((Decimal("1000200"),),))
    assert not same_result(((Decimal("0"),),), ((Decimal("0.01"),),))


def test_a_missing_row_is_not_the_same_answer():
    """A breakdown with a bucket dropped is a wrong answer, not a close one."""
    assert not same_result(
        (("EU", Decimal("1")), ("UK", Decimal("2"))), (("EU", Decimal("1")),)
    )


def test_a_gold_question_that_expects_no_answer_carries_no_statement(tmp_path):
    """`expects` is a claim about the file, and the loader holds it to it."""
    path = tmp_path / "bad.yaml"
    path.write_text(
        "name: x\nquestion: what was our revenue\nexpects: clarifying question\n"
        "sql: SELECT 1 AS answer\nresult:\n  - [1]\n"
    )
    with pytest.raises(GoldQuestionError, match="no gold SQL"):
        read_gold_question(path)


def test_a_gold_question_that_expects_an_answer_carries_one(tmp_path):
    """The other direction: ground truth with no statement is not ground truth."""
    path = tmp_path / "bad.yaml"
    path.write_text("name: x\nquestion: how many trades\nexpects: answer\n")
    with pytest.raises(GoldQuestionError, match="gold result"):
        read_gold_question(path)


def test_a_field_the_format_does_not_name_fails_to_load(tmp_path):
    """The dataclass field list is the file format, as it is for a Semantic Entry."""
    path = tmp_path / "bad.yaml"
    path.write_text(
        "name: x\nquestion: how many trades\nexpects: refusal\nrelevant: [Trade Count]\n"
    )
    with pytest.raises(GoldQuestionError, match="relevant"):
        read_gold_question(path)


def test_an_ending_outside_the_three_fails_to_load(tmp_path):
    """A fourth ending would be a measure grouped by a word nothing else knows."""
    path = tmp_path / "bad.yaml"
    path.write_text("name: x\nquestion: how many trades\nexpects: maybe\n")
    with pytest.raises(GoldQuestionError, match="expects"):
        read_gold_question(path)


def test_the_set_reads_back_as_the_questions_it_holds(gold):
    """What a reader of the review sees: the whole set, with the ending each expects."""
    assert len(gold) == len({question.name for question in gold})
    for question in gold:
        assert isinstance(question, GoldQuestion)
        print(f"\n  {question.expects:20s} {question.question}")


def _apart(one: Decimal, other: Decimal) -> Decimal:
    """How far apart two figures are, as a fraction of the larger."""
    return abs(one - other) / max(abs(one), abs(other))
