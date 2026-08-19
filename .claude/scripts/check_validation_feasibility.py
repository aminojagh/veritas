"""Probe what a Validation Gate can and cannot see in a generated query's parse
tree — the claim ADR-0003 rests on and nothing has ever run.

Run with:  uv run python -m veritas.ingestion            # the Warehouse is gitignored
           uv run python .claude/scripts/check_validation_feasibility.py

**This is a spike, not the Validation Gate.** No `veritas/validation/` directory
exists and this file creates none: a spike that quietly becomes the component is
how its answer stops being falsifiable. What it produces is a measurement, and
Sub-step 3.5 turns that into a go or a no-go on
[ADR-0003](../docs/adr/0003-validation-gate-is-deterministic-code.md).

Three of the four claims in the [Step 003 plan](../docs/plan/step-003-validation-feasibility.md):

  **Claim 1 — tracing.** A certified expression has to stay recognisable in a
  generated query's parse tree under the rewrites a generator performs for its
  own reasons: table aliases, an output alias, a derived table, a common table
  expression (CTE). Each shape below is traced and its verdict printed. **A shape
  that does not trace is a finding rather than a failure** — the output of this
  Step is the boundary, wherever it falls — so the two shapes measured *not* to
  trace are listed as such and the run still passes. What fails the run is the
  measurement changing: a shape that traced yesterday and does not today, or the
  reverse.

  **Claim 2 — the Restricted Column that must not reach the projection.** The
  Gate's other parse-tree rule, in the
  [Target State](../docs/design/target-state.md#flow)'s words: *"no restricted
  column in the projection"*. ADR-0003 rejected matching the text of a query
  on the ground that

    > a restricted name in a comment, a column aliased to something benign, a
    > subquery, or a `SELECT *` that expands to include a restricted column all
    > defeat text matching — and none of those are adversarial, they are ordinary
    > SQL

  which is an argument rather than a measurement. So each shape below is judged
  **twice** — once by searching the query's text for the restricted name, once
  from its parse tree — and both verdicts are recorded. The shapes where the two
  agree measure nothing. The ones where they disagree are the finding, and they
  fall on both sides: a query text matching lets through, and queries it would
  reject that are perfectly legitimate.

  The question the parse tree is asked is **does this column reach the answer**,
  not does this name appear in the statement. A column in a filter, a name in a
  comment, and a column projected inside a subquery and aggregated away before the
  answer are all in the statement and in none of them does a reader of the Grounded
  Answer see a Client's name. `columns_reaching_the_answer` is where that
  distinction is made, and four of the shapes below are there to hold it in place.

  **Claim 3 — the Shadow Metric it must catch.** A tracer that says yes to every
  statement passes claim 1 and catches nothing, so the statements that must be
  **rejected** are here beside the ones that must be allowed. Every probe that can
  be run is run through the Warehouse Adapter and its number printed, because the
  numbers are what make a rejection worth having: if a Shadow Metric returned the
  certified number, rejecting it would be an argument about naming. Each of these
  returns a different number, so allowing one means answering the question wrongly.

The certified expressions and the Restricted Columns are **Python literals in this
file**, per
[R2](../docs/plan/step-003-validation-feasibility.md#r2--the-spikes-certified-expressions-stay-python-literals--approved-by-amino-2026-08-15).
They are probe inputs, not a corpus: writing them as `semantic/metrics/*.yaml`
would fix the Semantic Layer's file format inside a spike, and that format is a
seam three Extension Register entries land against. The same reasoning covers the
Restricted Columns unchanged — an Access Profile is a part of the Validation Gate
that does not exist yet, and a spike is the wrong place to decide what one looks
like on disk.

Exits non-zero if any verdict or any number is not the one recorded here.
"""

import sys
from decimal import Decimal
from pathlib import Path
from typing import NamedTuple

import sqlglot
from sqlglot import exp
from sqlglot.lineage import lineage
from sqlglot.optimizer import optimize
from sqlglot.optimizer.merge_subqueries import merge_subqueries
from sqlglot.optimizer.qualify import qualify
from sqlglot.optimizer.scope import build_scope

CLAUDE_DIR = Path(__file__).resolve().parent.parent  # <repo>/.claude
REPO_ROOT = CLAUDE_DIR.parent                        # <repo>

sys.path.insert(0, str(REPO_ROOT))

from veritas.warehouse import DATABASE_PATH, WarehouseAdapter  # noqa: E402
# E402 is pycodestyle/ruff's "module-level import not at top of file".
# The veritas import has to come after sys.path.insert(0, str(REPO_ROOT)),
# or the script can't find the package when run from .claude/scripts/.
# The comment tells the linter that specific line is deliberate, and suppresses nothing else.

# The engine the probes are written against. ADR-0002 puts sqlglot in charge of
# retargeting, and Sub-step 3.4 is the one that asks what survives the trip to
# BigQuery; here every statement is read in the dialect it would actually run in.
DIALECT = "duckdb"

# The Reporting Currency every monetary figure below is expressed in, matching
# `check_warehouse.py --distinctions` so the two scripts' numbers are comparable.
# `Reporting Currency` is registered as *"the single currency a Grounded Answer is
# expressed in. Every monetary metric must state one"*.
#
# It is written into each probe's SQL as a literal rather than bound as a
# parameter, because these statements stand in for SQL an Orchestrator generated
# and a generator writes the currency it was asked for. `check_reporting_currency`
# below reads the literal back out of each parse tree and fails if it and this
# constant have drifted apart, so the two cannot disagree silently.
REPORTING_CURRENCY = "EUR"

# How far apart two figures must be before "a different number" means anything to
# a reader. Two numbers differing in the sixth decimal place are technically
# distinct and tell nobody anything, so a rejection that separates only those is a
# rejection nobody is better off for.
#
# The same value as `check_warehouse.py`'s MIN_DISTINCTION_GAP and deliberately
# not the same rule: that one is the floor for a Section C pair being separable in
# the loaded data, this one is the floor for a rejection being worth having. They
# are free to move apart, and neither reads the other.
MIN_GAP = Decimal("0.005")

# The optimizer rules the tracer runs, and no more. Each does exactly one job the
# tracer needs, and dropping either one is measured in the Sub-step 3.2 review
# rather than argued here:
#
#   qualify           resolves every column to the table it came from, using the
#                     real schema — which is what makes a table alias invisible.
#   merge_subqueries  inlines a subquery into the statement that selects from it.
#                     A generator can write half a certified expression inside a
#                     WITH block or a FROM (SELECT ...) and the other half outside
#                     it: the columns fetched in, the arithmetic done out. This
#                     rule removes that boundary, which puts the two halves back
#                     together into the one expression they compute.
#
# sqlglot's own `optimize()` runs fourteen rules. The other twelve are left out
# deliberately: ADR-0003 already names sqlglot as "load-bearing safety
# infrastructure", and every rule is one more rewrite trusted to preserve meaning
# between the statement a reviewer reads and the statement a Gate judges. Two is
# what the shapes below actually need — which is itself a finding, and it is
# printed on every run rather than asserted here.
TRACING_RULES = (qualify, merge_subqueries)

