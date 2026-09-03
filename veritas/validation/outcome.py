"""The Validation Gate outcome and the Rejection Reason taxonomy — the data
contract, before it is a return value.

Both names are Glossary terms as of 2026-08-25
([R3](../../.claude/docs/plan/step-005-validation-gate.md#r3--validation-gate-outcome-and-rejection-reason-get-glossary-rows--approved-by-amino-2026-08-25)),
and they are here rather than in `gate.py` because three components that will never
import a rule still have to read a verdict: a `Grounded Answer` carries one, the
`App` renders one, and `Observability` charts *"Validation-Gate rejections by
reason"*. A contract only its producer can import is not a contract.

**The taxonomy is registered in code and enumerated here.**
[ADR-0003](../../.claude/docs/adr/0003-validation-gate-is-deterministic-code.md)
sells determinism partly on that taxonomy existing — an LLM validator *"cannot
produce the stable taxonomy of rejection reasons that 'Validation-Gate rejections
by reason' needs to be a real chart"* — so the members are a closed set a chart can
group by, not strings each rule invents. R3 is also where this Step declined to put
the members in the Glossary cell instead, because a vocabulary inside one table cell
read by a prose parse is
[DEBT-017](../../.claude/docs/debt-ledger.md#debt-017--the-certified-axes-are-registered-inside-one-glossary-cell),
opened four days earlier and still open.

**The set is complete for the slice, and was built one rule at a time.** Sub-step 5.1
shipped the rules that need neither the corpus nor the schema and registered four
members; Sub-step 5.2 added the tracing rule and the three ways it can fail; Sub-step
5.3 added the Restricted Column rule and the one way it can; Sub-step 5.4 added the
certified-route rule and the two ways it can — a route the corpus does not name, and a
period filter on a date column the metric does not certify; and Sub-step 5.5 added
three, two of them to that same rule as it widened — an axis no route reaches from the
metric, a certified filter the statement dropped, and the Access Profile's own
predicate absent. Every member arrived with the rule that can produce it, because a
member with no rule behind it would be a chart category nothing can ever fall into.
The next member arrives with the next rule, and nothing in
[Step 005](../../.claude/docs/plan/step-005-validation-gate.md) is left to add one.

**A rule may register more than one member.** Four rules and four members made them
look paired; the tracing rule is one rule with three distinct failures behind it, and
they are separate members because they are separate bars a reader would act on
differently — a statement the optimizer cannot resolve, a Shadow Metric, and a
statement that aggregates nothing are three different things to go and fix. The
certified-route rule ended the Step with four of its own, which is the same test applied
four times: a route nothing certifies, a period on the wrong date column, an axis the
metric cannot reach, and a certified filter dropped are four different things to go and
fix, and one bar would hide which.
"""

from dataclasses import dataclass
from enum import StrEnum


