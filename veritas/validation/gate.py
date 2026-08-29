"""The Validation Gate — the deterministic checks a generated query passes before it
executes.

[ADR-0003](../../.claude/docs/adr/0003-validation-gate-is-deterministic-code.md)
decided what this is: code over a parse tree, and *"no LLM participates in the
decision to allow or reject a query."*
[Step 003](../../.claude/docs/design/validation-feasibility.md) spent five Sub-steps
measuring whether that is possible on this schema and this data, and returned **GO**.
This module is the thing that was measured for.

**Five decisions, and all five have shipped.** The
[Target State's flow](../../.claude/docs/design/target-state.md#flow) names what
`VALIDATE` decides; the [Step 005 plan](../../.claude/docs/plan/step-005-validation-gate.md#what-the-gate-must-decide)
puts them in the order a statement meets them. Sub-step 5.1 shipped everything that
needs neither the Semantic Layer nor a certified metric — can this be read at all, is
it one statement, is it a read, will it stay inside the scan ceiling — Sub-step
5.2 added the first rule that reads the corpus: does every metric expression trace to
a Certified Metric; Sub-step 5.3 added the first rule that reads an identity: does
a Restricted Column reach the answer; Sub-step 5.4 added the rule that reads the
rows underneath the projection: is the metric computed across the joins and over the
period its own Metric Definition names; and Sub-step 5.5 added the last one — is the
Access Profile's predicate present — while widening 5.4's to admit a slice route and
to require a Metric Definition's certified filters.

**The widest thing 5.5 changed is not a rule but what an allowed statement looks
like.** Every statement Veritas runs is now scoped to the identity asking it, so a
statement carrying no access predicate is refused however certified everything else
about it is. Every probe written for the four earlier rules predates that and is
refused at the last rule rather than allowed, which the check reads off
`ValidationGateOutcome.rules` and reports as *"this rule allowed it and a later one did
not"*.

**What the Access Profile enforcement here is, and is not.**
[DEBT-008](../../.claude/docs/debt-ledger.md#debt-008--the-access-control-story-promises-more-than-it-delivers)
is open on the honesty of that claim, and its own words are the ones to repeat rather
than paraphrase:

> Access Profile enforcement is applied in the application layer, over synthetic
> data. It demonstrates the mechanism; it is not a production access control, and
> it does not protect the Warehouse from being read another way.

The entry is not paid by this sentence sitting here — its Trigger is the first
access-control claim in `README.md`, the App or a demo script, and none of the three
exists. The sentence is here so that the first person to write one finds it beside the
code instead of having to reconstruct it, and so that this module never reads as more
than it is. When
[EXT-001](../../.claude/docs/extension-register.md#ext-001--warehouse-native-security-and-concurrency)
lands, warehouse-native security **replaces** this check rather than joining it.

**The order is a safety property, not a speed one.** Two things depend on it.

  * A rule that needs nothing returns the right verdict on a day the corpus will not
    load or the Warehouse will not open. `check_validation_gate` proves that by
    judging every read-only shape through a Gate whose Warehouse raises on contact:
    an error is not a rejection, and a caller can act on *"this statement writes"*
    where it cannot act on *"the Gate did not get far enough to say."*
  * The bounded-read rule hands the engine the caller's own text. DuckDB executes
    every statement after the first in such a string **even under `EXPLAIN`** — see
    `WarehouseAdapter.estimated_scan_rows`, and the probe that drops a throwaway
    table to prove it. So the single-statement rule is not merely cheaper than the
    bounded-read rule; running it second would be a hole.

  * The tracing rule reads the Semantic Layer and the live schema, so it runs after
    every rule that reads neither. A statement that drops a table is refusable from
    the parse tree alone, and a Gate that loaded the whole Semantic Layer before
    refusing it would have made a rule that needs nothing depend on something that
    can fail underneath it.
  * The Restricted Column rule reads all of that **and** the Access Profile the
    question is asked under, so it runs last of the three. Ordering it first would gain
    nothing and cost the property above: the rules that need nothing would run behind
    the rule that needs the most, and a caller who asked *"does this write?"* would be
    told instead that the Warehouse would not open.
  * The certified-route rule reads the corpus twice over — the canonical forms, to learn
    which metric the statement computes, and then that metric's `join_paths`,
    `date_column` and `filters`, and the `routes` of every axis the statement slices by.
    It is the only rule that needs a Metric Definition's fields rather than its
    expression, so it runs after the three that do not, and the flow's own order
    ([5.4 after 5.3](../../.claude/docs/plan/step-005-validation-gate.md#what-the-gate-must-decide))
    is the same order. It matters where a statement is wrong in two ways at once: `net
    revenue by client` reaches `dim_client` through uncertified joins **and** projects a
    Client's name, and the leak is the more useful thing to be told about.
  * The access-predicate rule runs **last**, which the flow's diagram also has, and the
    reason is the same one every line above gives: it is the only rule that would refuse
    a statement for something true of every statement written before Sub-step 5.5. A
    query that computes a Shadow Metric and carries no predicate is better described as
    a Shadow Metric, and a reader told *"unscoped"* about a query that was never going
    to be allowed learns nothing they can act on.

**The Gate stops at the first rule that rejects.** A statement that does not parse
has no tree for a later rule to read, and a rejected outcome names the rules that
actually ran, so nothing has to be inferred from a verdict's silence.

**The Gate never executes the statement it judges** — not even to size it.
`VALIDATE` is step 5 of the flow and `EXECUTE` is step 6, and a Gate that runs the
query it just approved is a Gate with no boundary.
"""

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from functools import cached_property, partial
from types import MappingProxyType

import sqlglot
from sqlglot import exp
from sqlglot.lineage import lineage
from sqlglot.optimizer import optimize
from sqlglot.optimizer.merge_subqueries import merge_subqueries
from sqlglot.optimizer.qualify import qualify
from sqlglot.optimizer.scope import Scope, build_scope

from veritas.semantic import (
    DimensionDefinition,
    MetricDefinition,
    SemanticLayer,
    load_semantic_layer,
)
from veritas.validation.outcome import RejectionReason, ValidationGateOutcome
from veritas.validation.profile import ACCESS_AXIS, AccessProfile, RestrictedColumn
from veritas.warehouse import WarehouseAdapter, WarehouseError

# The shape sqlglot's optimizer wants a catalogue in, and the shape
# `WarehouseAdapter.columns_by_table` returns: table -> column -> declared type.
Schema = Mapping[str, Mapping[str, str]]

# The engine every statement is read in: the Warehouse's own, so the Gate parses a
# statement the way the engine that would run it does. The same choice, for the same
# reason, as `check_warehouse.py`'s dialect scan and the spike.
DIALECT = "duckdb"

# The optimizer rewrites the Gate trusts, and no more —
# [C5](../../.claude/docs/design/validation-feasibility.md#c5--the-rewrites-the-gate-trusts-are-named-in-code-and-there-are-two)
# in one place, *"so that widening it is a visible decision rather than a default"*.
# sqlglot's own `optimize()` runs fourteen; these two are what Sub-step 3.2 measured
# the tracer to need, and each is a rewrite trusted to preserve meaning between the
# statement a reviewer reads and the statement the Gate judges.
#
# They are the callables rather than their names, so that the names a
# `Validation Gate outcome` reports are taken off them and there is no second list to
# drift. Sub-step 5.1 declared them ahead of their first user and 5.2's `resolve` is
# that user — the only place in the Gate that applies a rewrite, so widening this
# tuple is the one edit that changes what every parse-tree rule reads.
TRUSTED_REWRITES = (qualify, merge_subqueries)

# The most rows the planner may expect a single question to read from tables.
#
# A **policy**, not a measurement: it is what Veritas is willing to spend on one
# question, so it is a round number chosen and stated rather than derived from the
# Warehouse that happens to be loaded. Nothing in this file goes stale when the data
# grows. What a reader wants beside it — how much headroom the loaded Warehouse
# actually leaves — is printed by `.claude/scripts/check_validation_gate/` on every
# run, which is where a figure a later run can move belongs.
#
# The [Target State](../../.claude/docs/design/target-state.md#extension-path-to-the-full-proposal)
# is what this becomes on the way out of the slice: *"swap DuckDB's estimate for
# BigQuery dry-run bytes-billed"*, where the same ceiling is spelled in bytes.
SCAN_CEILING = 1_000_000

# The declared type of every date column in the Warehouse. `veritas/warehouse/schema.sql`
# writes `DATE` on all six of them — `trade_date`, `settlement_date`, `movement_date`,
# `price_date`, `rate_date`, `snapshot_date` — and says why there is no `dim_date` to
# read instead: *"The date axis is the trade_date, settlement_date, movement_date,
# price_date, rate_date and snapshot_date columns."* The certified-route rule asks which
# columns in a WHERE clause are dates, and the live catalogue is the only thing that
# knows. `check_semantic_layer.py` holds the same constant for the same reason, and the
# two are free to move apart: that one asks which axes may enumerate their values.
DATE_TYPE = "DATE"

# What a `Reading` was given when nobody gave it a corpus — an empty mapping that cannot
# be edited into a corpus by accident. A `Reading` built this way answers every rule that
# needs only the statement, and fails closed at the first rule that needs more.
# `MappingProxyType` is a wrapper class from Python's standard `types` module that creates
# a read-only, dynamic view of a dictionary**.
NO_CERTIFIED_EXPRESSIONS: Mapping[str, str] = MappingProxyType({})