# The certified expressions the tracer traces to, as they would be written in a
# Metric Definition: qualified by base table, in one Reporting Currency, with the
# conversion in them.
#
# They are the real shapes rather than toy ones. A tracer proved against
# `sum(commission)` proves nothing about the metric Veritas will certify: `Gross
# Revenue` is registered as *"Σ(Commission) before any Rebate or pass-through Fee
# is deducted"*, and every monetary metric must state a Reporting Currency, so the
# honest expression carries the multiplication by an FX Rate. A parse tree with a
# conversion in it is the tree the Gate will actually see.
#
# `Traded Notional` carries one thing the Glossary's definition does not: a
# widening cast. Σ(quantity × Execution Price) × FX Rate overflows on this
# Warehouse — the engine computes the product in DECIMAL(18) and a JPY notional
# does not fit — so the expression that computes the metric at all is this one.
# That is not a claim made here: `check_widening_cast` below runs the expression
# without the cast on every run and prints the refusal, so a reader who thinks the
# cast is tidiness can see what removing it costs.
CERTIFIED_EXPRESSIONS = {
    "Gross Revenue":
        "sum(fct_trade.commission * fct_fx_rate.fx_rate)",
    "Net Revenue":
        "sum((fct_trade.commission - fct_trade.rebate - fct_trade.fee) "
        "* fct_fx_rate.fx_rate)",
    "Traded Notional":
        "sum(CAST(fct_trade.quantity AS DECIMAL(38, 6)) "
        "* fct_trade.execution_price * fct_fx_rate.fx_rate)",
}

# The Restricted Columns claim 2 probes for. A `Restricted Column` is registered as
# *"a column an Access Profile forbids from appearing in a Grounded Answer's
# projection"*, and `dim_client.client_name` is the one this Warehouse offers: of
# the ten tables in Glossary Section B it is the only column naming a firm rather
# than describing a Trade, a Position or a price.
#
# Held as (table, column) rather than as a bare name, because a parse tree resolves
# a column to the table it came from and a Gate that forbade the *name* would
# forbid it everywhere it appeared. Two tables are free to have a `name` column and
# for only one of them to be restricted.
RESTRICTED_COLUMNS = frozenset({("dim_client", "client_name")})


# What each probe's verdict means. Every probe declares one, so that "did not
# trace" is never left to the reader to interpret as good or bad news.
CERTIFIED = "certified"    # must trace: this is the metric, in some shape
FORM = "form"              # must not trace, and is arithmetically the metric
SHADOW = "shadow"          # must not trace: a Shadow Metric
BLIND_SPOT = "blind spot"  # traces, and tracing is the wrong answer
REFUSED = "refused"        # the tracer cannot read it at all


class Probe(NamedTuple):
    """One generated statement, what it is, and what this Sub-step measured.

    `metric` is the Certified Metric the probe is expected to trace to, or the
    one it is *about* where it does not trace. `same_number_as` and
    `different_number_from` name another probe, so that the numbers are checked
    against each other rather than against figures written down here — a figure
    written here would go stale the moment the simulator's seed or the loaded
    window moved.

    `unit` exists because one probe's figure is deliberately not in the Reporting
    Currency: printing an unconverted mixture of four currencies under a `EUR`
    label would be the Section C error the probe was written to demonstrate,
    committed by the script demonstrating it.
    """

    name: str
    kind: str
    metric: str | None
    why: str
    sql: str
    executable: bool = True
    same_number_as: str | None = None
    different_number_from: str | None = None
    unit: str = REPORTING_CURRENCY


