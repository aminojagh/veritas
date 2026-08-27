"""The Validation Gate — the deterministic checks a generated query passes before it
executes.

[ADR-0003](../../.claude/docs/adr/0003-validation-gate-is-deterministic-code.md)
decided what this is: code over a parse tree, and *"no LLM participates in the
decision to allow or reject a query."*
[Step 003](../../.claude/docs/design/validation-feasibility.md) spent five Sub-steps
measuring whether that is possible on this schema and this data, and returned **GO**.
This module is the thing that was measured for.

**Five rules, and two Sub-steps have shipped.** The
[Target State's flow](../../.claude/docs/design/target-state.md#flow) names what
`VALIDATE` decides; the [Step 005 plan](../../.claude/docs/plan/step-005-validation-gate.md#what-the-gate-must-decide)
puts them in the order a statement meets them. Sub-step 5.1 shipped everything that
needs neither the Semantic Layer nor a certified metric — can this be read at all, is
it one statement, is it a read, will it stay inside the scan ceiling — and Sub-step
5.2 added the first rule that reads the corpus: does every metric expression trace to
a Certified Metric. The Restricted Column, certified-route and Access Profile rules
are still to come.

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
    the parse tree alone, and a Gate that loaded twenty-seven Semantic Entries before
    refusing it would have made a rule that needs nothing depend on something that
    can fail underneath it.

**The Gate stops at the first rule that rejects.** A statement that does not parse
has no tree for a later rule to read, and a rejected outcome names the rules that
actually ran, so nothing has to be inferred from a verdict's silence.

**The Gate never executes the statement it judges** — not even to size it.
`VALIDATE` is step 5 of the flow and `EXECUTE` is step 6, and a Gate that runs the
query it just approved is a Gate with no boundary.
"""

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field

import sqlglot
from sqlglot import exp
from sqlglot.optimizer import optimize
from sqlglot.optimizer.merge_subqueries import merge_subqueries
from sqlglot.optimizer.qualify import qualify
from sqlglot.optimizer.scope import build_scope

from veritas.semantic import SemanticLayer, load_semantic_layer
from veritas.validation.outcome import RejectionReason, ValidationGateOutcome
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


@dataclass(frozen=True, slots=True)
class Reading:
    """What the Gate has read off a statement, before any rule has judged it.

    Parsing happens once, here, rather than inside each rule: five rules that each
    call `sqlglot.parse` are five chances to parse with different settings, and the
    settings are the whole of what a parse tree means.

    `statements` is `None` exactly when sqlglot refused the string, and `refusal`
    carries what it said. That is
    [C6](../../.claude/docs/design/validation-feasibility.md#c6--fail-closed-on-parse-failure-by-a-rule-rather-than-by-accident)'s
    requirement made structural: a rule reads *"the parse failed"* as a fact it was
    handed, not as an empty list it has to interpret.
    """

    sql: str
    statements: tuple[exp.Expression, ...] | None = None
    refusal: str = ""

    @property
    def statement(self) -> exp.Expression:
        """The one statement, for the rules that run after the count has been checked."""
        assert self.statements is not None and len(self.statements) == 1
        return self.statements[0]


def read(sql: str) -> Reading:
    """Parse the statement, or record that it could not be parsed.

    `sqlglot.parse` rather than `parse_one`, and the difference is a rule: given
    `SELECT 1; SELECT 2` this version returns two statements where `parse_one`
    returns a single `Block` node that reads like one statement and is not one.
    A Gate built on `parse_one` would have to notice `Block` by name to refuse a
    multi-statement string, which is one library release away from silence.

    Empty segments come back as `None` — `sqlglot.parse("SELECT 1;;")` is a
    statement and a nothing — and are dropped, so a trailing semicolon is not a
    second statement and an empty string is no statements at all.
    """
    try:
        parsed = sqlglot.parse(sql, dialect=DIALECT)
    except sqlglot.errors.SqlglotError as refusal:
        return Reading(sql=sql, statements=None, refusal=str(refusal))
    return Reading(sql=sql, statements=tuple(s for s in parsed if s is not None))


# A rule returns the Rejection Reasons that fired and the sentence explaining them,
# or None when the statement passed it. Reasons rather than one reason because a
# single rule may find several things wrong at once — Sub-step 5.3's Restricted
# Column rule names every column it found rather than the first.
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
    except sqlglot.errors.SqlglotError as failure:
        raise TracerRefused(f"{type(failure).__name__}: {failure}") from failure


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
    resolved = resolve(statement, schema, dialect)

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
        # The lookup: alias -> the base table it stands for. A source that is another
        # Scope is a subquery `merge_subqueries` could not flatten, and is left out
        # of this map because its projections are read on its own turn.
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
    return [
        canonical(expression, dialect)
        for expression in projected_expressions(statement, schema, dialect)
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
        """
        schema = self.warehouse.columns_by_table()
        try:
            expressions = metric_expressions(reading.statement, schema)
        except TracerRefused as refusal:
            return (RejectionReason.UNRESOLVABLE,), (
                f"the statement parses but will not resolve against the Warehouse's "
                f"columns, so no expression in it can be traced: {refusal}"
            )

        corpus = certified_forms(
            {name: metric.expression for name, metric in self.semantic.metrics.items()},
            schema,
        )
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

    def rules(self) -> tuple[tuple[str, Rule], ...]:
        """The rules, in the order a statement meets them.

        One list in one place, which is what lets the ordering argument in this
        module's docstring be something the code states rather than something the
        file happens to be. Each later Sub-step of Step 005 appends to it.
        """
        return (
            ("parses", parses),
            ("one statement", one_statement),
            ("a read", a_read),
            ("bounded", self.bounded),
            ("traces", self.traces),
        )

    def judge(self, sql: str) -> ValidationGateOutcome:
        """Allow or reject one statement, and say under what.

        Stops at the first rule that rejects: a statement that does not parse has no
        tree for the next rule to read, and there is nothing to gain from asking a
        rule a question it cannot answer. The outcome names the rules that ran, so a
        reader never has to infer what a verdict covered.
        """
        reading = read(sql)
        ran: list[str] = []
        for name, rule in self.rules():
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