@dataclass(frozen=True)
class Reading:
    """Everything one judgement reads, read at most once each.

    Parsing happens once, here, rather than inside each rule: eight rules that each
    call `sqlglot.parse` are eight chances to parse with different settings, and the
    settings are the whole of what a parse tree means.

    `statements` is `None` exactly when sqlglot refused the string, and `refusal`
    carries what it said. That is
    [C6](../../.claude/docs/design/validation-feasibility.md#c6--fail-closed-on-parse-failure-by-a-rule-rather-than-by-accident)'s
    requirement made structural: a rule reads *"the parse failed"* as a fact it was
    handed, not as an empty list it has to interpret.

    **Three more things are read at most once, and that is
    [DEBT-019](../../.claude/docs/debt-ledger.md#debt-019--every-parse-tree-rule-reads-the-catalogue-and-resolves-the-statement-again)
    paid.** Until Sub-step 5.4 each parse-tree rule opened with its own
    `columns_by_table()` and its own `resolve()`, so one judgement read the catalogue
    twice and resolved one statement twice. The entry's own reason for that being wrong
    is not speed: *"two rules judging one statement against two readings of a live
    catalogue can, in principle, disagree about what a `SELECT *` stands for."* Its
    Trigger was the third rule to read the catalogue, which is the rule this Sub-step
    adds, and the shape it named is the one below — the catalogue, the resolved tree and
    the corpus are properties of the **judgement**, not of the rule.

    **Read at most once, not read eagerly**, which is the whole of why they are
    `cached_property` and not fields. The Gate's rule order is a safety property: a rule
    that needs nothing must return the right verdict on a day the Warehouse will not
    open, and a `Reading` that read the catalogue in its constructor would break that for
    every statement, including the ones refused three rules before anything needs a
    schema. `read_only.py` judges every read-only shape through a Warehouse that raises
    on contact, so a `Reading` that touched one too early fails that check rather than
    passing quietly.

    `catalogue` is *how to read the live schema* rather than the schema itself, for the
    same reason. `certified_expressions` is the corpus as `{name: expression}` — the
    Gate's own `semantic/metrics/`, or the spike's pins — and it is data rather than a
    callable because `semantic/` is committed text that cannot change under a running
    Gate, where the Warehouse's column list is live state that can.

    `slots=True` is gone, and that is what pays for the caching: `cached_property` writes
    its answer into the instance's `__dict__`, which a slotted class does not have.
    Nothing else about the class changed — it is still frozen, and no rule can edit what
    another rule read.
    """

    sql: str
    statements: tuple[exp.Expression, ...] | None = None
    refusal: str = ""
    catalogue: Callable[[], Schema] | None = None
    certified_expressions: Mapping[str, str] = NO_CERTIFIED_EXPRESSIONS

    @property
    def statement(self) -> exp.Expression:
        """The one statement, for the rules that run after the count has been checked."""
        assert self.statements is not None and len(self.statements) == 1
        return self.statements[0]

    @cached_property
    def schema(self) -> Schema:
        """The Warehouse's column list, read through the adapter once per judgement.

        [C4](../../.claude/docs/design/validation-feasibility.md#c4--the-gate-reads-the-schema-at-run-time)
        is why it is read at run time at all, and why it comes through the Warehouse
        Adapter — *"which keeps it on the right side of ADR-0002's seam."*

        A `Reading` made without a catalogue raises `TracerRefused` here rather than
        answering with an empty mapping. An empty schema is not a schema: `qualify`
        would resolve nothing against it, a `SELECT *` would expand to nothing, and
        every parse-tree rule would reach a verdict about a statement it had not read.
        Fail closed, and name the cause.
        """
        if self.catalogue is None:
            raise TracerRefused(
                "this Reading was made without a catalogue, so no rule that reads a "
                "parse tree can reach a verdict from it"
            )
        return self.catalogue()

    @cached_property
    def resolved(self) -> exp.Expression:
        """The statement rewritten into the form every parse-tree rule is judged on.

        One resolution per judgement, shared by every rule that reads a tree — so the
        tracing rule, the Restricted Column rule and the certified-route rule are all
        looking at the **same** tree, qualified against the **same** catalogue.

        It is not copied on the way out. `resolve` copies before it rewrites, so the
        `statements` a caller handed in are safe; what a rule must not do is edit this
        tree, because the rules after it read the same object. The one walk that does
        edit — `columns_reaching_the_answer`, which renames every output column before
        asking for its lineage — copies first, and says so where it does it.

        **A refusal is not memoised.** `cached_property` stores what the property
        *returns*, and a raise returns nothing — so if `resolve` raises `TracerRefused`,
        the next rule to touch `resolved` runs `resolve` again and raises again. On
        `SELECT a FROM no_such_table` that is one `qualify` per rule that asks, not one
        in total.

        Nothing in the assembled Gate pays that: the first rule to reach the refusal
        turns it into `unresolvable`, and `judge` stops at the first rule that rejects,
        so `resolve` refuses once and the judgement ends. Holding the exception in a
        field of our own, to save a repeat nothing is paying, would be a second cache —
        hand-written, on the path that ends in a refusal anyway. More code, guarding
        less, on the side where being wrong is the more expensive mistake.
        """
        return resolve(self.statement, self.schema)

    @cached_property
    def corpus(self) -> dict[str, str]:
        """`{canonical form: Certified Metric name}` — the corpus, built once per
        judgement.

        Rebuilt per judgement rather than cached on the Gate, and that is correctness
        rather than caution: a certified expression and the statement computing it are
        compared as text, so both have to be resolved against the **same** reading of
        the schema. Caching one side and re-reading the other is how the two would come
        to disagree with nothing to notice. What Sub-step 5.4 changed is that the
        rebuild now happens once for the two rules that read it instead of once each.
        The Sub-step 5.2 review measures what it costs.
        """
        return certified_forms(self.certified_expressions, self.schema)


def read(
    sql: str,
    catalogue: Callable[[], Schema] | None = None,
    certified_expressions: Mapping[str, str] = NO_CERTIFIED_EXPRESSIONS,
) -> Reading:
    """Parse the statement, or record that it could not be parsed.

    `sqlglot.parse` rather than `parse_one`, and the difference is a rule: given
    `SELECT 1; SELECT 2` this version returns two statements where `parse_one`
    returns a single `Block` node that reads like one statement and is not one.
    A Gate built on `parse_one` would have to notice `Block` by name to refuse a
    multi-statement string, which is one library release away from silence.

    Empty segments come back as `None` — `sqlglot.parse("SELECT 1;;")` is a
    statement and a nothing — and are dropped, so a trailing semicolon is not a
    second statement and an empty string is no statements at all.

    The two sources are optional because the three rules that need nothing beyond the
    statement are answerable without them, and `read(sql)` on its own is exactly that
    reading. `ValidationGate.judge` always supplies both.
    """
    try:
        parsed = sqlglot.parse(sql, dialect=DIALECT)
    except sqlglot.errors.SqlglotError as refusal:
        return Reading(
            sql=sql,
            statements=None,
            refusal=str(refusal),
            catalogue=catalogue,
            certified_expressions=certified_expressions,
        )
    return Reading(
        sql=sql,
        statements=tuple(s for s in parsed if s is not None),
        catalogue=catalogue,
        certified_expressions=certified_expressions,
    )


# A rule returns the Rejection Reasons that fired and the sentence explaining them,
# or None when the statement passed it. Reasons rather than one reason because the
# taxonomy is a contract with components that import no rule — see
# `ValidationGateOutcome`, which carries the same tuple and the correction to what
# Sub-step 5.1 predicted would first put two members in it.
Rejected = tuple[tuple[RejectionReason, ...], str]
Rule = Callable[[Reading], Rejected | None]


def parses(reading: Reading) -> Rejected | None:
    """A statement sqlglot cannot read is rejected, by a rule.

    [C6](../../.claude/docs/design/validation-feasibility.md#c6--fail-closed-on-parse-failure-by-a-rule-rather-than-by-accident)
    exists because the spike fails closed *"incidentally"* — gibberish produces no
    projections, and a tracer that requires at least one projection to trace refuses
    it as a side effect. Sub-step 3.2's review measured exactly one mutation that
    survives that, *"for a reason no probe here is written to measure"*. A refusal
    that is a side effect of another rule is removed by changing that other rule,
    and nothing anywhere says so.
    """
    if reading.statements is None:
        return (RejectionReason.UNPARSEABLE,), (
            f"sqlglot could not read this as {DIALECT} SQL: {reading.refusal}"
        )
    return None


def one_statement(reading: Reading) -> Rejected | None:
    """Exactly one statement, or reject.

    Ordered ahead of every rule that hands the engine anything, because it is what
    makes doing so safe: `EXPLAIN (FORMAT json) SELECT 1; DROP TABLE t;` plans the
    first statement and executes the second. `WarehouseAdapter.estimated_scan_rows`
    carries that, and `check_validation_gate/read_only.py` performs it on a throwaway
    table every run rather than leaving it as a warning in a docstring.

    `statements or ()` reads a failed parse as no statements rather than crashing on
    it. The state cannot arise while `parses` runs first, and the fallback is not
    defensiveness for its own sake — it is what makes C6 **legible**: delete `parses`
    from the rule list and gibberish is still refused, by this rule, under the wrong
    Rejection Reason. That is the shape of failure C6 was written about, and the check
    catches it as a mislabelled reason rather than as a traceback.
    """
    statements = reading.statements or ()
    if len(statements) != 1:
        return (RejectionReason.NOT_A_SINGLE_STATEMENT,), (
            f"Veritas runs one statement per question and this string holds "
            f"{len(statements)}"
        )
    return None


def a_read(reading: Reading) -> Rejected | None:
    """The one statement is a `SELECT`, or reject.

    Stated as what is allowed rather than as a list of what is not, because a list
    of forbidden verbs is a list somebody has to keep up with: `DROP`, `INSERT`,
    `COPY`, `PRAGMA` and `ATTACH` are the shapes
    [5.1](../../.claude/docs/plan/step-005-validation-gate.md#the-six-shapes-read-only-has-to-cover)
    names, and `INSTALL`, `SET`, `EXPORT` and whatever the engine grows next are the
    ones it does not. Every one of them is refused here by not being a `SELECT`.

    `COPY (SELECT 1) TO 'leak.csv'` is the shape worth naming: it reads nothing it
    should not and writes the answer to the filesystem, where no reader of a Grounded
    Answer will ever see it. Read-only has to mean the Warehouse **and** the
    filesystem or it does not mean much.

    A `UNION` of two `SELECT`s is refused here too, and that is a decision rather than
    an oversight: nothing in `semantic/` needs one, and a Gate that fail-closes on a
    shape it has no use for costs a rejection message where the other reading costs a
    hole. Admitting it later is one `isinstance` and a probe.
    """
    statement = reading.statement
    if not isinstance(statement, exp.Select):
        return (RejectionReason.NOT_A_READ,), (
            f"Veritas runs SELECT statements and this is a "
            f"{statement.key.upper()} statement"
        )
    return None


class TracerRefused(Exception):
    """The statement parses, and the tracer still cannot reach a verdict about it.

    Raised where the spike raised it and for the reason the spike gave: ADR-0003
    fails closed, and *"a tracer that returned 'no certified expression found' here
    would be indistinguishable from one that had read the query and found nothing,
    which is the difference between a rejection and a hole."* The Gate turns it into
    `RejectionReason.UNRESOLVABLE` — a rejection, named for the mechanism that
    produced it, never a pass.
    """


def canonical(expression: exp.Expression, dialect: str = DIALECT) -> str:
    """One expression, written the one way the Gate compares expressions.

    `Expression.sql()` writes a parse tree back out as text, and the two flags settle
    how identifiers are spelled on the way out:

      `identify=True`   quote every table and column name, so a generator that wrote
                        `"commission"` and one that wrote `commission` come out as
                        the same text.
      `normalize=True`  lower-case them, so `SUM(T.COMMISSION)` and
                        `sum(t.commission)` do too.

    Both are about spelling and not about meaning: DuckDB is case-insensitive, and
    quoting an identifier there does not change what it refers to. Without the two
    flags the Gate would report differences no engine would.

    `dialect` is a parameter rather than the constant because
    `check_validation_feasibility.py`'s claim 4 asks what a Gate standing in front of
    another engine would decide, and the same expression written as BigQuery quotes
    identifiers with backticks rather than double quotes. A retargeted statement and
    a retargeted corpus have to be written by the same generator or every comparison
    between them fails on punctuation.
    """
    return expression.sql(dialect=dialect, identify=True, normalize=True)