# The four shapes claim 1 names, then the two where "recognisable" stops being
# obvious, then the negative cases, then the one that is caught and should not be.
#
# Every statement is portable SQL. `.claude/scripts/` is inside `check_warehouse.py`'s
# scanned roots, so these literals are read by the dialect scan Sub-step 2.6 built
# and Sub-step 3.1 narrowed, and under
# [R3](../docs/plan/step-003-validation-feasibility.md#r3--an-exemption-names-the-file-as-well-as-the-symbol--approved-and-widened-by-amino-2026-08-15)
# this file has to pass that scan **without claiming an exemption**.
PROBES = (
    Probe(
        name="bare",
        kind=CERTIFIED,
        metric="Gross Revenue",
        why="the Metric Definition's own expression, with no rewriting at all — "
            "if this does not trace, nothing else can",
        sql="SELECT sum(fct_trade.commission * fct_fx_rate.fx_rate) "
            "FROM fct_trade "
            "JOIN fct_fx_rate "
            "  ON fct_fx_rate.rate_date = fct_trade.trade_date "
            " AND fct_fx_rate.from_currency = fct_trade.denomination_currency "
            " AND fct_fx_rate.to_currency = 'EUR'",
    ),
    Probe(
        name="aliased",
        kind=CERTIFIED,
        metric="Gross Revenue",
        why="table aliases and an output alias — what a generator writes by "
            "default, and what defeats matching the text",
        sql="SELECT sum(billed.commission * rate.fx_rate) AS revenue "
            "FROM fct_trade AS billed "
            "JOIN fct_fx_rate AS rate "
            "  ON rate.rate_date = billed.trade_date "
            " AND rate.from_currency = billed.denomination_currency "
            " AND rate.to_currency = 'EUR'",
        same_number_as="bare",
    ),
    Probe(
        name="derived table",
        kind=CERTIFIED,
        metric="Gross Revenue",
        why="the conversion done in a subquery and aggregated outside it, so the "
            "certified expression is split across a boundary",
        sql="SELECT sum(converted.commission * converted.fx_rate) AS revenue "
            "FROM ( "
            "  SELECT billed.commission, rate.fx_rate "
            "  FROM fct_trade AS billed "
            "  JOIN fct_fx_rate AS rate "
            "    ON rate.rate_date = billed.trade_date "
            "   AND rate.from_currency = billed.denomination_currency "
            "   AND rate.to_currency = 'EUR' "
            ") AS converted",
        same_number_as="bare",
    ),
    Probe(
        name="common table expression",
        kind=CERTIFIED,
        metric="Gross Revenue",
        why="the same split, written the way a model that has read a style guide "
            "writes it",
        sql="WITH converted AS ( "
            "  SELECT billed.commission AS commission, rate.fx_rate AS fx_rate "
            "  FROM fct_trade AS billed "
            "  JOIN fct_fx_rate AS rate "
            "    ON rate.rate_date = billed.trade_date "
            "   AND rate.from_currency = billed.denomination_currency "
            "   AND rate.to_currency = 'EUR' "
            ") "
            "SELECT sum(converted.commission * converted.fx_rate) AS revenue "
            "FROM converted",
        same_number_as="bare",
    ),
    Probe(
        name="net revenue",
        kind=CERTIFIED,
        metric="Net Revenue",
        why="the second certified expression, so the tracer is shown to pick "
            "between metrics rather than to recognise one",
        sql="SELECT sum((billed.commission - billed.rebate - billed.fee) "
            "           * rate.fx_rate) AS net_revenue "
            "FROM fct_trade AS billed "
            "JOIN fct_fx_rate AS rate "
            "  ON rate.rate_date = billed.trade_date "
            " AND rate.from_currency = billed.denomination_currency "
            " AND rate.to_currency = 'EUR'",
        different_number_from="bare",
    ),
    Probe(
        name="net revenue by region",
        kind=CERTIFIED,
        metric="Net Revenue",
        why="a Dimension Definition applied to a metric — two more joins, a "
            "grouping column beside the metric in the projection, and the shape "
            "nearly every real question produces",
        sql="SELECT client.client_region AS client_region, "
            "       sum((billed.commission - billed.rebate - billed.fee) "
            "           * rate.fx_rate) AS net_revenue "
            "FROM fct_trade AS billed "
            "JOIN dim_account AS account "
            "  ON account.account_id = billed.account_id "
            "JOIN dim_client AS client "
            "  ON client.client_id = account.client_id "
            "JOIN fct_fx_rate AS rate "
            "  ON rate.rate_date = billed.trade_date "
            " AND rate.from_currency = billed.denomination_currency "
            " AND rate.to_currency = 'EUR' "
            "GROUP BY client.client_region "
            "ORDER BY client.client_region",
        same_number_as="net revenue",
    ),
    Probe(
        name="traded notional",
        kind=CERTIFIED,
        metric="Traded Notional",
        why="the third certified expression, and the one that converts out of the "
            "Instrument's Quotation Currency rather than the Trade's Denomination "
            "Currency — a different route through fct_fx_rate for the same table",
        sql="SELECT sum(CAST(billed.quantity AS DECIMAL(38, 6)) "
            "           * billed.execution_price * rate.fx_rate) AS traded_notional "
            "FROM fct_trade AS billed "
            "JOIN dim_instrument AS instrument "
            "  ON instrument.instrument_id = billed.instrument_id "
            "JOIN fct_fx_rate AS rate "
            "  ON rate.rate_date = billed.trade_date "
            " AND rate.from_currency = instrument.quotation_currency "
            " AND rate.to_currency = 'EUR'",
    ),
    Probe(
        name="commuted subtraction",
        kind=FORM,
        metric="Net Revenue",
        why="Net Revenue with two of its three terms swapped: commission - fee - "
            "rebate rather than commission - rebate - fee. The same number, and a "
            "different tree",
        sql="SELECT sum((billed.commission - billed.fee - billed.rebate) "
            "           * rate.fx_rate) AS net_revenue "
            "FROM fct_trade AS billed "
            "JOIN fct_fx_rate AS rate "
            "  ON rate.rate_date = billed.trade_date "
            " AND rate.from_currency = billed.denomination_currency "
            " AND rate.to_currency = 'EUR'",
        same_number_as="net revenue",
    ),
    Probe(
        name="commuted multiplication",
        kind=FORM,
        metric="Gross Revenue",
        why="Gross Revenue with the two factors written the other way round. "
            "Multiplication commutes and sqlglot does not reorder it, so this is "
            "the smallest edit that stops a certified expression being recognised",
        sql="SELECT sum(rate.fx_rate * billed.commission) AS revenue "
            "FROM fct_trade AS billed "
            "JOIN fct_fx_rate AS rate "
            "  ON rate.rate_date = billed.trade_date "
            " AND rate.from_currency = billed.denomination_currency "
            " AND rate.to_currency = 'EUR'",
        same_number_as="bare",
    ),
    Probe(
        name="open-coded net revenue",
        kind=SHADOW,
        metric="Net Revenue",
        why="the Shadow Metric claim 3 names: revenue built inline out of "
            "commission, rebate and fee as three separate sums, instead of drawn "
            "from the certified expression. It returns Net Revenue's number and "
            "is nowhere in the Semantic Layer",
        sql="SELECT sum(billed.commission * rate.fx_rate) "
            "     - sum(billed.rebate * rate.fx_rate) "
            "     - sum(billed.fee * rate.fx_rate) AS revenue "
            "FROM fct_trade AS billed "
            "JOIN fct_fx_rate AS rate "
            "  ON rate.rate_date = billed.trade_date "
            " AND rate.from_currency = billed.denomination_currency "
            " AND rate.to_currency = 'EUR'",
        same_number_as="net revenue",
        different_number_from="bare",
    ),
    Probe(
        name="unconverted commission",
        kind=SHADOW,
        metric="Gross Revenue",
        why="revenue computed inline from commission with the conversion left "
            "out — Section C's Quotation Currency against Reporting Currency row, "
            "arriving as a query rather than as a mistake in a build script",
        sql="SELECT sum(billed.commission) AS revenue FROM fct_trade AS billed",
        different_number_from="bare",
        unit="(mixed)",
    ),
    Probe(
        name="rebate silently dropped",
        kind=SHADOW,
        metric="Net Revenue",
        why="the near miss: Net Revenue's shape with one of its three terms "
            "missing. Neither Gross nor Net, and the only probe here whose number "
            "answers no question at all",
        sql="SELECT sum((billed.commission - billed.fee) * rate.fx_rate) AS revenue "
            "FROM fct_trade AS billed "
            "JOIN fct_fx_rate AS rate "
            "  ON rate.rate_date = billed.trade_date "
            " AND rate.from_currency = billed.denomination_currency "
            " AND rate.to_currency = 'EUR'",
        different_number_from="net revenue",
    ),
    Probe(
        name="notional through the wrong currency",
        kind=BLIND_SPOT,
        metric="Traded Notional",
        why="Traded Notional's certified expression, converted out of the Trade's "
            "Denomination Currency instead of the Instrument's Quotation Currency "
            "— the Section C pair registered because both columns sit on "
            "fct_trade. Nothing in the projection differs, so it traces",
        sql="SELECT sum(CAST(billed.quantity AS DECIMAL(38, 6)) "
            "           * billed.execution_price * rate.fx_rate) AS traded_notional "
            "FROM fct_trade AS billed "
            "JOIN fct_fx_rate AS rate "
            "  ON rate.rate_date = billed.trade_date "
            " AND rate.from_currency = billed.denomination_currency "
            " AND rate.to_currency = 'EUR'",
        different_number_from="traded notional",
    ),
    Probe(
        name="half-certified union",
        kind=SHADOW,
        metric="Gross Revenue",
        why="a certified branch and a Shadow Metric branch in one statement, the "
            "certified one first. It is the probe that found the tracer's own "
            "hole: reading the outermost scope alone means reading one branch and "
            "allowing the statement on the strength of it. Not executed — a total "
            "adding a euro figure to an unconverted mixture is the wrong number "
            "this project is about, and printing one to illustrate a point is "
            "still printing one",
        sql="SELECT sum(fct_trade.commission * fct_fx_rate.fx_rate) AS revenue "
            "FROM fct_trade "
            "JOIN fct_fx_rate "
            "  ON fct_fx_rate.rate_date = fct_trade.trade_date "
            " AND fct_fx_rate.from_currency = fct_trade.denomination_currency "
            " AND fct_fx_rate.to_currency = 'EUR' "
            "UNION ALL "
            "SELECT sum(fct_trade.commission) AS revenue FROM fct_trade",
        executable=False,
    ),
    Probe(
        name="unknown table",
        kind=SHADOW,
        metric=None,
        why="a table no schema knows. sqlglot resolves it without objecting, so "
            "the rejection has to come from the expression not matching rather "
            "than from resolution failing — two mechanisms a Gate must not confuse",
        sql="SELECT sum(ledger.commission) AS revenue "
            "FROM fct_revenue_ledger AS ledger",
        executable=False,
    ),
    Probe(
        name="unparseable",
        kind=REFUSED,
        metric=None,
        why="ADR-0003 commits that \"a parse failure on generated SQL must be "
            "treated as a rejection, never a pass\". This is what makes that "
            "commitment a measurement",
        sql="SELECT sum(billed.commission * rate.fx_rate FROM fct_trade AS billed",
        executable=False,
    ),
)

class RestrictedColumnProbe(NamedTuple):
    """One statement, and what this Sub-step measured about it from three angles.

    `reaches_projection` is the parse tree's answer: True when a Restricted Column
    is among the columns this statement projects, once `SELECT *` has been expanded
    against the real schema. It is the verdict the Gate would act on.

    `found_by_text` is what ADR-0003's rejected alternative says — the restricted
    name searched for in the query's text. It is recorded beside the parse tree's
    answer so that the rejection is a measurement: a shape where the two disagree
    is a query text matching gets wrong, in one direction or the other.

    `traces` is claim 1's verdict on the same statement. The two claims are
    separate checks over the same parse tree, and a statement that computes a
    Certified Metric perfectly and still must not run is what shows it.
    """

    name: str
    reaches_projection: bool
    found_by_text: bool
    traces: bool
    why: str
    sql: str