class RejectionReason(StrEnum):
    """Why the Validation Gate refused a statement. One member per rule that can fire.

    A `StrEnum` so that a member survives the trip into a log line, a Postgres row
    and a Grafana filter as the word a person reads, while staying a member the Gate
    can enumerate. The value is the chart label; the name is the code identifier.
    """

    UNPARSEABLE = "unparseable"
    """sqlglot could not read the statement at all.

    [C6](../../.claude/docs/design/validation-feasibility.md#c6--fail-closed-on-parse-failure-by-a-rule-rather-than-by-accident)
    is the constraint that requires this to be its own reason rather than a
    consequence of finding nothing in an empty tree. The spike fails closed
    *"incidentally"*, and Sub-step 3.2's review measured one mutation that passes
    *"for a reason no probe here is written to measure"*. A Gate whose refusal of
    gibberish is a side effect is a Gate whose refusal of gibberish can be removed
    by an unrelated change and nothing will notice.
    """

    NOT_A_SINGLE_STATEMENT = "not a single statement"
    """The string holds more or fewer than one statement.

    Separate from `NOT_A_READ` because the danger is different in kind. Every
    statement in `SELECT 1; DROP TABLE fct_trade;` reads fine on its own and the
    string is a write; worse, the engine executes the tail of such a string even
    when the head is wrapped in `EXPLAIN`, which is why this rule is ordered ahead
    of any rule that asks the engine anything. `WarehouseAdapter.estimated_scan_rows`
    carries the measurement.
    """

    NOT_A_READ = "not a read"
    """The one statement is something other than a `SELECT`.

    Covers a write to the Warehouse, a write to the filesystem, engine
    introspection, and attaching a second database — the shapes
    [Sub-step 5.1](../../.claude/docs/plan/step-005-validation-gate.md#the-six-shapes-read-only-has-to-cover)
    enumerates. They share a reason because they share a rule: the Gate does not ask
    what a statement would do, it asks whether it is the one kind of statement
    Veritas runs. What it *was* goes in the outcome's explanation, so a chart can
    group by the rule and a reader can still see the verb.
    """

    UNBOUNDED_SCAN = "unbounded scan"
    """The planner expects the statement to read more rows than the ceiling allows.

    The `Validation Gate`'s registered definition ends with *"cost bounded,
    read-only"*, and the [Target State](../../.claude/docs/design/target-state.md#flow)
    spells the first of those *"scan bounded"*.
    """

    UNRESOLVABLE = "unresolvable"
    """The statement parses, but cannot be resolved against the live schema.

    A different mechanism from every reason above it and from the two below, and the
    spike is where the distinction was found: its `unknown table` probe is there
    because *"sqlglot resolves it without objecting, so the rejection has to come
    from the expression not matching rather than from resolution failing — two
    mechanisms a Gate must not confuse."* Resolution is what attaches every column to
    the table it came from and expands a `SELECT *` into real columns, so a statement
    that will not resolve is one no parse-tree rule can reach a verdict about. It is
    refused rather than passed, which is
    [ADR-0003](../../.claude/docs/adr/0003-validation-gate-is-deterministic-code.md)'s
    fail-closed commitment applied to the second way a statement can be unreadable.

    It is reachable rather than theoretical: the engine plans some statements
    sqlglot's optimizer will not resolve, and `check_validation_gate/traces.py` puts
    one in front of the Gate on every run.
    """

    SHADOW_METRIC = "shadow metric"
    """The statement computes an expression that is not a Certified Metric.

    The Glossary's own words for the thing: *"a metric computed inline in a query
    instead of drawn from the Semantic Layer. The failure mode Veritas exists to
    prevent."* The rule is the
    [Target State](../../.claude/docs/design/target-state.md#flow)'s, verbatim —
    *"every metric expression traces to a Certified Metric"* — and **every** is what
    this member reports failing: one uncertified expression beside three certified
    ones is still a rejection.

    A paraphrase that returns the identical number lands here too, by design.
    [C1](../../.claude/docs/design/validation-feasibility.md#c1--a-metric-definition-publishes-a-form-the-orchestrator-pastes)
    chose a pasteable form over a normalising comparison precisely so the Gate does
    not have to decide which rewrites preserve meaning, and the price of that choice
    is that a commuted operand is a Shadow Metric.
    """

    NO_METRIC_EXPRESSION = "no metric expression"
    """The statement computes no metric expression at all.

    Separate from `SHADOW_METRIC` because the two are different failures with
    different fixes: one says the generator invented arithmetic, the other says it
    wrote a statement that aggregates nothing. Charting them as one bar would hide
    which.

    Without this member the tracing rule would pass a statement vacuously — *"every
    metric expression traces"* is trivially true of a statement holding none — and a
    vacuous pass is half of what the spike achieved by accident.
    """


    RESTRICTED_COLUMN = "restricted column"
    """A column the Access Profile forbids reaches the statement's answer.

    The [Target State](../../.claude/docs/design/target-state.md#flow)'s second check on the
    parse tree, and the half of
    [C3](../../.claude/docs/design/validation-feasibility.md#c3--the-two-parse-tree-rules-ship-together)
    that a Step shipping certified-metrics-only alone would have left out: *"a Step that
    builds certified-metrics-only alone and defers the Restricted Column check has not
    built half a Gate; it has built a Gate that passes the leak."*

    **One member for the rule, and the columns go in the explanation.** A chart grouping
    by reason answers *"how often does the generator try to project an identity"*, which
    is one bar however many columns one statement names; *which* column it was is what a
    person reading the rejection needs, so the rule names every column it found rather
    than the first.

    Separate from `SHADOW_METRIC` because the two are unrelated failures that can arrive
    together. A statement can compute a Certified Metric exactly and still put a Client's
    name beside it — the spike's `net revenue by client` is that statement, and it is why
    the two rules are two rules.
    """

    UNCERTIFIED_ROUTE = "uncertified route"
    """The statement reaches its rows through joins the Metric Definition does not name.

    [C2](../../.claude/docs/design/validation-feasibility.md#c2--a-metric-definition-carries-its-join-path-and-its-date-predicate)'s
    half of the Gate, and the reason it exists in one sentence: *"a certified expression
    pins down the arithmetic and not the rows it is computed over."* `Traded Notional`
    converted out of the Trade's Denomination Currency instead of the Instrument's
    Quotation Currency projects **identically** to the right one, so `SHADOW_METRIC`
    cannot fire on it and the number is wrong by a margin
    `check_validation_feasibility.py` prints on every run. That statement is
    [DEBT-014](../../.claude/docs/debt-ledger.md#debt-014--the-spike-allows-a-query-the-gate-must-reject),
    and this member is what pays it.

    **It fires in both directions, and both are the same failure.** A statement that
    carries a join no entry certifies is reaching rows the Metric Definition never
    promised — a cross product, or a hop to a table with an identity in it. A statement
    that *omits* one of the metric's own joins is computing the expression over rows the
    conversion or the filter it names was supposed to narrow. The explanation says which
    it was; the bar says the route was not the certified one.
    """

    UNCERTIFIED_DATE_COLUMN = "uncertified date column"
    """The statement's period filter keys on a date column the metric does not certify.

    The other half of C2 and of DEBT-014, which
    [R4 of Step 003](../../.claude/docs/design/validation-feasibility.md#r4--debt-014-is-amended-to-name-the-date-predicate--approved-by-amino-2026-08-20)
    settled as *"this entry's question, not a second one"*: Trade Date and Settlement
    Date are two columns on `fct_trade`, a projection cannot tell them apart, and they
    are a
    [Glossary Section C](../../.claude/docs/glossary.md#c-distinctions-we-must-not-blur)
    pair because choosing between them moves the number. A Metric Definition's
    `date_column` is what it is certified against; a WHERE clause that keys on any other
    date column is asking for a period the metric does not define.

    **Its own bar rather than `UNCERTIFIED_ROUTE`'s**, for the reason `SHADOW_METRIC`
    and `NO_METRIC_EXPRESSION` are two bars: a statement that joined the wrong way and
    one that filtered on the wrong date are different things to go and fix, and one bar
    would hide which. They are one **rule** because C2 and DEBT-014 treat them as one
    question — the rows the certified expression is computed over.
    """

    UNREACHABLE_AXIS = "unreachable axis"
    """The statement slices a metric by a certified axis no route reaches from it.

    Sub-step 5.5's, and the one the `routes` field exists to make sayable. An axis
    declares the Join Paths that reach it from each fact table; an **absent key** says
    it cannot be reached from that one at all, and *"Cash Balance by instrument type"*
    is the case — a Cash Balance has no Instrument, so the honest refusal names the
    missing key rather than pointing at whichever two tables the generator joined
    trying to get there.

    **A different bar from `UNCERTIFIED_ROUTE`, because it is a different thing to go
    and fix.** An uncertified route says the statement's joins are wrong and the
    question is fine; this says the **question** cannot be asked of that metric, and no
    rewriting of the SQL will make it answerable. A reader acting on the first edits a
    query and a reader acting on the second asks a different one, which is exactly the
    distinction
    [ADR-0003](../../.claude/docs/adr/0003-validation-gate-is-deterministic-code.md)
    sold determinism on a stable taxonomy to preserve.

    It is also what makes
    [R11 of Step 004](../../.claude/docs/plan/step-004-semantic-layer.md#r11--aminos-rulings-on-the-45-review--decided-2026-08-25)'s
    fourth ruling enforceable rather than argued. That ruling defends three date axes
    where the Glossary had one, on the grounds that *"an axis named `fct_trade.trade_date`
    applied to a Snapshot metric is a certified axis whose route never reaches the
    column."* Under `routes` that sentence stops being an argument in a plan and becomes
    this member.
    """

    MISSING_CERTIFIED_FILTER = "missing certified filter"
    """The statement computes a metric without the certified predicate that defines it.

    [DEBT-020](../../.claude/docs/debt-ledger.md#debt-020--the-gate-checks-a-metrics-route-and-not-its-certified-filters)
    paid. A Metric Definition carries **three** fields that pin down which rows its
    expression is computed over — `join_paths`, `date_column` and `filters` — and
    Sub-step 5.4 read two of them. `Realised P&L` shares `fct_accounting_movement` with
    three other movement types and `filters` is the whole difference between them, so a
    statement that drops `movement_type = 'realised P&L'` computes the certified
    expression across the certified route over four movement types and calls the total
    Realised P&L.

    **Its own bar rather than `UNCERTIFIED_ROUTE`'s**, on the same test the two members
    above are separated by: a statement that joined the wrong way, one that filtered on
    the wrong date, and one that dropped a WHERE clause are three different things to go
    and fix, and a generator that forgets a filter is the most ordinary failure of the
    three. One **rule** with the other two, because C2 treats all of them as one
    question — the rows the certified expression is computed over.
    """

    MISSING_ACCESS_PREDICATE = "missing access predicate"
    """The statement is not scoped to the Access Profile's permitted region.

    The [Target State](../../.claude/docs/design/target-state.md#flow)'s third check on
    the parse tree, in its own words: *"Access Profile predicate present"*. Present, on
    every statement — not *"absent from statements that ask for another region"*. A
    statement over `fct_trade` that never joins `dim_client` reads every region's rows,
    and a rule that only refused the ones naming a region it may not see would be a rule
    that permits the leak by omission.

    So this is the member every question written before Sub-step 5.5 falls into, which
    is what makes it the widest change the Gate has made to what it allows: after 5.5, a
    statement is a Veritas statement when it is scoped, and the route that scopes it is
    the `by region` axis's own.

    Separate from `RESTRICTED_COLUMN` because the Glossary's Access Profile row names
    two powers and they fail differently: *"Determines which **rows** and **columns** the
    Validation Gate allows"*. A projected identity and an unscoped population are two
    bars a reader acts on differently, and
    [DEBT-008](../../.claude/docs/debt-ledger.md#debt-008--the-access-control-story-promises-more-than-it-delivers)
    is honest about what both are worth: application-layer enforcement over synthetic
    data, demonstrating the mechanism.
    """