def resolve(
    statement: exp.Expression | str, schema: Schema, dialect: str = DIALECT
) -> exp.Expression:
    """Rewrite a statement into the form the parse-tree rules are judged on.

    The shared half of every rule that reads a tree, and the only place the rewriting
    settings live. `qualify` attaches every column to the table it came from using
    the real schema and expands `SELECT *` into the columns that star actually stands
    for; `merge_subqueries` folds a derived table or a Common Table Expression (CTE)
    back into the statement that selects from it. After this a certified expression
    written across a subquery boundary is one expression again, and a star is a list
    of real columns.

    The two rules are `TRUSTED_REWRITES`, declared at the top of this module by
    [C5](../../.claude/docs/design/validation-feasibility.md#c5--the-rewrites-the-gate-trusts-are-named-in-code-and-there-are-two)
    and applied here for the first time. sqlglot's own `optimize()` runs fourteen.

    `optimize` parses a string and copies a tree before touching either, so the
    `Reading` a caller passes in is not edited underneath the rules that have not run
    yet.

    Raises `TracerRefused` if sqlglot cannot resolve the statement — which is not the
    same as being unable to parse it, and is measured to be reachable: the engine
    plans some statements the optimizer will not resolve.

    **`AssertionError` is one of the ways it says so.** sqlglot signals some optimizer
    failures through `Expression.assert_is`, which raises the built-in `AssertionError`
    rather than anything under `sqlglot.errors` — `check_validation_gate/restricted.py`
    puts a statement in front of this function that does exactly that on every run.
    Catching it here is not catching everything: a `KeyError` out of a broken schema
    mapping still escapes, which is
    [DEBT-016](../../.claude/docs/debt-ledger.md#debt-016--the-semantic-layer-check-cannot-name-the-engines-error-type)'s
    distinction kept — *"a query the engine will not plan is a rejection, and an adapter
    that cannot open the Warehouse is a broken installation."* What is caught is the
    library refusing a caller's statement, however it spells the refusal, because a Gate
    that raises where it should reject hands its caller an error instead of a verdict.
    """
    try:
        return optimize(
            statement,
            schema=schema,
            dialect=dialect,
            rules=TRUSTED_REWRITES,
            # `optimize` passes this to `qualify` as True by default, on the
            # library's own comment that it is "needed for other optimizations to
            # perform well" — it wraps every base table in a subquery selecting that
            # table's columns. It is groundwork for the twelve rules the Gate does
            # not run, and it costs both of the two it does. Left on, `qualify`
            # resolves each column to one of those wrappers rather than to
            # `fct_trade`, so the rename in `projected_expressions` finds no base
            # table to rename to; and `merge_subqueries` spends itself unwrapping
            # what `qualify` just wrapped, instead of folding the subqueries the
            # generator wrote. Turned off, each rule does exactly the one job it is
            # here for.
            isolate_tables=False,
            # `qualify`'s default, written out because the Restricted Column rule
            # rests on it: a `SELECT *` is replaced by the columns the schema says
            # that star stands for. Without it the projection holds one `exp.Star`
            # node, no column name is anywhere in the statement, and a Restricted
            # Column reaches the answer with nothing in the text or the tree to
            # catch it.
            expand_stars=True,
        )
    except (sqlglot.errors.SqlglotError, AssertionError) as failure:
        raise TracerRefused(f"{type(failure).__name__}: {failure}") from failure


def base_tables(scope: Scope) -> dict[str, str]:
    """One scope's lookup: alias -> the base table it stands for.

    `scope.sources` maps each name in a FROM or JOIN clause to what it stands for — an
    `exp.Table` for a base table, another `Scope` for a subquery `merge_subqueries`
    could not flatten. Only the base tables are here, because a subquery's contents are
    read on its own turn round `traverse()`.
    """
    return {
        name: source.name
        for name, source in scope.sources.items()
        if isinstance(source, exp.Table)
    }


def on_base_tables(
    expression: exp.Expression, tables: Mapping[str, str]
) -> exp.Expression:
    """A copy of `expression` with every table alias replaced by the table it stands for.

    The one edit that makes aliasing invisible without making anything else invisible
    with it, and it is a **copy** because the tree it is read out of is shared by every
    rule in a judgement. Three readings need it — the projections, the joins and the
    date columns in a WHERE clause — so it is one function rather than three loops.
    """
    written = expression.copy()
    for column in written.find_all(exp.Column):
        if column.table in tables:
            column.set("table", exp.to_identifier(tables[column.table]))
    return written


def projected_expressions(
    statement: exp.Expression | str, schema: Schema, dialect: str = DIALECT
) -> list[exp.Expression]:
    """Every expression projected in every scope, written on base tables.

    One step on top of `resolve`. Resolution qualifies columns with whatever alias
    the generator chose, so `billed.commission` stays `billed.commission`; each alias
    is replaced by the table it stands for, which is what makes aliasing invisible
    without making anything else invisible with it.

    **Every scope, not only the outermost one.** A union node projects nothing itself,
    and asking it for its projections hands back its *first branch's* — so a statement
    whose first branch is certified and whose second is a Shadow Metric would be
    judged on the first. Sub-step 3.2 found that by writing this paragraph, and its
    `half-certified union` probe is the case.

    Raises `TracerRefused` if sqlglot cannot resolve the statement.
    """
    return projections_of(resolve(statement, schema, dialect))


def projections_of(resolved: exp.Expression) -> list[exp.Expression]:
    """`projected_expressions`, given the resolved tree rather than resolving one.

    The half of `projected_expressions` that reads a tree, split out in Sub-step 5.4 so
    that a judgement resolves once and every rule reads the same tree — see `Reading`,
    and [DEBT-019](../../.claude/docs/debt-ledger.md#debt-019--every-parse-tree-rule-reads-the-catalogue-and-resolves-the-statement-again),
    which the split pays. The public function above keeps the signature the spike and
    the checks call it by.
    """
    # `build_scope` returns one `Scope` per SELECT: the SELECT itself in
    # `scope.expression`, and in `scope.sources` what each name in its FROM and JOIN
    # clauses stands for — an `exp.Table` for a base table, another Scope for a
    # subquery. A statement with no SELECT in it at all gets no scope and so gets no
    # verdict from here.
    root = build_scope(resolved)
    if root is None:
        raise TracerRefused("sqlglot built no scope for the statement")

    found: list[exp.Expression] = []
    # `traverse()` yields every scope in the tree, innermost first and the root last,
    # so each branch of a union is read on its own turn round this loop.
    for scope in root.traverse():
        # A union's own scope projects nothing — its branches do, and each of them
        # arrives here as a scope of its own.
        if not isinstance(scope.expression, exp.Select):
            continue
        base = base_tables(scope)
        # `scope.expression.selects` is the projection list: one node per selected
        # item, in the order they were written.
        for projection in scope.expression.selects:
            # `unalias()` strips an `AS revenue` wrapper and leaves the expression
            # that computes. `billed.commission` then becomes `fct_trade.commission`,
            # so whatever alias the generator chose is gone by the time it is read.
            found.append(on_base_tables(projection.unalias(), base))
    return found


def metric_expressions(
    statement: exp.Expression | str, schema: Schema, dialect: str = DIALECT
) -> list[str]:
    """The canonical form of every projection that computes something.

    A projection with no aggregate in it is a grouping column — `client_region`
    sitting beside the metric — which belongs to a Dimension Definition rather than
    to this rule. The rule is the
    [Target State](../../.claude/docs/design/target-state.md#flow)'s: *"every metric
    expression traces to a Certified Metric"*, and a grouping column is not a metric
    expression. Which columns may appear in a projection **at all** is the Restricted
    Column rule's question, not this one's.

    `find_all` walks a subtree for nodes of one type, and `exp.AggFunc` is the base
    class sqlglot gives every aggregate — so this asks whether anything aggregates
    without listing `sum`, `count` and `avg` by name.
    """
    return metric_expressions_of(resolve(statement, schema, dialect), dialect)


def metric_expressions_of(
    resolved: exp.Expression, dialect: str = DIALECT
) -> list[str]:
    """`metric_expressions`, given the resolved tree rather than resolving one.

    The same split as `projections_of`, and for the same reason: two of the Gate's rules
    ask this question of one judgement's tree.
    """
    return [
        canonical(expression, dialect)
        for expression in projections_of(resolved)
        if list(expression.find_all(exp.AggFunc))
    ]


def certified_form(
    expression: str, schema: Schema, dialect: str = DIALECT
) -> str:
    """One certified expression, canonicalised the way a statement computing it is.

    **The corpus goes through the same reader as the query, and this is what makes
    `Position Change` traceable at all.** Canonicalising the corpus by parsing it
    alone compares a rewritten statement against an unrewritten expression, and the
    two agree only while the expression is flat arithmetic. `Position Change` holds a
    correlated scalar subquery, and `qualify` gives that subquery's projection an
    output alias on the statement side and not on the corpus side — one `AS
    "quantity"` of difference, and the metric traces to nothing. Sub-step 4.2 flagged
    that shape as *"the one expression shape the spike never measured"*; putting both
    sides through one reader is the answer, and it widens nothing, because it is
    `TRUSTED_REWRITES` on both sides rather than a third rewrite on one.

    The expression is resolved in a scope holding exactly the Warehouse tables it
    names, because `qualify` cannot resolve a column against a table that is not in
    scope. The tables come from the expression itself rather than from the Metric
    Definition's `from_table` and `join_paths`: a canonical form is a property of the
    expression, and reading the declared route here would make the corpus move when
    the route is edited. An alias the expression binds inside itself — `Position
    Change`'s `previous_snapshot` — is not a Warehouse table and so is correctly left
    out.

    Raises `ValueError` for an expression that does not yield exactly one metric
    expression, because that is a corpus defect rather than a caller's bad query: a
    Metric Definition whose expression aggregates nothing is not a metric, and a
    broken corpus deserves the traceback rather than a prettified rejection.
    """
    tree = sqlglot.parse_one(expression, dialect=dialect)
    named = sorted({column.table for column in tree.find_all(exp.Column)} & set(schema))
    if not named:
        raise ValueError(
            f"the certified expression {expression!r} names no Warehouse table, so "
            f"there is no scope to resolve it in"
        )
    forms = metric_expressions(
        f"SELECT {expression} AS answer FROM {', '.join(named)}", schema, dialect
    )
    if len(forms) != 1:
        raise ValueError(
            f"the certified expression {expression!r} yields {len(forms)} metric "
            f"expressions and a Certified Metric is one"
        )
    return forms[0]