# The shapes claim 2 is measured on. Five that must be caught: the obvious one,
# the three ADR-0003's rejected alternative names as defeating text matching — a
# star expansion, a benign output alias and a subquery — and a union, where the leak
# is in a branch the outermost scope does not reach. Then four that must **not** be
# caught: three where the restricted name is in the statement but not in the answer,
# and one where the column is projected inside a subquery and aggregated away before
# the answer.
#
# The four that must not be caught matter as much as the five that must. A Gate that
# refuses every query mentioning a restricted name in a comment, or every query that
# counts distinct Clients, is a Gate people route around — and a Gate people route
# around protects nothing.
RESTRICTED_COLUMN_PROBES = (
    RestrictedColumnProbe(
        name="net revenue by client",
        reaches_projection=True,
        found_by_text=True,
        traces=True,
        why="the plain case: a Client's name beside the metric, which is what "
            "\"net revenue by client\" generates. Claim 1 allows it — the metric "
            "expression is Net Revenue's certified one — so this is the probe "
            "that shows the two claims are different checks",
        sql="SELECT client.client_name AS client_name, "
            "       sum((billed.commission - billed.rebate - billed.fee) "
            "           * rate.fx_rate) AS net_revenue "
            "FROM fct_trade AS billed "
            "JOIN dim_account AS account "
            "  ON account.account_id = billed.account_id "
            "JOIN dim_client AS client "
            "  ON client.client_id = account.client_id "
            "JOIN fct_fx_rate AS rate "
            "  ON rate.rate_date = billed.trade_date "
            " AND rate.from_currency = billed.denomination_currency "
            " AND rate.to_currency = 'EUR' "
            "GROUP BY client.client_name "
            "ORDER BY client.client_name",
    ),
    RestrictedColumnProbe(
        name="star over a join to dim_client",
        reaches_projection=True,
        found_by_text=False,
        traces=False,
        why="the restricted name appears nowhere in this query, and the query "
            "projects it. Only the schema knows what the star expands to, which "
            "is the shape ADR-0003 named and the one that cannot be matched as "
            "text at all",
        sql="SELECT * "
            "FROM fct_trade AS billed "
            "JOIN dim_account AS account "
            "  ON account.account_id = billed.account_id "
            "JOIN dim_client AS client "
            "  ON client.client_id = account.client_id",
    ),
    RestrictedColumnProbe(
        name="aliased to a benign name",
        reaches_projection=True,
        found_by_text=True,
        traces=True,
        why="the same Client name, output as `name`. Nothing in the result set "
            "says which column it came from, so a Gate reading the answer's "
            "column headings sees a benign one — the parse tree is read before "
            "the alias rather than after it",
        sql="SELECT client.client_name AS name, "
            "       sum((billed.commission - billed.rebate - billed.fee) "
            "           * rate.fx_rate) AS net_revenue "
            "FROM fct_trade AS billed "
            "JOIN dim_account AS account "
            "  ON account.account_id = billed.account_id "
            "JOIN dim_client AS client "
            "  ON client.client_id = account.client_id "
            "JOIN fct_fx_rate AS rate "
            "  ON rate.rate_date = billed.trade_date "
            " AND rate.from_currency = billed.denomination_currency "
            " AND rate.to_currency = 'EUR' "
            "GROUP BY client.client_name "
            "ORDER BY client.client_name",
    ),
    RestrictedColumnProbe(
        name="hidden behind a derived table",
        reaches_projection=True,
        found_by_text=True,
        traces=True,
        why="the fourth defeat ADR-0003's quote names — a subquery — with the "
            "Client name renamed inside it and only the benign name selected "
            "outside. The statement computes Net Revenue's certified expression "
            "exactly, so claim 1 allows it and claim 2 is the only thing standing "
            "between a Client's name and the answer",
        sql="SELECT anonymised.label AS label, "
            "       sum(anonymised.net_revenue) AS net_revenue "
            "FROM ( "
            "  SELECT client.client_name AS label, "
            "         (billed.commission - billed.rebate - billed.fee) "
            "         * rate.fx_rate AS net_revenue "
            "  FROM fct_trade AS billed "
            "  JOIN dim_account AS account "
            "    ON account.account_id = billed.account_id "
            "  JOIN dim_client AS client "
            "    ON client.client_id = account.client_id "
            "  JOIN fct_fx_rate AS rate "
            "    ON rate.rate_date = billed.trade_date "
            "   AND rate.from_currency = billed.denomination_currency "
            "   AND rate.to_currency = 'EUR' "
            ") AS anonymised "
            "GROUP BY anonymised.label "
            "ORDER BY anonymised.label",
    ),
    RestrictedColumnProbe(
        name="a union branch that names the Client",
        reaches_projection=True,
        found_by_text=True,
        traces=True,
        why="Net Revenue by region, and Net Revenue by Client name, in one "
            "statement. Both branches compute the certified expression, so claim 1 "
            "allows the whole thing; the leak is in the branch a Gate reading the "
            "outermost scope would never reach. The claim 1 counterpart is the "
            "`half-certified union` probe, which is how that hole was found",
        sql="SELECT client.client_region AS label, "
            "       sum((billed.commission - billed.rebate - billed.fee) "
            "           * rate.fx_rate) AS net_revenue "
            "FROM fct_trade AS billed "
            "JOIN dim_account AS account "
            "  ON account.account_id = billed.account_id "
            "JOIN dim_client AS client "
            "  ON client.client_id = account.client_id "
            "JOIN fct_fx_rate AS rate "
            "  ON rate.rate_date = billed.trade_date "
            " AND rate.from_currency = billed.denomination_currency "
            " AND rate.to_currency = 'EUR' "
            "GROUP BY client.client_region "
            "UNION ALL "
            "SELECT client.client_name AS label, "
            "       sum((billed.commission - billed.rebate - billed.fee) "
            "           * rate.fx_rate) AS net_revenue "
            "FROM fct_trade AS billed "
            "JOIN dim_account AS account "
            "  ON account.account_id = billed.account_id "
            "JOIN dim_client AS client "
            "  ON client.client_id = account.client_id "
            "JOIN fct_fx_rate AS rate "
            "  ON rate.rate_date = billed.trade_date "
            " AND rate.from_currency = billed.denomination_currency "
            " AND rate.to_currency = 'EUR' "
            "GROUP BY client.client_name",
    ),
    RestrictedColumnProbe(
        name="the name in a comment",
        reaches_projection=False,
        found_by_text=True,
        traces=True,
        why="a generator that was told the column is restricted, said so in a "
            "comment, and grouped by region instead. Rejecting this is the false "
            "positive claim 2 is measured on: the query obeys the rule and names "
            "the rule while obeying it",
        sql="SELECT client.client_region AS client_region, "
            "       /* grouped by region because client_name is restricted */ "
            "       sum((billed.commission - billed.rebate - billed.fee) "
            "           * rate.fx_rate) AS net_revenue "
            "FROM fct_trade AS billed "
            "JOIN dim_account AS account "
            "  ON account.account_id = billed.account_id "
            "JOIN dim_client AS client "
            "  ON client.client_id = account.client_id "
            "JOIN fct_fx_rate AS rate "
            "  ON rate.rate_date = billed.trade_date "
            " AND rate.from_currency = billed.denomination_currency "
            " AND rate.to_currency = 'EUR' "
            "GROUP BY client.client_region "
            "ORDER BY client.client_region",
    ),
    RestrictedColumnProbe(
        name="the name in a string literal",
        reaches_projection=False,
        found_by_text=True,
        traces=True,
        why="the restricted name as data rather than as a column — a label saying "
            "which column was left out. A string is not an identifier, and the "
            "difference is one a parse tree makes and a substring search cannot",
        sql="SELECT 'client_name' AS withheld_column, "
            "       sum((billed.commission - billed.rebate - billed.fee) "
            "           * rate.fx_rate) AS net_revenue "
            "FROM fct_trade AS billed "
            "JOIN fct_fx_rate AS rate "
            "  ON rate.rate_date = billed.trade_date "
            " AND rate.from_currency = billed.denomination_currency "
            " AND rate.to_currency = 'EUR'",
    ),
    RestrictedColumnProbe(
        name="the name in a filter only",
        reaches_projection=False,
        found_by_text=True,
        traces=True,
        why="one Client's revenue, with the name in the WHERE clause and out of "
            "the projection. The rule being measured is the Target State's — *no "
            "restricted column in the projection* — so this is allowed, and "
            "whether a filter on a column nobody reads should be is a different "
            "question this Step does not widen into",
        sql="SELECT sum((billed.commission - billed.rebate - billed.fee) "
            "           * rate.fx_rate) AS net_revenue "
            "FROM fct_trade AS billed "
            "JOIN dim_account AS account "
            "  ON account.account_id = billed.account_id "
            "JOIN dim_client AS client "
            "  ON client.client_id = account.client_id "
            "JOIN fct_fx_rate AS rate "
            "  ON rate.rate_date = billed.trade_date "
            " AND rate.from_currency = billed.denomination_currency "
            " AND rate.to_currency = 'EUR' "
            "WHERE client.client_name = 'Northwind Asset Management'",
    ),

    RestrictedColumnProbe(
        name="projected inside, aggregated away",
        reaches_projection=False,
        found_by_text=True,
        traces=False,
        why="how many distinct Clients traded — an ordinary question whose answer "
            "is one number and carries no name. The Client name is projected "
            "inside a subquery that cannot be folded away, and never reaches the "
            "answer. Rejecting this is the false positive a Gate that reads every "
            "scope commits; claim 1 rejects it too, for the unrelated reason that "
            "counting Clients is not a Certified Metric",
        sql="SELECT count(*) AS clients "
            "FROM ( "
            "  SELECT DISTINCT client.client_name AS label "
            "  FROM fct_trade AS billed "
            "  JOIN dim_account AS account "
            "    ON account.account_id = billed.account_id "
            "  JOIN dim_client AS client "
            "    ON client.client_id = account.client_id "
            ") AS traded",
    ),
)