@dataclass(frozen=True, slots=True)
class ValidationGateOutcome:
    """The verdict: allowed or rejected, why, and what it was decided under.

    Frozen, because it is evidence. Between the Gate returning one and Observability
    charting it there is an Orchestrator and a Grounded Answer, and a verdict any of
    them can edit is a verdict none of them can be held to.

    `reasons` is empty exactly when `allowed` is true. `explanation` is the sentence a
    person reads; `reasons` is what a chart groups by. Both, because the
    [Target State's flow](../../.claude/docs/design/target-state.md#flow) says
    *"fail → explain the violation"* and ADR-0003 says the taxonomy has to be stable,
    and neither one does the other's job.

    **A tuple, and so far every rule has put exactly one member in it.** Sub-step 5.1
    wrote the plural expecting the Restricted Column rule to contribute one member per
    column it found; Sub-step 5.3 built that rule and it contributes one member and
    names the columns in the `explanation` instead, because a chart grouping by reason
    is answering *"how often does the generator try to project an identity"* and that
    is one bar whether the statement named one column or three. The prediction is
    corrected here rather than deleted, since the shape it argued for is the shape
    that shipped. What keeps the tuple is not that prediction: `reasons` is the
    outcome's contract with three components that import no rule, and widening a
    single member into a tuple later is a change every reader of a verdict has to
    follow, where a tuple that has only ever held one member is not.

    `rules` names the rules that actually ran, in order, which is not the same as the
    rules that exist: the Gate stops at the first rule that rejects, so a statement
    refused as unparseable was never asked whether it was bounded. A reader who wants
    to know what a verdict covers reads this rather than assuming.

    `trusted_rewrites` is
    [C5](../../.claude/docs/design/validation-feasibility.md#c5--the-rewrites-the-gate-trusts-are-named-in-code-and-there-are-two)
    reported rather than declared. The rewrites themselves are `gate.TRUSTED_REWRITES`,
    where they are the callables a rule can actually run; what reaches a chart is their
    names, taken off those callables so there is no second list to drift. A verdict
    reached under a wider rule set is a different verdict, which is why it travels with
    the verdict instead of being looked up later.

    **`metrics`, `dimensions` and `join_paths` are what the statement was composed
    from** — the Certified Metrics its expressions traced to, the certified axes it
    sliced by, and the Join Paths its route was certified by. They are
    [DEBT-034](../../.claude/docs/debt-ledger.md#debt-034--lineage-records-what-the-model-was-shown-not-what-the-statement-used)
    paid: `Lineage` is read off the verdict rather than off what the model was shown, so
    an answer cites the entries that produced it and *"metric-usage frequency"* counts
    the metrics that were computed. The Gate's rules already decide all three on the way
    to a verdict; carrying them is the difference between a verdict and an audit trail.

    **Names, not entries.** A name survives into a Postgres row and a Grafana filter,
    where an entry would drag the Semantic Layer into a contract three components import
    without importing a rule. The Semantic Layer is what turns a name back into the entry
    and the version it was read at.

    **A rejected statement composed nothing**, and the check below holds it to that. Its
    metrics were *attempted*, not used — nothing ran — and a usage chart that counted
    them would report the corpus's failures as its traffic, which is the direction
    DEBT-034 says a wrong Lineage flatters the corpus in.
    """

    allowed: bool
    explanation: str = ""
    reasons: tuple[RejectionReason, ...] = ()
    rules: tuple[str, ...] = ()
    trusted_rewrites: tuple[str, ...] = ()
    metrics: tuple[str, ...] = ()
    dimensions: tuple[str, ...] = ()
    join_paths: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.allowed and self.reasons:
            raise ValueError(
                f"an allowed outcome carries no Rejection Reason, and this one "
                f"carries {list(self.reasons)}"
            )
        if not self.allowed and not self.reasons:
            raise ValueError(
                "a rejected outcome names at least one Rejection Reason, because "
                "'rejections by reason' is a chart and an unlabelled rejection is a "
                "bar with no name"
            )
        composed = [*self.metrics, *self.dimensions, *self.join_paths]
        if not self.allowed and composed:
            raise ValueError(
                f"a rejected statement composed nothing and this one names "
                f"{composed} — a refused statement's entries were attempted, not "
                f"used, and Lineage records what produced an answer"
            )