def certified_forms(
    expressions: Mapping[str, str], schema: Schema, dialect: str = DIALECT
) -> dict[str, str]:
    """`{Certified Metric name: expression}` -> `{canonical form: name}`.

    The corpus the tracing rule traces to, keyed the way it is asked: given an
    expression found in a statement, which Certified Metric is it.

    It takes the expressions rather than reading `semantic/metrics/` itself so that
    `check_validation_feasibility.py` can go on tracing against the three pinned
    literals [R4 of Step 004](../../.claude/docs/plan/step-004-semantic-layer.md#r4--the-spike-is-pinned-to-the-corpus-rather-than-re-pointed-at-it--approved-by-amino-2026-08-21)
    froze, while the Gate traces against the corpus on disk. One tracer, two corpora,
    which is the whole point of
    [R2](../../.claude/docs/plan/step-005-validation-gate.md#r2--the-spike-imports-the-gate-rather-than-keeping-its-own-tracer--approved-by-amino-2026-08-25).
    """
    return {
        certified_form(expression, schema, dialect): name
        for name, expression in expressions.items()
    }


def certified_metrics_only(
    expressions: list[str], corpus: Mapping[str, str]
) -> tuple[bool, list[str], list[str]]:
    """The rule: allowed, what it traced to, and what it could not place.

    The [Target State](../../.claude/docs/design/target-state.md#flow)'s words,
    verbatim: *"every metric expression traces to a Certified Metric"*. **Every**,
    not *some* — so a statement is allowed when it computes at least one metric
    expression and all of them trace, and is rejected otherwise. Written as *some*, a
    statement could carry a certified expression and a Shadow Metric side by side and
    be allowed on the strength of the first.
    """
    traced = [corpus.get(expression) for expression in expressions]
    hit = [name for name in traced if name is not None]
    untraced = [
        expression for expression, name in zip(expressions, traced) if name is None
    ]
    return bool(expressions) and not untraced, hit, untraced


# The alias every output column is given before its lineage is asked for. A generated
# query is free to name two output columns the same thing — `SELECT *` over a join does
# it by itself, twice over on this schema — and lineage is asked for a column *by name*,
# so a duplicate name would answer for the first column and leave the second unexamined.
# Numbering the outputs first removes the ambiguity rather than hoping a generator
# avoids it.
ANSWER_COLUMN = "answer_column_"


def columns_reaching_the_answer(
    statement: exp.Expression | str, schema: Schema, dialect: str = DIALECT
) -> set[tuple[str, str]]:
    """Every base-table column that reaches the statement's output, as (table, column).

    **Reaching the answer is the question, not appearing in the statement.** The rule is
    the [Target State](../../.claude/docs/design/target-state.md#flow)'s *"no restricted
    column in the projection"*, and
    [`Restricted Column`](../../.claude/docs/glossary.md#a-the-system) registers what
    *the projection* means: judged on the parse tree once `SELECT *` has been expanded,
    and *"the name in a comment, in a string literal, or in a filter is not a projection
    of it."* Four kinds of column are therefore not returned, and the spike wrote a probe
    for each:

      * a column in a WHERE clause, a JOIN condition or a GROUP BY, which no reader of
        the answer sees;
      * a column projected inside a subquery and aggregated away before the answer —
        `count(*)` over `SELECT DISTINCT client_name` shows nobody a Client's name;
      * a name that is not a column at all: a comment, or a string literal.

    `sqlglot.lineage` is what makes the second one answerable. It takes one output column
    and walks back through every scope to the base-table columns that produced it,
    following a subquery `merge_subqueries` could not flatten and both branches of a
    union. Reading the projections of every scope instead — which is what
    `projected_expressions` does, correctly, for its own question — counts a column the
    answer never carries, and rejects the ordinary query that asks how many distinct
    Clients traded.

    **It adds no new trust.** `lineage` runs `qualify` and nothing else, so
    `TRUSTED_REWRITES` is still the whole of what
    [C5](../../.claude/docs/design/validation-feasibility.md#c5--the-rewrites-the-gate-trusts-are-named-in-code-and-there-are-two)
    names. It is handed the already-resolved statement so that a `SELECT *` is expanded
    before it starts.

    Raises `TracerRefused` if sqlglot cannot read the statement — from `resolve`, and
    from `lineage` itself, which runs `qualify` again and so can refuse in either of the
    two ways `resolve` documents. No probe has yet produced a statement that resolves and
    whose lineage then cannot be walked; the arm is kept because *"nothing found"* and
    *"could not look"* are the two answers a rule must never confuse, not because a case
    is on file.
    """
    return columns_reaching_the_answer_of(
        resolve(statement, schema, dialect), schema, dialect
    )


def columns_reaching_the_answer_of(
    resolved: exp.Expression, schema: Schema, dialect: str = DIALECT
) -> set[tuple[str, str]]:
    """`columns_reaching_the_answer`, given the resolved tree rather than resolving one.

    **The copy on the first line is load-bearing**, and it is the one hazard Sub-step
    5.4's hoist introduced. This walk renames every output column before asking for its
    lineage, which is an edit to the tree — and the tree is now shared by every rule in
    the judgement, where before Sub-step 5.4 each rule resolved its own. Numbering the
    outputs of a tree the next rule is about to read would leave that rule judging
    `answer_column_0` instead of what the generator wrote.
    """
    numbered = resolved.copy()

    # Number the output columns. `.selects` on a union is its first branch's projection
    # list, which is where a union's output names come from, so numbering there names the
    # outputs of both branches.
    for position, projection in enumerate(numbered.selects):
        projection.replace(
            exp.alias_(projection.unalias().copy(), f"{ANSWER_COLUMN}{position}")
        )

    reaching: set[tuple[str, str]] = set()
    try:
        for position in range(len(numbered.selects)):
            # `lineage` returns a tree of `Node`s: the root is the output column, and
            # walking it reaches one leaf per base-table column that feeds it. A leaf
            # carries the table it came from in `source` and the column as
            # `<source alias>.<column>` in `name`.
            for step in lineage(
                f"{ANSWER_COLUMN}{position}", numbered, schema=schema, dialect=dialect
            ).walk():
                if isinstance(step.source, exp.Table) and "." in step.name:
                    reaching.add((step.source.name, step.name.split(".")[-1]))
    except (sqlglot.errors.SqlglotError, AssertionError) as failure:
        raise TracerRefused(f"{type(failure).__name__}: {failure}") from failure
    return reaching


def restricted_columns_in_projection(
    statement: exp.Expression | str,
    restricted: Iterable[RestrictedColumn],
    schema: Schema,
    dialect: str = DIALECT,
) -> list[RestrictedColumn]:
    """The Restricted Columns that reach this statement's answer, in a stable order.

    It takes the Restricted Columns rather than reading an Access Profile itself, for the
    reason `certified_forms` takes the expressions: `check_validation_feasibility.py`
    holds its own pinned declaration of the same column and judges nine shapes against it
    on every run, while the Gate judges against whatever the Access Profile it was built
    with carries. One detector, two declarations — which is
    [R2](../../.claude/docs/plan/step-005-validation-gate.md#r2--the-spike-imports-the-gate-rather-than-keeping-its-own-tracer--approved-by-amino-2026-08-25)
    applied to the second of the two parse-tree rules, the same way 5.2 applied it to the
    first.
    """
    reaching = columns_reaching_the_answer(statement, schema, dialect)
    return sorted(
        column for column in restricted if (column.table, column.column) in reaching
    )


def restricted_columns_in_projection_of(
    resolved: exp.Expression,
    restricted: Iterable[RestrictedColumn],
    schema: Schema,
    dialect: str = DIALECT,
) -> list[RestrictedColumn]:
    """`restricted_columns_in_projection`, given the resolved tree rather than resolving
    one."""
    reaching = columns_reaching_the_answer_of(resolved, schema, dialect)
    return sorted(
        column for column in restricted if (column.table, column.column) in reaching
    )


# One join, as the Gate compares joins: the table joined, and the condition it is joined
# on written the one way `canonical` writes an expression. A pair rather than a type, for
# the reason `columns_reaching_the_answer` returns `(table, column)` pairs — it is a
# coordinate, and the thing with a name is the `Route` it belongs to.
Join = tuple[str, str]


@dataclass(frozen=True, slots=True)
class Route:
    """Where a statement's rows come from: the tables it starts at, and the joins it
    reaches the rest of them through.

    The word is the Glossary's own: a
    [`Join Path`](../../.claude/docs/glossary.md#a-the-system) is *"a certified **route**
    between two warehouse tables, so the model never invents a join"*, and
    [R8 of Step 004](../../.claude/docs/plan/step-004-semantic-layer.md#r8--the-route-a-metric-definition-carries--decided-in-sub-step-42-under-aminos-ruling-of-2026-08-22)
    is titled *"the route a Metric Definition carries"*. A Route here is the whole chain
    — one or more Join Paths, plus where the chain starts — read off a parse tree or
    built from a Metric Definition's fields, so that the two can be compared as values.

    **Sets, not sequences.** A statement that writes its two joins in the other order
    reaches the same rows, and a Gate that refused it would be refusing punctuation. What
    a set cannot express is one table joined twice on the same condition, which no
    statement in this project writes and which would be a self-cross-product if one did.

    Frozen and hashable, because it is half of a comparison and neither half may be
    edited by the rule doing the comparing.
    """

    from_tables: frozenset[str]
    joins: frozenset[Join]

    def joins_beyond(self, other: "Route") -> list[str]:
        """This Route's joins that `other` does not have, spelled for a person to read.

        Both directions of the certified-route rule are this one method: called on the
        statement it names the joins nothing certifies, and called on the certified route
        it names the joins the statement left out. Sorted, so a rejection explanation is
        the same string on every run.
        """
        return sorted(
            f"{table} ON {on}" if on else f"{table} (no join condition)"
            for table, on in self.joins - other.joins
        )


def route_of(
    statement: exp.Expression | str, schema: Schema, dialect: str = DIALECT
) -> Route:
    """The Route a statement carries, read off the resolved tree.

    Raises `TracerRefused` if sqlglot cannot resolve the statement.
    """
    return route_of_resolved(resolve(statement, schema, dialect))


def route_of_resolved(resolved: exp.Expression) -> Route:
    """`route_of`, given the resolved tree rather than resolving one.

    **Every scope, for the reason `projections_of` reads every scope**: a union projects
    nothing itself and its branches each join their own way, and a subquery
    `merge_subqueries` could not flatten carries joins that reach real rows. A route read
    from the outermost scope alone would be a route with a hole in it exactly where a
    generator would hide one.

    A join with no condition — `FROM fct_trade AS left_side, fct_trade AS right_side` —
    comes back with an empty condition rather than being skipped. It is a cross product,
    it is the one shape `read_only.py` measured the bounded rule cannot see, and no
    Metric Definition certifies one, so recording it is what makes it a rejection.

    The condition is written on base tables and then canonicalised, which is what makes
    the comparison about the join and not about the alias the generator happened to
    choose: `rate.rate_date = billed.trade_date` and
    `fct_fx_rate.rate_date = fct_trade.trade_date` are one join written twice.
    """
    root = build_scope(resolved)
    if root is None:
        raise TracerRefused("sqlglot built no scope for the statement")

    from_tables: set[str] = set()
    joins: set[Join] = set()
    for scope in root.traverse():
        if not isinstance(scope.expression, exp.Select):
            continue
        base = base_tables(scope)
        joined: set[str] = set()
        for join in scope.expression.args.get("joins", []):
            joined.add(join.this.alias_or_name)
            condition = join.args.get("on")
            joins.add(
                (
                    join.this.name,
                    ""
                    if condition is None
                    else canonical(on_base_tables(condition, base)),
                )
            )
        # What is left is what the scope starts at. Read as "the sources that were not
        # joined" rather than off the FROM node, because sqlglot has moved that node's
        # argument name between releases and `scope.sources` is the library's own answer
        # to the question this is asking.
        from_tables.update(
            table for name, table in base.items() if name not in joined
        )
    return Route(frozenset(from_tables), frozenset(joins))