problems: list[str] = []


class TracerRefused(Exception):
    """sqlglot could not read the statement, so the tracer returns no verdict.

    Raised rather than swallowed because ADR-0003 fails closed: a statement the
    parser cannot read is rejected, never passed. A tracer that returned "no
    certified expression found" here would be indistinguishable from one that had
    read the query and found nothing, which is the difference between a rejection
    and a hole.
    """


def warehouse_schema(warehouse: WarehouseAdapter) -> dict[str, dict[str, str]]:
    """The real star schema, in the shape sqlglot's optimizer wants.

    Read through `WarehouseAdapter.columns` rather than parsed out of
    `schema.sql`, so the tracer is qualified against the schema that exists rather
    than against a second reading of the file that made it.
    """
    return {
        table_name: dict(warehouse.columns(table_name))
        for table_name in warehouse.tables()
    }


def canonical(expression: exp.Expression) -> str:
    """One expression, written the one way this file compares expressions.

    `Expression.sql()` writes a parse tree back out as text, and the two flags
    settle how identifiers are spelled on the way out:

      `identify=True`   quote every table and column name, so a generator that
                        wrote `"commission"` and one that wrote `commission` come
                        out as the same text.
      `normalize=True`  lower-case them, so `SUM(T.COMMISSION)` and
                        `sum(t.commission)` do too.

    Both are about spelling and not about meaning: DuckDB is case-insensitive, and
    quoting an identifier there does not change what it refers to. Without the two
    flags the tracer would report differences no engine would.
    """
    return expression.sql(dialect=DIALECT, identify=True, normalize=True)


def certified_forms() -> dict[str, str]:
    """Canonical form -> the Certified Metric it is. The tracer's whole corpus."""
    return {
        canonical(sqlglot.parse_one(expression, dialect=DIALECT)): name
        for name, expression in CERTIFIED_EXPRESSIONS.items()
    }


def resolve(sql: str, schema: dict[str, dict[str, str]]) -> exp.Expression:
    """Parse one statement and rewrite it into the form both claims are judged on.

    The shared half of the two parse-tree claims, and the only place the rewriting
    settings live. `qualify` attaches every column to the table it came from using
    the real schema and expands `SELECT *` into the columns that star actually
    stands for; `merge_subqueries` folds a derived table or a common table
    expression (CTE) back into the statement that selects from it. After this a
    certified expression written across a subquery boundary is one expression
    again, and a star is a list of real columns.

    Claim 1 then reads the result one way and claim 2 another, in the two functions
    below.

    Raises `TracerRefused` if sqlglot cannot read the statement.
    """
    # `parse_one` turns SQL text into a tree of `exp.*` nodes; `optimize` rewrites
    # that tree with the rules it is handed and returns a new one.
    try:
        # One statement in, its root node out — `exp.Select` here, `exp.Union` for a
        # union. Bad syntax raises instead of returning a tree.
        statement = sqlglot.parse_one(sql, dialect=DIALECT)
        # `optimize` applies each rule in `rules` to the tree in turn. `qualify` is
        # handed the schema and uses it to give every column the table it came
        # from; `merge_subqueries` needs no schema and flattens subqueries away.
        return optimize(
            statement,
            schema=schema,
            dialect=DIALECT,
            rules=TRACING_RULES,
            # `optimize` passes this to `qualify` as True by default, on the
            # library's own comment that it is "needed for other optimizations to
            # perform well" — it wraps every base table in a subquery selecting
            # that table's columns. It is groundwork for the twelve rules this
            # tracer does not run, and it costs both of the two it does. Left on,
            # `qualify` resolves each column to one of those wrappers rather than
            # to `fct_trade`, so the rename below finds no base table to rename to;
            # and `merge_subqueries` spends itself unwrapping what `qualify` just
            # wrapped, instead of folding the subqueries the generator wrote.
            # Turned off, each rule does exactly the one job it is here for.
            isolate_tables=False,
            # `qualify`'s default, written out because claim 2 rests on it: a
            # `SELECT *` is replaced by the columns the schema says that star
            # stands for. Without it the projection holds one `exp.Star` node, no
            # column name is anywhere in the statement, and a Restricted Column
            # reaches the answer with nothing in the text or the tree to catch it.
            expand_stars=True,
        )
    except sqlglot.errors.SqlglotError as failure:
        raise TracerRefused(f"{type(failure).__name__}: {failure}") from failure


def projected_expressions(
    sql: str, schema: dict[str, dict[str, str]]
) -> list[exp.Expression]:
    """Claim 1's reading: every expression projected in every scope, on base tables.

    One step on top of `resolve`. Resolution qualifies columns with whatever alias
    the generator chose, so `billed.commission` stays `billed.commission`; each
    alias is replaced by the table it stands for, which is what makes aliasing
    invisible without making anything else invisible with it.

    **Every scope, not only the outermost one.** The first version of this code read
    the root scope's projections alone, which is right for every shape here and
    wrong for a union. A union node projects nothing itself, and asking it for its
    projections hands back its **first branch's** — so it read one branch, read it
    with no table sources to resolve aliases against, and never looked at the second
    at all. A statement whose first branch is certified and whose second is a Shadow
    Metric would have been judged on the first. The `half-certified union` probe is
    that case, and it is here because writing this docstring is what found it.

    Reading every scope is right for claim 1: a metric expression computed anywhere
    in the statement is a metric expression the Gate must place. It is **not** right
    for claim 2, which asks a narrower question and gets its own reading in
    `columns_reaching_the_answer` below.

    Raises `TracerRefused` if sqlglot cannot read the statement.
    """
    resolved = resolve(sql, schema)

    # `build_scope` returns one `Scope` per SELECT: the SELECT itself in
    # `scope.expression`, and in `scope.sources` what each name in its FROM and
    # JOIN clauses stands for — an `exp.Table` for a base table, another Scope for
    # a subquery. A statement with no SELECT in it at all, an INSERT among them,
    # gets no scope and so gets no verdict from this tracer.
    root = build_scope(resolved)
    if root is None:
        raise TracerRefused("sqlglot built no scope for the statement")

    found: list[exp.Expression] = []
    # `traverse()` yields every scope in the tree, innermost first and the root
    # last, so each branch of a union is read on its own turn round this loop.
    for scope in root.traverse():
        # A union's own scope projects nothing — its branches do, and each of them
        # arrives here as a scope of its own. Reading the union node as though it
        # projected is the hole described above.
        if not isinstance(scope.expression, exp.Select):
            continue
        # The lookup: alias -> the base table it stands for. A source that is
        # another Scope is a subquery `merge_subqueries` could not flatten, and is
        # left out of this map because its projections are read on its own turn.
        base_tables = {
            name: source.name
            for name, source in scope.sources.items()
            if isinstance(source, exp.Table)
        }
        # `scope.expression.selects` is the projection list: one node per selected
        # item, in the order they were written.
        for projection in scope.expression.selects:
            # `unalias()` strips an `AS revenue` wrapper and leaves the expression
            # that computes. The copy keeps the rename below out of `resolved`.
            expression = projection.unalias().copy()
            # `billed.commission` becomes `fct_trade.commission`, edited into this
            # copy of the tree. Whatever alias the generator chose is gone by the
            # time the expression is read.
            for column in expression.find_all(exp.Column):
                if column.table in base_tables:
                    column.set("table", exp.to_identifier(base_tables[column.table]))
            found.append(expression)
    return found


def metric_expressions(sql: str, schema: dict[str, dict[str, str]]) -> list[str]:
    """Claim 1's half: the canonical form of every projection that computes something.

    A projection with no aggregate in it is a grouping column — `client_region`
    sitting beside the metric — which belongs to a Dimension Definition rather than
    to this claim. The rule being measured is the
    [Target State](../docs/design/target-state.md#flow)'s: *"every metric
    expression traces to a Certified Metric"*, and a grouping column is not a
    metric expression. Which columns may appear in a projection **at all** is a
    different question — claim 2's, in `columns_reaching_the_answer` below.

    `find_all` walks a subtree for nodes of one type, and `exp.AggFunc` is the base
    class sqlglot gives every aggregate — so this asks whether anything aggregates
    without listing `sum`, `count` and `avg` by name.
    """
    return [
        canonical(expression)
        for expression in projected_expressions(sql, schema)
        if list(expression.find_all(exp.AggFunc))
    ]


def certified_metrics_only(
    expressions: list[str], corpus: dict[str, str]
) -> tuple[bool, list[str], list[str]]:
    """Claim 1's rule: allowed, what it traced to, and what it could not place.

    The rule is the Target State's, verbatim: *"every metric expression traces to
    a Certified Metric"*. **Every**, not *some* — so a statement is allowed when it
    computes at least one metric expression and all of them trace, and is rejected
    otherwise. Written as *some*, a statement could carry a certified expression
    and a Shadow Metric side by side and be allowed on the strength of the first,
    which is the `half-certified union` probe.
    """
    traced = [corpus.get(expression) for expression in expressions]
    hit = [name for name in traced if name is not None]
    untraced = [
        expression
        for expression, name in zip(expressions, traced)
        if name is None
    ]
    return bool(expressions) and not untraced, hit, untraced


# The alias every output column is given before its lineage is asked for. A
# generated query is free to name two output columns the same thing — `SELECT *`
# over a join does it by itself, twice over on this schema — and lineage is asked
# for a column *by name*, so a duplicate name would answer for the first column and
# leave the second unexamined. Numbering the outputs first removes the ambiguity
# rather than hoping a generator avoids it.
ANSWER_COLUMN = "answer_column_"


def columns_reaching_the_answer(
    sql: str, schema: dict[str, dict[str, str]]
) -> set[tuple[str, str]]:
    """Claim 2's reading: every base-table column that reaches the statement's output.

    **Reaching the answer is the question, not appearing in the statement.** The
    rule is the [Target State](../docs/design/target-state.md#flow)'s *"no restricted
    column in the projection"*, and *the projection* means the columns a reader of
    the Grounded Answer sees. Three kinds of column are therefore not returned, and
    each is a probe:

      * a column in a WHERE clause, a JOIN condition or a GROUP BY, which no reader
        of the answer sees;
      * a column projected inside a subquery and aggregated away before the answer
        — `count(*)` over `SELECT DISTINCT client_name` shows nobody a Client's
        name;
      * a name that is not a column at all: a comment, or a string literal.

    `sqlglot.lineage` is what makes the second one answerable. It takes one output
    column and walks back through every scope to the base-table columns that
    produced it, following a subquery `merge_subqueries` could not flatten and both
    branches of a union. Reading the projections of every scope instead — which is
    what claim 1 does, correctly, for its own question — counts a column the answer
    never carries, and rejects the ordinary query that asks how many distinct
    Clients traded.

    **It adds no new trust.** `lineage` runs `qualify` and nothing else, so the two
    rewrites this file is willing to rely on are still the only two. It is handed
    the already-resolved statement so that a `SELECT *` is expanded before it starts.

    Raises `TracerRefused` if sqlglot cannot read the statement.
    """
    resolved = resolve(sql, schema)

    # Number the output columns. `.selects` on a union is its first branch's
    # projection list, which is where a union's output names come from, so
    # numbering there names the outputs of both branches.
    for position, projection in enumerate(resolved.selects):
        projection.replace(
            exp.alias_(projection.unalias().copy(), f"{ANSWER_COLUMN}{position}")
        )

    reaching: set[tuple[str, str]] = set()
    try:
        for position in range(len(resolved.selects)):
            # `lineage` returns a tree of `Node`s: the root is the output column,
            # and walking it reaches one leaf per base-table column that feeds it.
            # A leaf carries the table it came from in `source` and the column as
            # `<source alias>.<column>` in `name`.
            for step in lineage(
                f"{ANSWER_COLUMN}{position}", resolved, schema=schema, dialect=DIALECT
            ).walk():
                if isinstance(step.source, exp.Table) and "." in step.name:
                    reaching.add((step.source.name, step.name.split(".")[-1]))
    except sqlglot.errors.SqlglotError as failure:
        raise TracerRefused(f"{type(failure).__name__}: {failure}") from failure
    return reaching


def restricted_columns_in_projection(
    sql: str, schema: dict[str, dict[str, str]]
) -> list[str]:
    """Claim 2's verdict: the Restricted Columns that reach the statement's answer."""
    reaching = columns_reaching_the_answer(sql, schema)
    return sorted(
        f"{table}.{column}" for table, column in reaching & RESTRICTED_COLUMNS
    )