def certified_route(
    expression: str,
    from_table: str,
    joins: Iterable[Join],
    schema: Schema,
    dialect: str = DIALECT,
) -> Route:
    """The Route a Metric Definition declares, read the way a statement's is.

    **The corpus goes through the same reader as the query**, which is `certified_form`'s
    argument applied to the second thing C2 requires a Metric Definition to carry. The
    declared route is assembled into the simplest statement that takes it — the metric's
    own expression over its own `from_table`, joined along its own Join Paths — and that
    statement is resolved and read by `route_of`. Canonicalising the corpus any other way
    would compare a rewritten statement against an unrewritten declaration, and the two
    agree only until a rewrite touches one of them.

    The **expression** is here for the same reason, and it is not decoration: `Position
    Change` holds a correlated scalar subquery whose own FROM clause is a scope of its
    own, and a statement computing that metric carries that scope too. Building the
    certified route without the expression would compare a statement that has that scope
    against a declaration that does not.

    It takes the fields rather than a `MetricDefinition` for the reason `certified_forms`
    takes the expressions and `restricted_columns_in_projection` takes the columns:
    `check_validation_feasibility.py` pins its own declarations and judges its dated
    measurement against those, while the Gate reads `semantic/`. One reader, two
    declarations —
    [R2](../../.claude/docs/plan/step-005-validation-gate.md#r2--the-spike-imports-the-gate-rather-than-keeping-its-own-tracer--approved-by-amino-2026-08-25)
    applied to the third of the Gate's parse-tree rules.

    A Metric Definition's `filters` are deliberately **not** assembled in. They are
    certified predicates on the rows, not a route to them, and nothing in this Sub-step
    checks that a statement carries them — see the Sub-step 5.4 review, which says what
    that costs.

    Raises `TracerRefused` if the assembled statement will not resolve, which is a corpus
    defect rather than a caller's bad query.
    """
    route = " ".join(f"JOIN {table} ON {on}" for table, on in joins)
    return route_of(
        f"SELECT {expression} AS answer FROM {from_table} {route}", schema, dialect
    )


def date_columns_filtered(
    resolved: exp.Expression, schema: Schema
) -> set[tuple[str, str]]:
    """Every date column a WHERE clause in this statement keys on, as (table, column).

    **The WHERE clause, and not the JOIN conditions.** Every Join Path in `semantic/`
    that reaches `fct_fx_rate` keys on a date, so a rule that read join conditions too
    would find `fct_trade.trade_date` in every converted metric and have nothing left to
    say. A period filter is what narrows the rows the answer covers; a join condition is
    what pairs them up.

    **Every scope**, for the reason the two readings above walk every scope — and
    `Position Change` is why it matters rather than being a precaution: its expression's
    correlated subquery carries `previous_snapshot.snapshot_date <
    fct_position_snapshot.snapshot_date` in a WHERE of its own, so a statement computing
    that metric has a date-keyed WHERE clause whether or not the question had a period in
    it.

    **A date is what the catalogue says is a date.** `DATE_TYPE` against the declared
    type, rather than a list of column names spelled out here: a seventh date column
    added to the Warehouse is caught by this rule on the day it is added, where a list
    would go on being right about six columns.
    """
    filtered: set[tuple[str, str]] = set()
    root = build_scope(resolved)
    if root is None:
        raise TracerRefused("sqlglot built no scope for the statement")
    for scope in root.traverse():
        if not isinstance(scope.expression, exp.Select):
            continue
        where = scope.expression.args.get("where")
        if where is None:
            continue
        base = base_tables(scope)
        for column in on_base_tables(where, base).find_all(exp.Column):
            if schema.get(column.table, {}).get(column.name, "").upper() == DATE_TYPE:
                filtered.add((column.table, column.name))
    return filtered


def where_conjuncts(resolved: exp.Expression) -> set[str]:
    """The outermost WHERE clause's ANDed parts, each written the way a rule compares
    them.

    Two rules ask what a statement asserts about its rows — the certified filters a
    Metric Definition names, and the Access Profile's predicate — and both ask it as
    *"is this exact predicate one of the things the statement requires"*. A set of
    canonical conjuncts is that question in one reading.

    **The outermost scope and no other**, which is the one place this reading differs
    from the three walks above it. `date_columns_filtered` asks which date columns a
    statement keys on *anywhere*, because a period is a period wherever it is written;
    this asks what narrows **the rows the answer is computed over**, and a predicate
    inside a subquery narrows that subquery. `Position Change`'s expression carries a
    correlated subquery with three conjuncts of its own in a WHERE, and none of them
    scopes the metric. Pooling every scope would let a statement satisfy the Access
    Profile by scoping a subquery nobody aggregates and leave the answer unscoped,
    which is the shape a rule about access must not be wrong about.

    `merge_subqueries` is what makes that affordable: a derived table or a Common Table
    Expression the generator wrote has already been folded into this statement by the
    time the rule reads it, so a predicate written one level down is here. One that
    could not be folded stays where it was written and does not count, which is the
    fail-closed direction.

    **ANDed parts only.** `a AND b` is two requirements and `a OR b` is one, so an
    `OR` comes back whole and matches no certified filter — correctly, since a
    predicate that holds only on some rows is not the predicate that defines a metric.
    """
    root = build_scope(resolved)
    if root is None:
        raise TracerRefused("sqlglot built no scope for the statement")
    statement = root.expression
    if not isinstance(statement, exp.Select):
        return set()
    where = statement.args.get("where")
    if where is None:
        return set()
    written = on_base_tables(where.this, base_tables(root))
    # `flatten()` on an `And` yields the leaves of the whole AND tree, so `a AND b AND
    # c` is three regardless of how the parser nested it. Every other node is one
    # requirement and is its own conjunct.
    parts = written.flatten() if isinstance(written, exp.And) else [written]
    return {canonical(part) for part in parts}


def grouped_columns(resolved: exp.Expression) -> set[tuple[str, str]]:
    """Every base-table column this statement groups by, as (table, column).

    What a `GROUP BY` names is what the answer is **sliced** by, and a slice is the one
    thing that earns a statement the joins an axis's `routes` declare —
    [R1](../../.claude/docs/plan/step-005-validation-gate.md#r1--the-access-profiles-predicate-and-the-slice-rule-ship-together-in-this-step--approved-and-widened-by-amino-2026-08-25)'s
    second source of permission. Reaching an axis is permitted by grouping on it, never
    by mentioning its table: a statement that joins `dim_instrument` and groups by
    nothing has added a join for no certified reason, and the route rule refuses it.

    **Every scope**, for the reason `route_of_resolved` and `date_columns_filtered`
    read every scope: a subquery `merge_subqueries` could not flatten groups its own
    rows, and the joins it carries are read from that same scope. A reading that took
    the outermost `GROUP BY` alone would permit joins in one scope on the strength of a
    grouping in another.

    It is deliberately not *"the columns in the projection that do not aggregate"*. The
    two readings return the same list for every statement this project writes today —
    the only builder there is, the check's `certified_statement`, projects the axis it
    groups by — so the agreement is a habit of the writer and not a property of SQL. The
    questions differ: a projection is what the answer **shows**, and a grouping is what
    it is **cut by**.

    `access.py` probes the refusal above as *"a join to a table nothing groups by"* —
    `Net Revenue`, scoped, with one extra join to `dim_instrument` and no `GROUP BY`.
    Add the grouping and nothing else, with no label in the projection:

        SELECT sum(...) AS answer FROM fct_trade JOIN ... JOIN dim_instrument ...
        WHERE dim_client.client_region = 'EU'
        GROUP BY dim_instrument.instrument_type

    The answer is now one row per instrument type, the join has the certified reason it
    lacked, and the Gate allows it. The projection still holds nothing but an aggregate,
    so a reading taken from there would find no axis, `by instrument type` would
    contribute no `routes`, and that rejection would stand over a statement the corpus
    certifies.
    """
    root = build_scope(resolved)
    if root is None:
        raise TracerRefused("sqlglot built no scope for the statement")
    sliced: set[tuple[str, str]] = set()
    for scope in root.traverse():
        if not isinstance(scope.expression, exp.Select):
            continue
        group = scope.expression.args.get("group")
        if group is None:
            continue
        base = base_tables(scope)
        for column in on_base_tables(group, base).find_all(exp.Column):
            sliced.add((column.table, column.name))
    return sliced


def access_predicate(
    access_profile: AccessProfile, semantic: SemanticLayer, dialect: str = DIALECT
) -> str:
    """The predicate that scopes a statement to one Access Profile, canonicalised.

    **The profile names the axis and the corpus holds everything else**, which is
    [R1](../../.claude/docs/plan/step-005-validation-gate.md#r1--the-access-profiles-predicate-and-the-slice-rule-ship-together-in-this-step--approved-and-widened-by-amino-2026-08-25)
    and the reason `AccessProfile` carries a region rather than a column and a list of
    regions: the `by region` Dimension Definition already registers the column, the
    buckets and — since Sub-step 5.5 — the routes, and a profile restating any of them
    would be the second registration Non-Negotiable 1 exists to prevent.

    Written through `canonical` for the reason `certified_form` and `certified_route`
    put the corpus through the same reader as the query: a rule comparing a predicate
    it built against one the generator wrote is comparing two pieces of text, and two
    readers is how they come to disagree about quoting.

    **Raises `ValueError` on a profile the corpus cannot certify** — an axis that is not
    there, an axis over more than one column, or a region that is not one of its
    buckets. That is a broken installation and not a bad query, so it is the call
    `certified_form` makes for a corpus that will not yield a metric expression rather
    than a rejection a user is handed. `ValidationGate.judge` asks for this before it
    runs a rule, so the refusal arrives when the profile is put to work rather than
    inside whichever rule happened to read it first.
    """
    axis = semantic.dimensions.get(ACCESS_AXIS)
    if axis is None:
        raise ValueError(
            f"the Access Profile is scoped along the {ACCESS_AXIS!r} axis and no "
            f"Dimension Definition publishes it, so there is no column to scope on"
        )
    if len(axis.columns) != 1:
        raise ValueError(
            f"the {ACCESS_AXIS!r} axis names {list(axis.columns)} and an Access "
            f"Profile scopes on one column — a predicate over two columns would be "
            f"two predicates, and which of them is the boundary is not written anywhere"
        )
    if access_profile.permitted_region not in axis.allowed_values:
        raise ValueError(
            f"the Access Profile {access_profile.role!r} permits the region "
            f"{access_profile.permitted_region!r} and the {ACCESS_AXIS!r} axis "
            f"certifies {list(axis.allowed_values)} — an identity scoped to a bucket "
            f"the axis does not have is an identity every statement is refused for"
        )
    return canonical(
        sqlglot.parse_one(
            f"{axis.columns[0]} = '{access_profile.permitted_region}'", dialect=dialect
        ),
        dialect,
    )