def found_by_text(sql: str) -> list[str]:
    """What ADR-0003's rejected alternative sees: the restricted name, in the text.

    Lower-cased on both sides and nothing else — no tokenising, no stripping of
    comments or string literals — because the alternative ADR-0003 rejected is
    matching text, and handing it a parser first is giving it the very thing it was
    rejected for lacking.
    """
    lowered = sql.lower()
    return sorted(
        f"{table}.{column}"
        for table, column in RESTRICTED_COLUMNS
        if column in lowered
    )


def probe_statements() -> list[tuple[str, str]]:
    """Every probe in this file, claim 1's and claim 2's, as (name, statement)."""
    return [(probe.name, probe.sql) for probe in PROBES] + [
        (probe.name, probe.sql) for probe in RESTRICTED_COLUMN_PROBES
    ]


def check_reporting_currency() -> None:
    """Every probe that converts, converts to the currency this file claims.

    The currency is a literal inside each statement, because these stand in for
    generated SQL. That is two places one fact lives, so the second one is read
    back out of the parse tree here rather than trusted.
    """
    converting = 0
    for name, sql in probe_statements():
        try:
            statement = sqlglot.parse_one(sql, dialect=DIALECT)
        except sqlglot.errors.SqlglotError:
            continue
        for comparison in statement.find_all(exp.EQ):
            named = [
                side for side in (comparison.this, comparison.expression)
                if isinstance(side, exp.Column) and side.name == "to_currency"
            ]
            literals = [
                side for side in (comparison.this, comparison.expression)
                if isinstance(side, exp.Literal) and side.is_string
            ]
            if not named or not literals:
                continue
            converting += 1
            if literals[0].this != REPORTING_CURRENCY:
                problems.append(
                    f"probe {name!r} converts to {literals[0].this!r} where "
                    f"this file reports every figure in {REPORTING_CURRENCY} — the "
                    f"printed numbers would be labelled with a currency they are "
                    f"not in"
                )
    print(f"  Reporting Currency: {REPORTING_CURRENCY}, stated in "
          f"{converting} conversion predicates and checked against every probe")


def describe_tracer() -> dict[str, str]:
    """Print the corpus the tracer traces to, and the rewrites it is allowed.

    Both are printed rather than described, because both are the finding: which
    expressions count as certified, and how much of sqlglot's optimizer a Gate
    has to trust in order to recognise them.
    """
    corpus = certified_forms()
    print(f"  certified expressions: {len(corpus)}, as Python literals in this "
          f"script (R2)")
    for form, name in sorted(corpus.items(), key=lambda item: item[1]):
        print(f"    {name:<18} {form}")
    print(f"  tracing rules: {' · '.join(rule.__name__ for rule in TRACING_RULES)}"
          f" (sqlglot's own optimize() runs 14)")
    return corpus


def check_traces(corpus: dict[str, str], schema: dict[str, dict[str, str]]) -> None:
    """Claim 1: judge every probe by `certified_metrics_only`, and compare the
    verdict with the one this Sub-step recorded."""
    for probe in PROBES:
        expected_allowed = probe.kind in (CERTIFIED, BLIND_SPOT)
        try:
            expressions = metric_expressions(probe.sql, schema)
        except TracerRefused as refusal:
            # First line only: sqlglot's ParseError carries the offending SQL and
            # a terminal escape sequence underlining the token, which is helpful
            # at a prompt and unreadable pasted into a Step Review.
            print(f"    REFUSED   {probe.name:<36} "
                  f"{str(refusal).splitlines()[0]}")
            if probe.kind != REFUSED:
                problems.append(
                    f"probe {probe.name!r} is a {probe.kind} probe and the tracer "
                    f"could not read it at all ({refusal}) — its verdict is a "
                    f"parse failure rather than the measurement recorded here"
                )
            continue

        if probe.kind == REFUSED:
            problems.append(
                f"probe {probe.name!r} was written to be unreadable and the tracer "
                f"read it — ADR-0003's fail-closed commitment is measured by this "
                f"probe and is now measuring nothing"
            )

        allowed, hit, untraced = certified_metrics_only(expressions, corpus)

        # `dict.fromkeys` drops repeats and keeps first-seen order: one statement
        # can compute the same metric in more than one projection, and printing
        # `Net Revenue, Net Revenue` tells a reader nothing. A set would dedupe
        # too, and would reorder the names between runs.
        detail = ", ".join(dict.fromkeys(hit)) if hit else "nothing certified"
        if untraced and hit:
            detail += f", plus {len(untraced)} uncertified"
        elif untraced:
            detail = f"{len(untraced)} expression(s), none certified"
        print(f"    {'ALLOWED ' if allowed else 'REJECTED'}  {probe.name:<36} "
              f"{detail}")

        if expected_allowed and not allowed:
            problems.append(
                f"probe {probe.name!r} has to be allowed and was rejected — it "
                f"traced to {hit or 'nothing'} and could not place {untraced or 'any expression at all'}. "
                f"{probe.why}"
            )
        if expected_allowed and probe.metric not in hit:
            problems.append(
                f"probe {probe.name!r} has to trace to {probe.metric!r} and traced "
                f"to {hit or 'nothing'}. {probe.why}"
            )
        if not expected_allowed and allowed:
            problems.append(
                f"probe {probe.name!r} must be rejected and was allowed, tracing "
                f"to {hit} — {probe.why}"
            )

    kinds = {kind: sum(1 for p in PROBES if p.kind == kind)
             for kind in (CERTIFIED, FORM, SHADOW, BLIND_SPOT, REFUSED)}
    print()
    print("    " + " · ".join(f"{count} {kind}" for kind, count in kinds.items()))


def check_restricted_columns(
    corpus: dict[str, str], schema: dict[str, dict[str, str]]
) -> None:
    """Claim 2: judge every shape twice — from the text and from the parse tree —
    and compare both answers with the ones this Sub-step recorded.

    Neither answer is assumed. A shape both agree on measures nothing, so the run
    prints the pair for every probe and fails if **either** moves: the parse tree
    missing a Restricted Column is a leak, the parse tree finding one where there
    is none is the false positive that makes a Gate unusable, and the text column
    changing means ADR-0003's rejected alternative is no longer the thing being
    compared against.
    """
    print(f"    Restricted Columns: {len(RESTRICTED_COLUMNS)}, as Python literals "
          f"in this script (R2)")
    for table, column in sorted(RESTRICTED_COLUMNS):
        print(f"      {table}.{column}")
    print(f"    {'verdict':<10}{'text':<10}{'claim 1':<10}"
          f"{'shape':<38}in the projection")

    unseen_by_text = 0
    rejected_by_text_alone = 0
    for probe in RESTRICTED_COLUMN_PROBES:
        try:
            projected = restricted_columns_in_projection(probe.sql, schema)
            traces, _, _ = certified_metrics_only(
                metric_expressions(probe.sql, schema), corpus
            )
        except TracerRefused as refusal:
            problems.append(
                f"probe {probe.name!r} is a claim 2 probe and the tracer could not "
                f"read it at all ({refusal}) — its verdict is a parse failure "
                f"rather than the measurement recorded here"
            )
            continue

        by_text = found_by_text(probe.sql)
        print(f"    {'REJECTED' if projected else 'ALLOWED':<10}"
              f"{'matched' if by_text else 'missed':<10}"
              f"{'traces' if traces else '—':<10}"
              f"{probe.name:<38}{', '.join(projected) or '—'}")

        if probe.reaches_projection and not projected:
            problems.append(
                f"probe {probe.name!r} projects a Restricted Column and the parse "
                f"tree did not find one — the Gate would let it through. {probe.why}"
            )
        if not probe.reaches_projection and projected:
            problems.append(
                f"probe {probe.name!r} projects no Restricted Column and the parse "
                f"tree found {projected} — a false positive, which is the failure "
                f"this probe measures. {probe.why}"
            )
        if probe.found_by_text != bool(by_text):
            problems.append(
                f"probe {probe.name!r} was recorded as "
                f"{'matched' if probe.found_by_text else 'missed'} by text matching "
                f"and is now {'matched' if by_text else 'missed'} — the alternative "
                f"ADR-0003 rejected is no longer the one being measured against"
            )
        if probe.traces != traces:
            problems.append(
                f"probe {probe.name!r} was recorded as "
                f"{'tracing' if probe.traces else 'not tracing'} to a Certified "
                f"Metric and now does the opposite — claim 1's verdict on a claim 2 "
                f"probe has moved, so the two claims are no longer independent in "
                f"the way this run reports"
            )

        unseen_by_text += probe.reaches_projection and not probe.found_by_text
        rejected_by_text_alone += probe.found_by_text and not probe.reaches_projection

    print()
    print(f"    text matching and the parse tree disagree on "
          f"{unseen_by_text + rejected_by_text_alone} of "
          f"{len(RESTRICTED_COLUMN_PROBES)} shapes: {unseen_by_text} the text "
          f"cannot see, {rejected_by_text_alone} it would reject with no Restricted "
          f"Column in the projection at all")


def gap(left: Decimal, right: Decimal) -> Decimal:
    """How far apart two figures are, as a share of the larger."""
    largest = max(abs(left), abs(right))
    return abs(left - right) / largest if largest else Decimal("0")


def probe_total(rows: list[tuple[object, ...]]) -> Decimal:
    """The last column of every row, added up.

    One row of one column for a scalar metric; one row per bucket for a metric
    sliced by a Dimension Definition, where the total is what the slices have to
    add back up to.
    """
    return sum((Decimal(row[-1]) for row in rows), Decimal("0"))


# Traded Notional's certified expression with the widening cast taken out: the
# metric exactly as the Glossary defines it, and the version this Warehouse cannot
# compute. It is here so that the cast in CERTIFIED_EXPRESSIONS is a measurement
# rather than a preference — a later reader who takes it out for looking
# engine-shaped should be able to see, in one run, what it was holding up.
UNCAST_TRADED_NOTIONAL = (
    "SELECT sum(billed.quantity * billed.execution_price * rate.fx_rate) "
    "       AS traded_notional "
    "FROM fct_trade AS billed "
    "JOIN dim_instrument AS instrument "
    "  ON instrument.instrument_id = billed.instrument_id "
    "JOIN fct_fx_rate AS rate "
    "  ON rate.rate_date = billed.trade_date "
    " AND rate.from_currency = instrument.quotation_currency "
    " AND rate.to_currency = 'EUR'"
)


def check_widening_cast(warehouse: WarehouseAdapter) -> None:
    """Traded Notional's cast is required to compute the metric, not decoration.

    A certified expression that carries an engine-shaped detail is worth a second
    look, and the honest way to present one is to show what happens without it.
    Sub-step 3.4 asks the next question — whether the cast survives the trip to
    BigQuery — and it can only ask it if the cast is known to be load-bearing.

    A run where the engine accepts the uncast expression is a change in what this
    spike measured, so it fails rather than passing quietly: a wider default
    arithmetic, or a Warehouse whose largest notional has shrunk, both mean the
    certified expression should be revisited rather than left carrying a cast for
    a reason that has expired.
    """
    try:
        ((computed,),) = warehouse.query(UNCAST_TRADED_NOTIONAL)
    except Exception as refusal:
        print(f"    without the widening cast, Traded Notional does not compute: "
              f"{type(refusal).__name__}")
        print(f"      {str(refusal).splitlines()[0].strip()}")
        return

    print(f"    without the widening cast, Traded Notional computes: {computed}")
    problems.append(
        f"Traded Notional's certified expression carries a widening cast on the "
        f"ground that the engine overflows without one, and the engine has just "
        f"computed {computed} without it — the cast is now unexplained, so either "
        f"the engine's arithmetic has widened or this Warehouse no longer holds a "
        f"notional large enough to overflow. Re-decide the expression rather than "
        f"leaving a cast whose reason has expired"
    )


def check_numbers(warehouse: WarehouseAdapter) -> None:
    """Claim 3: execute every executable probe and check the recorded relations.

    Nothing here compares a figure with one written down in this file. Each probe
    names another probe it must equal or must differ from, and the two are
    executed against the same Warehouse in the same run — so a `--refresh`, a new
    seed or a wider window moves every figure and breaks nothing.
    """
    if not warehouse.row_count("fct_trade"):
        problems.append(
            "fct_trade is empty — run `uv run python -m veritas.ingestion` before "
            "this check, or every figure below is zero against zero and the "
            "Shadow Metrics are indistinguishable from the certified ones"
        )
        return

    totals: dict[str, Decimal] = {}
    for probe in PROBES:
        if not probe.executable:
            print(f"    {probe.name:<36} {'not executed':>22} ({probe.kind})")
            continue
        rows = warehouse.query(probe.sql)
        totals[probe.name] = probe_total(rows)
        shape = f" over {len(rows)} rows" if len(rows) > 1 else ""
        print(f"    {probe.name:<36} {totals[probe.name]:>22,.2f} "
              f"{probe.unit}{shape}")

    print()
    for probe in PROBES:
        if probe.name not in totals:
            continue
        if probe.same_number_as in totals:
            here, there = totals[probe.name], totals[probe.same_number_as]
            same = here == there
            print(f"    {'==' if same else '!='} {probe.name} and "
                  f"{probe.same_number_as}")
            if not same:
                problems.append(
                    f"probe {probe.name!r} returns {here:,.6f} and "
                    f"{probe.same_number_as!r} returns {there:,.6f}, and they have "
                    f"to be the same number: {probe.why}"
                )
        if probe.different_number_from in totals:
            here, there = totals[probe.name], totals[probe.different_number_from]
            apart = gap(here, there)
            print(f"    {probe.name} against {probe.different_number_from}: "
                  f"{here:,.2f} against {there:,.2f}, {apart:.2%} apart")
            if apart < MIN_GAP:
                problems.append(
                    f"probe {probe.name!r} and {probe.different_number_from!r} are "
                    f"{apart:.4%} apart, under the {MIN_GAP:.2%} floor — the "
                    f"rejection this Sub-step measures would cost a reader nothing, "
                    f"which is what makes it not worth having"
                )


def main() -> int:
    if not DATABASE_PATH.exists():
        print(f"  no Warehouse at {DATABASE_PATH.relative_to(REPO_ROOT)} — run "
              f"`uv run python -m veritas.ingestion` first")
        return 1

    with WarehouseAdapter() as warehouse:
        schema = warehouse_schema(warehouse)
        print(f"  Warehouse: {DATABASE_PATH.relative_to(REPO_ROOT)} · "
              f"{len(schema)} tables · "
              f"{warehouse.row_count('fct_trade')} Trades")
        check_reporting_currency()
        corpus = describe_tracer()
        print()
        print("  claim 1 — does a certified expression survive the shapes a "
              "generator writes?")
        check_traces(corpus, schema)
        print()
        print("  claim 2 — can a Restricted Column reach the projection unseen?")
        check_restricted_columns(corpus, schema)
        print()
        print("  claim 3 — what each shape actually returns, through the adapter")
        check_widening_cast(warehouse)
        check_numbers(warehouse)

    print()
    if problems:
        print(f"FAIL — {len(problems)} problem(s)")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    print("PASS — every probe's verdict and every probe's number is the one this "
          "spike recorded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