@dataclass(frozen=True, slots=True)
class ValidationGate:
    """The Gate. Built once with what its rules read, then asked for a verdict.

    It takes the Warehouse Adapter rather than a statement alone because
    [C4](../../.claude/docs/design/validation-feasibility.md#c4--the-gate-reads-the-schema-at-run-time)
    binds this Step: the Gate reads the live schema at run time and reads it
    *"through the Warehouse Adapter — which keeps it on the right side of ADR-0002's
    seam"*. Sub-step 5.1 uses the adapter for the planner's estimate only; 5.3 is
    where the column list arrives.

    The scan ceiling is a constructor argument rather than a constant read inside a
    rule so that a caller can say what it is willing to spend, and so that the rule
    can be given teeth without building a query big enough to trip the real one.

    **The Access Profile is an argument to `judge`, not a field here.** The Glossary
    registers it as *"the identity Veritas runs a **question** as"* — per question, so
    one Gate serves many identities and an application process loads the corpus once for
    all of them. That is
    [R14](../../.claude/docs/plan/step-005-validation-gate.md#r14--aminos-rulings-on-the-53-review--decided-2026-08-27),
    ruled against this class's first draft, where the profile was a second constructor
    argument: what a Gate is **built with** is what its rules read out of the world —
    the adapter, the corpus, the ceiling — and what a statement is **judged under** is
    the identity asking. A field would have made the second look like the first, and
    would have made a second identity a second Gate.

    `judge` requires it and there is no default profile, so a caller who does not say
    who is asking gets a `TypeError` rather than a verdict reached under an identity
    nobody chose. There is exactly one profile in this slice, `profile.ANALYST`, and
    naming it at every call site is what keeps the day there are two from being a
    silent change of meaning at the sites that did not name it.

    **The Semantic Layer is read once, at construction; the schema and the canonical
    forms built from it are read again on every judgement.** `semantic/` is committed
    text that cannot change under a running Gate; the Warehouse's column list is live
    state that can, which is what
    [C4](../../.claude/docs/design/validation-feasibility.md#c4--the-gate-reads-the-schema-at-run-time)
    means by *"at run time"*. The corpus's canonical forms are rebuilt with it, and
    that is correctness rather than caution: a certified expression and the statement
    computing it are compared as text, so both have to be resolved against the **same**
    reading of the schema. Caching one side and re-reading the other is how the two
    would come to disagree with nothing to notice. The Sub-step 5.2 review measures
    what the rebuild costs.
    """

    warehouse: WarehouseAdapter
    scan_ceiling: int = SCAN_CEILING
    semantic: SemanticLayer = field(default_factory=load_semantic_layer)

    def catalogue(self) -> Schema:
        """The Warehouse's column list, read at the moment a rule asks for it.

        A method rather than `self.warehouse.columns_by_table` handed straight to the
        `Reading`, and the difference is not stylistic: **reaching for that bound method
        is already touching the adapter.** `read_only.py` judges every read-only shape
        through a Warehouse that raises on any attribute access, and it caught this the
        first time `judge` was written the other way — a rule that needs nothing would
        have failed on a statement it can refuse from the parse tree alone, which is the
        exact property that check exists to hold.

        So the indirection is what makes the laziness complete: nothing about the
        Warehouse is looked at until a rule asks the `Reading` for a schema.
        """
        return self.warehouse.columns_by_table()

    def bounded(self, reading: Reading) -> Rejected | None:
        """The planner's estimate for what this will read, against the ceiling.

        The estimate comes from the engine through the adapter, never from this
        module: `EXPLAIN` is dialect, and `check_warehouse.py`'s seam scan fails the
        run on a `duckdb` import outside `veritas/warehouse/` — correctly.
        [R7](../../.claude/docs/plan/step-005-validation-gate.md#r7--the-bounded-read-uses-the-engines-estimate-if-the-adapter-can-reach-it--approved-by-amino-2026-08-25)
        put two rules up and said the measurement chooses between them; this is the
        engine's estimate, which Sub-step 5.1 found reachable in a machine-readable
        plan, so the parse-tree fallback R7 pre-approved was not needed.

        **An engine that will not plan the statement is a rejection, not a crash.**
        A query naming a column that does not exist is refused here rather than at
        execution, and it is refused as unbounded because that is the honest verdict
        this rule can reach: the planner would not say how much it reads. That
        distinction is only expressible because
        [DEBT-016](../../.claude/docs/debt-ledger.md#debt-016--the-semantic-layer-check-cannot-name-the-engines-error-type)
        was paid in the same Sub-step — a `WarehouseError` is the engine refusing a
        caller's SQL, where a bare `Exception` here would have swallowed a broken
        adapter and called it a bad query.
        """
        try:
            scanned = self.warehouse.estimated_scan_rows(reading.statement.sql(DIALECT))
        except WarehouseError as refusal:
            return (RejectionReason.UNBOUNDED_SCAN,), (
                f"the engine would not plan this statement, so how much it reads is "
                f"unknown and an unknown scan is not a bounded one: {refusal}"
            )
        if scanned > self.scan_ceiling:
            return (RejectionReason.UNBOUNDED_SCAN,), (
                f"the planner expects to read {scanned} rows and the ceiling is "
                f"{self.scan_ceiling}"
            )
        return None

    def traces(self, reading: Reading) -> Rejected | None:
        """Every metric expression in the statement traces to a Certified Metric.

        The [Target State](../../.claude/docs/design/target-state.md#flow)'s rule and
        the one [ADR-0001](../../.claude/docs/adr/0001-semantic-layer-as-the-retrieval-corpus.md)
        exists to make decidable, in three failures a chart can tell apart: a
        statement that will not resolve, one that computes something the corpus does
        not hold, and one that computes nothing at all.

        **The corpus comes from `semantic/metrics/` through the loader, not from
        Python literals.** That is the difference between the Gate and the spike, and
        the reason [R2](../../.claude/docs/plan/step-005-validation-gate.md#r2--the-spike-imports-the-gate-rather-than-keeping-its-own-tracer--approved-by-amino-2026-08-25)
        matters: one tracer reads two corpora, and the spike's pins are what keep its
        dated measurement honest while this reads whatever `semantic/` now says.

        Both halves of the rule are load-bearing. *Every* expression must trace, or a
        certified expression and a Shadow Metric sitting side by side would be allowed
        on the strength of the first; and *at least one* must be found, or a statement
        that aggregates nothing would pass vacuously.

        The catalogue, the resolved tree and the corpus come off the `Reading`, which
        reads each of them at most once per judgement — see `Reading`, and
        [DEBT-019](../../.claude/docs/debt-ledger.md#debt-019--every-parse-tree-rule-reads-the-catalogue-and-resolves-the-statement-again),
        which Sub-step 5.4 paid.
        """
        try:
            expressions = metric_expressions_of(reading.resolved)
        except TracerRefused as refusal:
            return (RejectionReason.UNRESOLVABLE,), (
                f"the statement parses but will not resolve against the Warehouse's "
                f"columns, so no expression in it can be traced: {refusal}"
            )

        corpus = reading.corpus
        allowed, hit, untraced = certified_metrics_only(expressions, corpus)
        if allowed:
            return None
        # Past here the statement is rejected and the branches only choose which
        # reason says so. The verdict itself is `certified_metrics_only`'s, so the
        # rule lives in one place and a change to it moves what the Gate decides
        # rather than only what the Gate says.
        if not expressions:
            return (RejectionReason.NO_METRIC_EXPRESSION,), (
                "Veritas answers questions with Certified Metrics and this statement "
                "computes none — every projection in it is a column, not a metric"
            )
        if untraced:
            # `dict.fromkeys` drops repeats and keeps first-seen order: one statement
            # can compute the same metric in more than one projection, and naming it
            # twice tells a reader nothing. A set would dedupe too, and would reorder
            # the names between runs.
            traced = ", ".join(dict.fromkeys(hit)) or "nothing"
            return (RejectionReason.SHADOW_METRIC,), (
                f"{len(untraced)} of {len(expressions)} expression(s) in this "
                f"statement are computed inline rather than drawn from the Semantic "
                f"Layer, and every one has to trace — traced {traced}, could not "
                f"place {untraced[0]}"
            )
        raise AssertionError(
            f"certified_metrics_only rejected {expressions} against a corpus of "
            f"{len(corpus)} forms without leaving anything untraced, which no "
            f"reading of the rule allows"
        )

    def no_restricted_column(
        self, reading: Reading, access_profile: AccessProfile
    ) -> Rejected | None:
        """No column the Access Profile restricts reaches this statement's answer.

        The one rule that takes an argument beyond the `Reading`, because it is the one
        rule that judges against an identity rather than against the world the Gate was
        built with. `rules` binds it to the profile `judge` was called with.

        The [Target State](../../.claude/docs/design/target-state.md#flow)'s *"no
        restricted column in the projection"*, and the other half of
        [C3](../../.claude/docs/design/validation-feasibility.md#c3--the-two-parse-tree-rules-ship-together),
        which is why it is in the same Step as the tracing rule and not a Step later:
        *"a Step that builds certified-metrics-only alone and defers the Restricted
        Column check has not built half a Gate; it has built a Gate that passes the
        leak."*

        **The question is whether the column reaches the answer, not whether the name
        appears.** `columns_reaching_the_answer` is where that distinction is made and
        argued; a Gate that refused every query mentioning a restricted name in a
        comment, or every query counting distinct Clients, is a Gate people route
        around, and a Gate people route around protects nothing.

        `SELECT *` is the shape this rule cannot do without
        [C4](../../.claude/docs/design/validation-feasibility.md#c4--the-gate-reads-the-schema-at-run-time)'s
        run-time schema read: it is *"the one shape whose restricted name exists nowhere
        in its own text"*, and only the live column list says what the star stands for.

        **An unreadable statement is a rejection here too.** In the assembled Gate this
        branch is unreached: an earlier rule refuses every statement found so far that
        cannot be read — the bounded rule refuses what the engine will not plan, and the
        tracing rule refuses what the optimizer will not resolve.
        `check_validation_gate/restricted.py` measures that on every run, naming which
        rule caught which, rather than leaving it to be assumed. It is kept because the two
        refusals are not the same refusal: `lineage` walks a resolved tree and can
        refuse one the optimizer accepted, and a rule that let that through would fail
        open on exactly the statement nobody wrote a probe for.
        """
        try:
            projected = restricted_columns_in_projection_of(
                reading.resolved, access_profile.restricted_columns, reading.schema
            )
        except TracerRefused as refusal:
            return (RejectionReason.UNRESOLVABLE,), (
                f"the statement parses but the columns reaching its answer cannot be "
                f"read, so whether a Restricted Column is among them is unknown: "
                f"{refusal}"
            )
        if projected:
            names = ", ".join(str(column) for column in projected)
            return (RejectionReason.RESTRICTED_COLUMN,), (
                f"the Access Profile {access_profile.role!r} may not see "
                f"{names} and this statement's answer would carry "
                f"{'them' if len(projected) > 1 else 'it'}"
            )
        return None

    def traced_metrics(self, reading: Reading) -> list[str]:
        """The Certified Metrics this statement computes, in the order it computes them.

        The certified-route rule needs to know **whose** route to compare against, and it
        derives that here rather than being handed it by the tracing rule that ran before
        it. Two reasons, and the second is the one that matters:

          * it costs almost nothing. The catalogue, the resolved tree and the corpus are
            all read once per judgement, so what this repeats is one walk of a tree the
            `Reading` already holds and one dictionary lookup per projection;
          * a rule that took another rule's output would stop being independently
            answerable. Deleting the tracing rule from `rules()` would then break the
            route rule too, and the check's first mutation is exactly that deletion —
            a mutation that takes two rules out is a mutation that measures neither.

        `dict.fromkeys` drops repeats and keeps first-seen order, because a statement can
        compute one metric in two projections and the route is the same route either way.
        """
        expressions = metric_expressions_of(reading.resolved)
        _, hit, _ = certified_metrics_only(expressions, reading.corpus)
        return list(dict.fromkeys(hit))

    def routed(self, reading: Reading) -> Rejected | None:
        """The statement reaches its rows the way the Metric Definition says, or reject.

        [C2](../../.claude/docs/design/validation-feasibility.md#c2--a-metric-definition-carries-its-join-path-and-its-date-predicate)
        in one rule, and the payment of
        [DEBT-014](../../.claude/docs/debt-ledger.md#debt-014--the-spike-allows-a-query-the-gate-must-reject).
        The reason both exist is one sentence of C2's: *"a certified expression pins down
        the arithmetic and not the rows it is computed over."* The tracing rule reads the
        projection, and `Traded Notional` converted out of the Trade's Denomination
        Currency instead of the Instrument's Quotation Currency **projects identically**
        to the right one. Nothing the tracing rule can see separates them. The join does.

        **Both halves are one rule because C2 and DEBT-014 treat them as one question.**
        [R4 of Step 003](../../.claude/docs/design/validation-feasibility.md#r4--debt-014-is-amended-to-name-the-date-predicate--approved-by-amino-2026-08-20)
        settled that: the Trade Date / Settlement Date question *"is this entry's
        question, not a second one"*, because it is the same shape — two columns on
        `fct_trade`, a projection that cannot tell them apart, and a Section C pair that
        exists because the choice moves the number. They are two `Rejection Reason`
        members because they are two different things to go and fix.

        **Permission comes from a list, and a join no entry names is a rejection.** The
        list has three sources and no fourth —
        [R1](../../.claude/docs/plan/step-005-validation-gate.md#r1--the-access-profiles-predicate-and-the-slice-rule-ship-together-in-this-step--approved-and-widened-by-amino-2026-08-25):
        the metric's own `join_paths`, the `routes` of each axis the statement groups
        by, and the route the Access Profile's predicate needs, which is the `by region`
        axis's own `routes` read from the same field. The Gate never searches
        `semantic/joins/` for a chain that would reach a table, which is that ruling's
        decision and the difference between a Gate and a query planner.

        **Permitted and required are two lists, and the difference is the whole of what
        Sub-step 5.5 changed here.** Until 5.5 they were one: the metric's own route was
        both the most a statement could carry and the least. A slice route and the
        access route are permission without obligation — a statement need not slice by
        region, and one that does not must not be told it *omitted* a join its Metric
        Definition certifies. So a join beyond `permitted_route` is a rejection and a
        join absent from `required_route` is a rejection, and the two questions are
        asked of two different Routes.

        **Reachability is asked before the joins are compared**, because the two
        rejections answer different questions and only one of them is actionable as
        written. `Cash Balance by instrument type` names an axis with no route from
        `fct_balance_snapshot`; comparing joins first would refuse it for whichever
        tables the generator joined trying to get there, and the honest answer is that a
        Cash Balance has no Instrument.

        **A statement that traces to nothing is not this rule's business.** It returns
        `None` — there is no metric whose route to compare against, and the tracing rule
        one place earlier has already refused it. In the assembled Gate that branch is
        unreached, and `route.py` says which rule caught what rather than leaving it to
        be assumed.
        """
        try:
            hit = self.traced_metrics(reading)
            sliced = grouped_columns(reading.resolved)
        except TracerRefused as refusal:
            return (RejectionReason.UNRESOLVABLE,), (
                f"the statement parses but will not resolve against the Warehouse's "
                f"columns, so the route it takes to its rows cannot be read: {refusal}"
            )
        if not hit:
            return None

        metrics = [self.semantic.metrics[name] for name in hit]
        axes = self.axes_sliced_by(sliced)
        unreachable = self.unreachable_axis(metrics, axes)
        if unreachable is not None:
            return unreachable

        permitted = self.permitted_route(metrics, axes, reading.schema)
        required = self.required_route(metrics, reading.schema)
        carried = route_of_resolved(reading.resolved)

        uncertified = carried.joins_beyond(permitted)
        if uncertified:
            return (RejectionReason.UNCERTIFIED_ROUTE,), (
                f"this statement computes {', '.join(hit)} across a join no Semantic "
                f"Entry certifies for it — {'; '.join(uncertified)}"
            )
        missing = required.joins_beyond(carried)
        if missing:
            return (RejectionReason.UNCERTIFIED_ROUTE,), (
                f"this statement computes {', '.join(hit)} without the join its Metric "
                f"Definition is certified across — {'; '.join(missing)}"
            )
        if carried.from_tables != required.from_tables:
            return (RejectionReason.UNCERTIFIED_ROUTE,), (
                f"this statement computes {', '.join(hit)} starting from "
                f"{', '.join(sorted(carried.from_tables))}, and its Metric Definition "
                f"starts from {', '.join(sorted(required.from_tables))}"
            )

        asserted = where_conjuncts(reading.resolved)
        uncarried = sorted(self.certified_filters(metrics) - asserted)
        if uncarried:
            return (RejectionReason.MISSING_CERTIFIED_FILTER,), (
                f"this statement computes {', '.join(hit)} without the certified "
                f"predicate that defines it — {'; '.join(uncarried)}"
            )

        # `date_column` is written `table.column` in the entry, and the loader keeps it
        # as the entry wrote it, so it is split here into the pair the parse tree
        # answers in. `check_semantic_layer.py` is what refuses one written any other
        # way, which is why there is no second reading of that shape here.
        certified_dates = {
            tuple(metric.date_column.split(".", 1)) for metric in metrics
        }
        filtered = date_columns_filtered(reading.resolved, reading.schema)
        stray = sorted(
            f"{table}.{column}" for table, column in filtered - certified_dates
        )
        if stray:
            keyed = ", ".join(
                sorted(f"{table}.{column}" for table, column in certified_dates)
            )
            return (RejectionReason.UNCERTIFIED_DATE_COLUMN,), (
                f"this statement filters {', '.join(hit)} on {', '.join(stray)}, and "
                f"the period {'each' if len(hit) > 1 else 'its'} Metric Definition is "
                f"certified over is keyed on {keyed}"
            )
        return None

    def unreachable_axis(
        self,
        metrics: Iterable[MetricDefinition],
        axes: Iterable[DimensionDefinition],
    ) -> Rejected | None:
        """The half of the route rule that answers *"can this question be asked at
        all?"*.

        An axis's `routes` has a key per fact table it can be reached from, and an
        **absent key** is a real answer rather than an omission: `by instrument type`
        names `fct_trade` and `fct_position_snapshot` and nothing else, because a Cash
        Balance has no Instrument. This is the branch that says so by name.

        It is asked before the joins are compared because the two rejections are
        different news. An uncertified route says the SQL is wrong and the question is
        fine; this says the **question** is not one this metric can answer, and no
        rewriting will change that. A reader acting on the first edits a query and a
        reader acting on the second asks a different one.

        A method of its own rather than four lines inside `routed`, so that
        `check_validation_gate/access.py` can assemble a Gate without it and measure
        what it is worth — a rule nobody can delete is a rule nobody has measured.
        """
        for axis in axes:
            for metric in metrics:
                if metric.from_table not in axis.routes:
                    return (RejectionReason.UNREACHABLE_AXIS,), (
                        f"this statement slices {metric.name} by {axis.name!r}, and "
                        f"that axis declares no route from {metric.from_table} — it is "
                        f"reachable from "
                        f"{', '.join(sorted(axis.routes)) or 'no table at all'}, and "
                        f"the Gate does not go looking for a chain nothing certifies"
                    )
        return None

    def certified_filters(self, metrics: Iterable[MetricDefinition]) -> set[str]:
        """The predicates these Certified Metrics require, written the way a statement's
        WHERE clause is read.

        The third of the three fields
        [C2](../../.claude/docs/design/validation-feasibility.md#c2--a-metric-definition-carries-its-join-path-and-its-date-predicate)
        puts on a Metric Definition to pin down which rows its expression is computed
        over, and the one Sub-step 5.4 did not read —
        [DEBT-020](../../.claude/docs/debt-ledger.md#debt-020--the-gate-checks-a-metrics-route-and-not-its-certified-filters),
        paid here. `Realised P&L` shares `fct_accounting_movement` with three other
        movement types and `filters` is the whole difference between them.

        **The corpus goes through the same reader as the query**, which is
        `certified_form`'s argument and `certified_route`'s applied to the third field:
        the filter is parsed and canonicalised exactly as the statement's own conjuncts
        are, so `movement.movement_type = 'realised P&L'` and the entry's
        `fct_accounting_movement.movement_type = 'realised P&L'` are one predicate
        written twice. A filter parsed on its own needs no schema — it names its table
        already, and nothing in it is a star to expand.

        A method of its own for `unreachable_axis`'s reason: `access.py` builds a Gate
        whose version of this returns nothing, and watches DEBT-020's statement go back
        to being allowed.
        """
        return {
            canonical(sqlglot.parse_one(predicate, dialect=DIALECT))
            for metric in metrics
            for predicate in metric.filters
        }

    def axes_sliced_by(
        self, columns: Iterable[tuple[str, str]]
    ) -> list[DimensionDefinition]:
        """The certified axes a statement's `GROUP BY` columns belong to.

        A grouping column that belongs to no axis is not an error here and grants no
        permission: it is a slice by something the corpus does not certify as an axis,
        and if reaching it needed a join then that join is one nothing names. Which
        columns may be grouped by **at all** is a question this slice does not ask — the
        [Target State](../../.claude/docs/design/target-state.md#flow)'s parse-tree
        checks are about metric expressions, restricted columns and the access
        predicate, and a fourth about grouping columns would be a rule no ruling asked
        for.

        Sorted by name so that a rejection naming an axis names the same one on every
        run, for the reason `RestrictedColumn` is ordered.
        """
        grouped = set(columns)
        return sorted(
            (
                axis
                for axis in self.semantic.dimensions.values()
                if any(
                    tuple(column.split(".", 1)) in grouped for column in axis.columns
                )
            ),
            key=lambda axis: axis.name,
        )

    def required_route(
        self, metrics: Iterable[MetricDefinition], schema: Schema
    ) -> Route:
        """The Route a statement computing these Certified Metrics must carry.

        The metric's own `join_paths` and nothing else: the joins the **expression**
        needs to compute the number, so dropping one computes it over rows the
        conversion or the filter it names was supposed to narrow. `Traded Notional`
        without its hop through `dim_instrument` is not a cheaper Traded Notional, it is
        a different number.

        The union across metrics, which for the one-metric statement this project
        generates is one metric's route. It is a union rather than a per-metric
        comparison because a statement computing two metrics genuinely carries both
        routes, and asking each metric whether the whole statement matches its route
        alone would refuse every such statement on the strength of the joins the other
        one needed.

        **What the union cannot say is which metric took which join**, and that is
        [DEBT-021](../../.claude/docs/debt-ledger.md#debt-021--two-joins-to-one-table-under-different-aliases-are-not-told-apart).
        Two metrics converting through `fct_fx_rate` by different routes put two joins to
        that one table in the permitted set, `route_of_resolved` and `projections_of` both
        write columns on their base table before comparing, and so the two conversions can
        be swapped over with every rule here satisfied.
        """
        return self.assembled_route(metrics, (), schema, access=False)

    def permitted_route(
        self,
        metrics: Iterable[MetricDefinition],
        axes: Iterable[DimensionDefinition],
        schema: Schema,
    ) -> Route:
        """The most a statement computing these metrics and slicing by these axes may
        carry.

        `required_route`'s joins, plus the `routes` each axis declares from each
        metric's `from_table`, plus the route the Access Profile's predicate needs. The
        third is not conditional on anything: every statement must be scoped, so every
        statement is permitted the joins that scope it, and the rule that notices a
        statement did not use them is the access rule rather than this one.

        Reachability has already been established by the caller — an axis with no route
        from a metric's `from_table` is `UNREACHABLE_AXIS`, refused by name — so a
        missing key here is the access axis's own, which
        `check_semantic_layer.py`'s check 19 and the reach reading beside it are what
        keep from happening quietly.
        """
        return self.assembled_route(metrics, axes, schema, access=True)

    def assembled_route(
        self,
        metrics: Iterable[MetricDefinition],
        axes: Iterable[DimensionDefinition],
        schema: Schema,
        access: bool,
    ) -> Route:
        """One Route built from the corpus, read the way a statement's is.

        The shared half of `required_route` and `permitted_route`, and the reason there
        is one: both build a Route by assembling the metric's own statement and reading
        it with `route_of`, and the only difference is how long the join list is. Two
        copies of that assembly would be two chances to canonicalise a join condition
        differently, which is precisely what `certified_route` exists to prevent one
        level down.

        **The joins are named once and kept in order.** An axis's route starts at the
        metric's `from_table`, so appending it after the metric's own joins produces a
        statement whose every hop extends a route already arrived at its start; and a
        Join Path already named — `trade_to_instrument`, which `Traded Notional`
        computes across and `by instrument type` is reached by — is not appended twice,
        because joining one table twice under one name makes every column that names it
        ambiguous.
        """
        wanted = list(axes)
        if access:
            wanted.append(self.semantic.dimensions[ACCESS_AXIS])

        declared = []
        for metric in metrics:
            names = list(metric.join_paths)
            for axis in wanted:
                for name in axis.routes.get(metric.from_table, ()):
                    if name not in names:
                        names.append(name)
            declared.append(
                certified_route(
                    metric.expression,
                    metric.from_table,
                    [
                        (
                            self.semantic.join_paths[path].to_table,
                            self.semantic.join_paths[path].on,
                        )
                        for path in names
                    ],
                    schema,
                )
            )
        return Route(
            frozenset().union(*(route.from_tables for route in declared)),
            frozenset().union(*(route.joins for route in declared)),
        )

    def scoped(
        self, reading: Reading, access_profile: AccessProfile
    ) -> Rejected | None:
        """The statement is scoped to the Access Profile's permitted region, or reject.

        The [Target State](../../.claude/docs/design/target-state.md#flow)'s third
        parse-tree check, in its own words: *"Access Profile predicate present"*. The
        last rule the Gate runs and the last one this Step builds.

        **Present on every statement, not absent from the ones that ask for another
        region.** A statement over `fct_trade` that never joins `dim_client` reads every
        region's rows and names none of them, so a rule that refused only the statements
        naming a forbidden region would permit the leak by omission. That is why this
        rule needs no metric, no route and no projection: it asks one question of the
        outermost WHERE clause, and the answer is the same for every statement Veritas
        will ever run.

        **What it makes true, and what it costs**, are the same sentence: after this
        rule, a Veritas statement is a scoped statement. Every probe written for the
        four earlier rules was written before it existed and carries no predicate, so
        each of them is now refused **here** rather than allowed — which is the Gate
        getting stricter rather than any of those verdicts having been wrong, and is
        read off `ValidationGateOutcome.rules` by every module of
        `check_validation_gate`.

        **What this enforcement is and is not** is
        [DEBT-008](../../.claude/docs/debt-ledger.md#debt-008--the-access-control-story-promises-more-than-it-delivers)'s
        sentence, quoted in this module's docstring rather than paraphrased here: the
        application layer, over synthetic data, demonstrating the mechanism.

        **An unreadable statement is a rejection here too**, and in the assembled Gate
        the branch is unreached for the reason the Restricted Column rule's is: three
        earlier rules refuse every statement that cannot be resolved. It is kept because
        *"nothing found"* and *"could not look"* are the two answers a rule must never
        confuse, and this is the rule where confusing them would mean running an
        unscoped query.
        """
        try:
            asserted = where_conjuncts(reading.resolved)
        except TracerRefused as refusal:
            return (RejectionReason.UNRESOLVABLE,), (
                f"the statement parses but what it asserts about its rows cannot be "
                f"read, so whether it is scoped to the Access Profile is unknown: "
                f"{refusal}"
            )
        predicate = access_predicate(access_profile, self.semantic)
        if predicate not in asserted:
            return (RejectionReason.MISSING_ACCESS_PREDICATE,), (
                f"the Access Profile {access_profile.role!r} may only see "
                f"{access_profile.permitted_region} and this statement does not say so "
                f"— its rows are narrowed by "
                f"{'; '.join(sorted(asserted)) or 'nothing at all'}, and every "
                f"statement Veritas runs carries {predicate}"
            )
        return None

    def rules(self, access_profile: AccessProfile) -> tuple[tuple[str, Rule], ...]:
        """The rules, in the order a statement meets them, under one identity.

        One list in one place, which is what lets the ordering argument in this
        module's docstring be something the code states rather than something the
        file happens to be. Each later Sub-step of Step 005 appends to it.

        **Every rule is a `Rule` — one `Reading` in, a verdict out — and the identity
        is bound in here rather than passed down the loop in `judge`.** The three
        module-level rules need nothing beyond the statement, and giving them a
        parameter they ignore would make that untrue on the page: a signature that
        takes an Access Profile is a rule a reader has to check does not consult one.
        `partial` puts the identity where it is actually read, and leaves `judge` with
        one shape to call.
        """
        return (
            ("parses", parses),
            ("one statement", one_statement),
            ("a read", a_read),
            ("bounded", self.bounded),
            ("traces", self.traces),
            (
                "no restricted column",
                partial(self.no_restricted_column, access_profile=access_profile),
            ),
            ("a certified route", self.routed),
            (
                "the access predicate",
                partial(self.scoped, access_profile=access_profile),
            ),
        )

    def judge(self, sql: str, access_profile: AccessProfile) -> ValidationGateOutcome:
        """Allow or reject one statement, asked under one identity, and say under what.

        Stops at the first rule that rejects: a statement that does not parse has no
        tree for the next rule to read, and there is nothing to gain from asking a
        rule a question it cannot answer. The outcome names the rules that ran, so a
        reader never has to infer what a verdict covered.

        The Access Profile is required and has no default — see the class docstring for
        why it is here rather than on the Gate.

        **One `Reading` per judgement, and it is where the catalogue, the resolved tree
        and the corpus are read.** Every rule below gets the same one, so the four that
        read a parse tree read the *same* tree qualified against the *same* catalogue —
        [DEBT-019](../../.claude/docs/debt-ledger.md#debt-019--every-parse-tree-rule-reads-the-catalogue-and-resolves-the-statement-again),
        whose own argument for this was never speed: *"a verdict assembled from two views
        of the Warehouse is a verdict about neither."* Nothing is read here, only made
        reachable — see `Reading` for why that distinction is the Gate's rule order.

        **The identity is checked against the corpus before any rule runs**, and it
        raises rather than rejecting. A profile scoped to a region the `by region` axis
        does not certify is a broken installation and not a bad query — the call
        `certified_form` makes for a corpus that yields no metric expression — and
        catching it here is
        [R1](../../.claude/docs/plan/step-005-validation-gate.md#r1--the-access-profiles-predicate-and-the-slice-rule-ship-together-in-this-step--approved-and-widened-by-amino-2026-08-25)'s
        *"refused where it is loaded rather than where it is used"* as close as this
        design allows: a profile is a constant in `profile.py` and the corpus is not in
        scope there, so the first moment the two meet is a judgement, and a judgement
        under an uncertifiable identity ends before it reaches a rule rather than
        rejecting every statement with an explanation about the statement. It reads the
        corpus, which is loaded, and never the Warehouse, which is why the rules that
        need nothing still answer on a day the Warehouse will not open.
        """
        access_predicate(access_profile, self.semantic)
        reading = read(
            sql,
            catalogue=self.catalogue,
            certified_expressions={
                name: metric.expression
                for name, metric in self.semantic.metrics.items()
            },
        )
        ran: list[str] = []
        for name, rule in self.rules(access_profile):
            ran.append(name)
            rejected = rule(reading)
            if rejected is None:
                continue
            reasons, explanation = rejected
            return ValidationGateOutcome(
                allowed=False,
                explanation=explanation,
                reasons=reasons,
                rules=tuple(ran),
                trusted_rewrites=trusted_rewrite_names(),
            )
        return ValidationGateOutcome(
            allowed=True,
            explanation="",
            reasons=(),
            rules=tuple(ran),
            trusted_rewrites=trusted_rewrite_names(),
        )


def trusted_rewrite_names() -> tuple[str, ...]:
    """`TRUSTED_REWRITES` as the names a chart and a log line can carry.

    Taken off the callables rather than typed beside them, so C5's *"named in one
    place"* survives someone adding a third.
    """
    return tuple(rewrite.__name__ for rewrite in TRUSTED_REWRITES)
