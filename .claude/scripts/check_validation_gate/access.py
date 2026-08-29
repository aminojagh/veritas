"""Sub-step 5.5's rule: the Access Profile's predicate is present, on every statement.

The fifth and last of the modules
[R8](../../docs/plan/step-005-validation-gate.md#r8--the-steps-check-is-a-package-with-one-module-per-rule-from-51--approved-by-amino-2026-08-25)
lays out, and the one that closes the
[Target State's](../../docs/design/target-state.md#flow) list of what `VALIDATE`
decides. It measures three things the Sub-step built, in the order the plan's own
verification section puts them:

  * **the predicate binds on every metric** — each of the nine Certified Metrics,
    scoped and unscoped, which is eighteen probes and is how the rule is shown to bind
    on the Snapshot and movement metrics rather than only on the trade-side four;
  * **the slice route works and is bounded** — `Net Revenue by region` is allowed and
    executed, `Cash Balance by instrument type` is refused by the absent key, and a
    statement that joins a table it does not group by is refused because reaching an
    axis is permitted by grouping on it, not by mentioning its table;
  * **the mutations** — the rule deleted, the absent-key branch deleted, and the
    certified-filter comparison deleted, each re-run so that what the rule is worth is
    measured rather than asserted.

**What the access control is worth is printed as two numbers, not argued.** The
Glossary's own worked example — *"Net Revenue by region last quarter"* — is executed
twice: once as the corpus certifies the axis, which returns the three buckets the axis
registers, and once as the Access Profile permits, which returns one. The gap between
them is the access control doing something, and a run where they agreed would mean it
was not.

**One statement in three, and the axis has three buckets**, so a reader can see that
the analyst's slice is a third of a chart rather than a whole one. That is a property
of a slice with one Access Profile in it, not a defect: a second role permitting a
second region is a file edit rather than a field change, which the
[Step 005 plan](../../docs/plan/step-005-validation-gate.md#not-in-this-step) files as
a scope boundary.

**What this enforcement is and is not** is
[DEBT-008](../../docs/debt-ledger.md#debt-008--the-access-control-story-promises-more-than-it-delivers)'s
own sentence rather than a paraphrase of it: applied in the application layer, over
synthetic data, demonstrating the mechanism. Nothing here claims more, and this module
is not the entry's payment — its Trigger is the first access-control claim in
`README.md`, the App or a demo script, and none of the three exists.

**No probe here names a date at all**, which is how
[DEBT-012](../../docs/debt-ledger.md#debt-012--the-price-table-is-sparse-so-the-snapshot-calendar-has-holes)'s
third arm — *"the first 'as of' date chosen by anything but the Snapshot calendar"* —
stays unfired in this module: an access predicate narrows rows by region and a period
would be a second question. What is imported from `route.py` is the pair of readers that
say whether two figures are far enough apart to mean anything, so this module and that
one agree about what *"a different number"* is.
"""

from dataclasses import dataclass, replace
from decimal import Decimal

from probes import (
    ALLOWED,
    REJECTED,
    Probe,
    Report,
    certified_statement,
    judge_probes,
    problems,
    rule_named,
)
from route import MIN_GAP, gap, total

from veritas.semantic import JoinPath
from veritas.validation import (
    ACCESS_AXIS,
    ANALYST,
    AccessProfile,
    RejectionReason,
    ValidationGate,
    access_predicate,
    grouped_columns,
    resolve,
    where_conjuncts,
)
from veritas.warehouse import WarehouseAdapter

# The axis the second family of probes slices by, and the one it cannot: a Cash Balance
# has no Instrument, so `by instrument type` names two fact tables and not the other
# two. Named here rather than spelled into each probe because the probes are built from
# the corpus and this is which entry they are built from.
SLICE_AXIS = "by instrument type"


@dataclass(frozen=True, slots=True)
class AccessProbe(Probe):
    """A probe, plus what this rule's own reading of it should find.

    `scoped` is True when the Access Profile's predicate is one of the things the
    statement's outermost WHERE clause requires — this rule's own reading, declared
    separately from `verdict` for the reason `restricted.py`'s `reaches` and
    `route.py`'s `off_route` are: a statement an earlier rule refuses is still scoped or
    unscoped, and the reading that would have caught it should not go unmeasured because
    something else got there first.
    """

    scoped: bool = False


def written_predicate(gate: ValidationGate, access_profile: AccessProfile) -> str:
    """The access predicate as `certified_statement` writes it into a statement.

    Not `access_predicate`'s canonical form, which is what the **Gate** compares
    against: `"dim_client"."client_region" = 'EU'` is the same predicate written for a
    parse tree, and what has to be found and removed here is the text this package
    wrote. Both are built from the axis entry and the profile, so neither is a literal
    that can drift from the other.
    """
    axis = gate.semantic.dimensions[ACCESS_AXIS]
    return f"{axis.columns[0]} = '{access_profile.permitted_region}'"


def unscoped(sql: str, predicate: str) -> str:
    """One statement with the access predicate taken back out of it.

    The negative half of each of the nine pairs, and it is produced by **removing** the
    predicate from the scoped statement rather than by building a second statement
    without it. That is the whole design of the pair: two statements that differ in one
    conjunct and nothing else, so the verdict that separates them can only be about that
    conjunct. A pair assembled twice would differ wherever the two assemblies did.

    Three shapes, because the predicate is written last and what precedes it is not
    always the same: an `AND` where a certified filter comes first — `Realised P&L` is
    the one metric that has one — and the `WHERE` itself where nothing does, in which
    case the whole clause goes and any `GROUP BY` after it stays.
    """
    for written in (f" AND {predicate}", f"{predicate} AND ", f" WHERE {predicate}"):
        if written in sql:
            return sql.replace(written, "", 1)
    raise SystemExit(
        f"the statement below does not carry the predicate this module wrote into it, "
        f"so the unscoped half of its pair cannot be built by removing one conjunct — "
        f"which is the only thing that makes the pair a measurement\n"
        f"      predicate: {predicate}\n      statement: {sql}"
    )


def with_extra_join(sql: str, join: JoinPath, sliced_by: str = "") -> str:
    """One more join in a statement `certified_statement` built, and optionally a slice.

    The join goes **before** the WHERE clause because that is where a join goes, and
    `certified_statement` always writes a WHERE — every statement it builds carries the
    access predicate. Two probes need this and both are about the difference between
    joining a table and slicing by it, so both start from a statement that is otherwise
    exactly what the corpus certifies.
    """
    head, _, narrowed = sql.partition(" WHERE ")
    projection = f"{sliced_by} AS slice, " if sliced_by else ""
    group = f" GROUP BY {sliced_by}" if sliced_by else ""
    return (
        head.replace("SELECT ", f"SELECT {projection}", 1)
        + f" JOIN {join.to_table} ON {join.on} WHERE {narrowed}{group}"
    )


def predicate_probes(gate: ValidationGate) -> tuple[AccessProbe, ...]:
    """Eighteen probes: every Certified Metric, scoped and unscoped.

    Nine and not three, for the reason `traces.py` asks all nine: a Gate that enforces
    an identity on the trade-side metrics alone enforces it on four questions out of
    nine, which is the kind of partial control
    [DEBT-008](../../docs/debt-ledger.md#debt-008--the-access-control-story-promises-more-than-it-delivers)
    is already about. The four fact tables the nine metrics start from each need their
    own first hop to `dim_account`, which is why the Sub-step added five Join Paths and
    not the two
    [R11 of Step 004](../../docs/plan/step-004-semantic-layer.md#r11--aminos-rulings-on-the-45-review--decided-2026-08-25)
    counted.

    Both halves are built from the corpus, so a tenth Metric Definition is a tenth pair
    with no edit here.
    """
    predicate = written_predicate(gate, ANALYST)
    built: list[AccessProbe] = []
    for name in sorted(gate.semantic.metrics):
        scoped = certified_statement(gate, name, ANALYST)
        built.append(
            AccessProbe(
                name=f"{name}, scoped",
                sql=scoped,
                verdict=ALLOWED,
                scoped=True,
                why=f"{name} computed the way its own Metric Definition says, reached "
                    f"through the `{ACCESS_AXIS}` route and narrowed to the region the "
                    f"Access Profile permits. It has to be allowed, or this rule is "
                    f"refusing every question there is",
            )
        )
        built.append(
            AccessProbe(
                name=f"{name}, unscoped",
                sql=unscoped(scoped, predicate),
                verdict=REJECTED,
                reasons=(RejectionReason.MISSING_ACCESS_PREDICATE,),
                scoped=False,
                why=f"the same statement with one conjunct removed. Everything else "
                    f"about it is certified — the expression, the route, the period, "
                    f"the filters — and it reads every region's rows, which is the "
                    f"leak a rule that only refused statements *naming* a forbidden "
                    f"region would permit by omission",
            )
        )
    return tuple(built)


def slice_probes(gate: ValidationGate) -> tuple[AccessProbe, ...]:
    """The slice route: one axis reached, one axis not reachable, one join not earned.

    Three shapes and each says a different thing about the `routes` field:

      * `Net Revenue by region` is the Glossary's own worked example, and it was a
        certified axis no query could reach between Sub-steps 4.5 and 5.5. The route
        exists now and the rule that lets a `GROUP BY` use it exists now, which are the
        two halves R11 of Step 004 named — so the first of the three questions Step 004
        handed to the Grounding Step is answered rather than narrowed;
      * `Cash Balance by instrument type` is the absent key. A Cash Balance has no
        Instrument, and the refusal names the axis and the table rather than pointing
        at whichever two tables a generator joined trying to get there;
      * a statement that joins `dim_instrument` and groups by nothing has added a join
        for no certified reason. **Reaching an axis is permitted by grouping on it, not
        by mentioning its table**, and this is the probe that separates the two.

    The third is written against `Net Revenue` rather than `Traded Notional` because
    `Traded Notional` computes across `dim_instrument` already — the join would be its
    own certified route and the probe would measure nothing.
    """
    layer = gate.semantic
    net_revenue = certified_statement(gate, "Net Revenue", ANALYST)
    cash_balance = certified_statement(gate, "Cash Balance", ANALYST)
    instrument_type = layer.dimensions[SLICE_AXIS].columns[0]
    # The join `Cash Balance by instrument type` has to write, and there is no sensible
    # one: `fct_balance_snapshot` holds no Instrument, which is the whole reason the
    # axis names no route from it. An Account identifier equated with an Instrument's is
    # the nonsense a generator reaching for an unreachable axis would have to invent,
    # and the rule's job is to refuse the question before anyone reads the join.
    to_instrument = replace(
        layer.join_paths["trade_to_instrument"],
        on="dim_instrument.instrument_id = fct_balance_snapshot.account_id",
    )
    return (
        AccessProbe(
            name="net revenue by region",
            sql=certified_statement(gate, "Net Revenue", ANALYST, sliced_by=ACCESS_AXIS),
            verdict=ALLOWED,
            scoped=True,
            why="the Glossary's worked example, executed rather than argued. The two "
                "hops that reach `dim_client` are certified by the `by region` axis's "
                "own `routes`, and the `GROUP BY` is what earns them — "
                "`check_the_slice_is_worth_having` prints what it returns",
        ),
        AccessProbe(
            name="cash balance by instrument type",
            sql=with_extra_join(cash_balance, to_instrument, instrument_type),
            verdict=REJECTED,
            reasons=(RejectionReason.UNREACHABLE_AXIS,),
            scoped=True,
            why=f"the absent key. `{SLICE_AXIS}` names `fct_trade` and "
                f"`fct_position_snapshot` and nothing else, and `Cash Balance` starts "
                f"at `fct_balance_snapshot` — so the axis is not reachable from it, and "
                f"the Gate names the axis and the table rather than refusing the join "
                f"a generator invented trying to get there",
        ),
        AccessProbe(
            name="a join to a table nothing groups by",
            sql=with_extra_join(net_revenue, layer.join_paths["trade_to_instrument"]),
            verdict=REJECTED,
            reasons=(RejectionReason.UNCERTIFIED_ROUTE,),
            scoped=True,
            why="`Net Revenue` scoped exactly as the first probe, with one extra join "
                "to a table it never groups by. `by instrument type` *does* declare a "
                "route from `fct_trade`, and that route is permission a `GROUP BY` "
                "earns — so the join is refused as one no entry names *for this "
                "statement*, which is the difference between a Gate and a query planner",
        ),
    )


def shapes(gate: ValidationGate) -> tuple[AccessProbe, ...]:
    """Every shape this module puts in front of the Gate, in the order it reports them.

    One tuple so that no check below can read a different set from the one
    `judge_probes` declared verdicts for — `route.py`'s arrangement, for its reason.
    """
    return slice_probes(gate) + predicate_probes(gate)


def check_the_slice_is_worth_having(gate: ValidationGate, report: Report) -> None:
    """Execute the Glossary's worked example twice and print what the scoping costs.

    Once as the **corpus** certifies the axis — three buckets, which is what
    `allowed_values` registers — and once as the **Access Profile** permits, which is
    one. Both are executed here rather than judged, because the Gate never executes
    anything: `VALIDATE` is step 5 of the flow and `EXECUTE` is step 6.

    This is the method `route.py`'s `check_the_numbers_differ` uses and the same reason
    for it: a rule is only worth having if the thing it refuses returns a different
    answer. Here the rule is the access predicate and the difference is the rows a
    Client outside the permitted region contributes, so a run where the scoped total
    matched the unscoped one would mean this profile restricts nothing on this data.
    """
    axis = gate.semantic.dimensions[ACCESS_AXIS]
    scoped = certified_statement(gate, "Net Revenue", ANALYST, sliced_by=ACCESS_AXIS)
    every_region = unscoped(scoped, f"{axis.columns[0]} = '{ANALYST.permitted_region}'")

    buckets = gate.warehouse.query(every_region)
    permitted = gate.warehouse.query(scoped)
    report.say(
        f"Net Revenue by region: the axis registers "
        f"{len(axis.allowed_values)} bucket(s) and the query returns "
        f"{len(buckets)}; the Access Profile {ANALYST.role!r} sees "
        f"{len(permitted)} — "
        + " · ".join(f"{row[0]} {Decimal(str(row[1])):.2f}" for row in buckets)
    )
    if len(buckets) != len(axis.allowed_values):
        problems.append(
            f"the `{ACCESS_AXIS}` axis registers {list(axis.allowed_values)} and the "
            f"unscoped slice returns {len(buckets)} bucket(s) — the axis and the "
            f"Warehouse have come apart, and `check_semantic_layer.py`'s check 16 is "
            f"where that is supposed to be caught"
        )
    if len(permitted) >= len(buckets):
        problems.append(
            f"the Access Profile {ANALYST.role!r} sees {len(permitted)} of "
            f"{len(buckets)} region(s), so the predicate this rule requires is not "
            f"narrowing anything and the run cannot show the access control does "
            f"something"
        )

    whole = total(gate.warehouse.query(unscoped(
        certified_statement(gate, "Net Revenue", ANALYST),
        f"{axis.columns[0]} = '{ANALYST.permitted_region}'",
    )))
    mine = total(gate.warehouse.query(certified_statement(gate, "Net Revenue", ANALYST)))
    difference = gap(whole, mine)
    report.say(
        f"Net Revenue: {whole:.2f} over every region · {mine:.2f} over "
        f"{ANALYST.permitted_region} — {difference:.2f}% apart, and the Gate allows "
        f"only the second"
    )
    if difference < MIN_GAP:
        problems.append(
            f"Net Revenue is the same number scoped and unscoped ({difference:.6f}% "
            f"apart), so the Access Profile's predicate costs a user a query and buys "
            f"them nothing on this data"
        )


def check_this_rules_reading(gate: ValidationGate, report: Report) -> None:
    """Read every probe the way this rule reads it, beside what was declared.

    `judge_probes` reports what a caller gets. This reports what **this rule** reads —
    which conjuncts the statement narrows its rows by, and whether the Access Profile's
    predicate is one of them — on every shape, including ones an earlier rule refuses.

    It also prints what the route rule read about the slice, because the two are one
    Sub-step: an axis a statement groups by is where the joins that reach it come from,
    and a table joined without being grouped by is where they do not.
    """
    schema = gate.warehouse.columns_by_table()
    predicate = access_predicate(ANALYST, gate.semantic)
    report.say(f"{'scoped':<10}{'shape':<40}sliced by · narrowed by")
    for probe in shapes(gate):
        resolved = resolve(probe.sql, schema)
        asserted = where_conjuncts(resolved)
        axes = gate.axes_sliced_by(grouped_columns(resolved))
        scoped = predicate in asserted
        report.say(
            f"{'YES' if scoped else 'no':<10}{probe.name:<40}"
            f"{', '.join(axis.name for axis in axes) or 'nothing'} · "
            f"{len(asserted)} conjunct(s)"
        )
        if probe.scoped != scoped:
            problems.append(
                f"{probe.name!r} was measured as "
                f"{'scoped' if probe.scoped else 'unscoped'} and reads as "
                f"{'scoped' if scoped else 'unscoped'}. {probe.why}"
            )


def check_a_profile_the_axis_cannot_certify(gate: ValidationGate, report: Report) -> None:
    """A region the `by region` axis does not register is refused before any rule runs.

    [R1](../../docs/plan/step-005-validation-gate.md#r1--the-access-profiles-predicate-and-the-slice-rule-ship-together-in-this-step--approved-and-widened-by-amino-2026-08-25)
    asks for a profile naming an uncertified region to be *"refused where it is loaded
    rather than where it is used"*. A profile is a constant in `veritas/validation/`
    and the corpus is not in scope there, so the first moment the two meet is a
    judgement — and `judge` asks for the predicate before it runs a rule, so what a
    caller gets is a `ValueError` naming the profile rather than a rejection that talks
    about the statement.

    Two probes, and the second is the one that would otherwise be missed: a region the
    axis does not certify, and a role whose axis is not in the corpus at all.
    """
    for description, profile, layer in (
        (
            "a region the axis does not certify",
            replace(ANALYST, permitted_region="LATAM"),
            gate.semantic,
        ),
        (
            "an axis the corpus does not publish",
            ANALYST,
            replace(
                gate.semantic,
                dimensions={
                    name: axis
                    for name, axis in gate.semantic.dimensions.items()
                    if name != ACCESS_AXIS
                },
            ),
        ),
    ):
        try:
            access_predicate(profile, layer)
        except ValueError as refusal:
            report.say(f"refuses  {description} — {refusal}")
            continue
        problems.append(
            f"an Access Profile with {description} was turned into a predicate rather "
            f"than refused, so the Gate would scope every statement on something the "
            f"corpus does not certify"
        )


def check_the_mutations(gate: ValidationGate, rule: str, report: Report) -> None:
    """Delete each half of what this Sub-step built and watch what stops being refused.

    Three mutations, and none of them edits a file: each is a Gate assembled without one
    of the three things 5.5 added, so what is measured is the rule and not a comment
    about it.

      * **the access-predicate rule removed** — the nine unscoped probes stop being
        refused, which is the number the rule is worth;
      * **the unreachable-axis branch removed** — `Cash Balance by instrument type` is
        judged on its joins instead of on the absent key, and the reason a reader is
        given stops naming the axis. The Gate still refuses it, on the nonsense join,
        which is exactly why the branch exists: the refusal a rule gives is half of what
        it is for;
      * **the certified-filter comparison removed** —
        [DEBT-020](../../docs/debt-ledger.md#debt-020--the-gate-checks-a-metrics-route-and-not-its-certified-filters)'s
        statement goes back to being allowed, which is what proves the payment is a rule
        and not a renamed probe.

    A mutation is a subclass overriding one method, because `ValidationGate` is frozen
    and a check that mutated the thing under test would be measuring something else.
    """
    class NoAccessRule(ValidationGate):
        def rules(self, access_profile: AccessProfile):
            return tuple(
                entry for entry in super().rules(access_profile) if entry[0] != rule
            )

    class NoAbsentKey(ValidationGate):
        def unreachable_axis(self, metrics, axes):
            return None

    class NoFilterComparison(ValidationGate):
        def certified_filters(self, metrics) -> set[str]:
            return set()

    unscoped_probes = [
        probe for probe in predicate_probes(gate) if probe.verdict == REJECTED
    ]
    without_rule = NoAccessRule(gate.warehouse, semantic=gate.semantic)
    still_refused = [
        probe.name
        for probe in unscoped_probes
        if not without_rule.judge(probe.sql, ANALYST).allowed
    ]
    report.say(
        f"delete the {rule!r} rule: {len(unscoped_probes) - len(still_refused)} of "
        f"{len(unscoped_probes)} unscoped statements are allowed to run"
    )
    if still_refused:
        problems.append(
            f"{len(still_refused)} unscoped statement(s) are refused by a Gate with no "
            f"access-predicate rule in it — {', '.join(still_refused)}. Something other "
            f"than this rule is refusing them, so the probes above are measuring that "
            f"other thing"
        )

    absent_key = next(
        probe for probe in slice_probes(gate)
        if probe.reasons == (RejectionReason.UNREACHABLE_AXIS,)
    )
    without_branch = NoAbsentKey(gate.warehouse, semantic=gate.semantic).judge(
        absent_key.sql, ANALYST
    )
    report.say(
        f"delete the absent-key branch: {absent_key.name!r} is refused as "
        f"{', '.join(reason.value for reason in without_branch.reasons) or 'nothing'} "
        f"instead of {absent_key.reasons[0].value!r}"
    )
    if RejectionReason.UNREACHABLE_AXIS in without_branch.reasons:
        problems.append(
            f"{absent_key.name!r} is still refused for an unreachable axis by a Gate "
            f"that does not read the axis, so the branch above is not what refuses it"
        )

    dropped = certified_statement(gate, "Realised P&L", ANALYST, with_filters=False)
    kept = gate.judge(dropped, ANALYST)
    lost = NoFilterComparison(gate.warehouse, semantic=gate.semantic).judge(
        dropped, ANALYST
    )
    report.say(
        f"delete the certified-filter comparison: `Realised P&L` with its filter "
        f"dropped goes from "
        f"{', '.join(reason.value for reason in kept.reasons) or 'allowed'} to "
        f"{', '.join(reason.value for reason in lost.reasons) or 'allowed'} (DEBT-020)"
    )
    if kept.allowed or not lost.allowed:
        problems.append(
            "the certified-filter comparison does not decide `Realised P&L with its "
            "filter dropped` on its own — DEBT-020's payment is only a payment while "
            "removing the comparison puts the statement back"
        )


def check_this_rule_ran(gate: ValidationGate, rule: str, report: Report) -> None:
    """Which of the shapes above this rule decided, and which an earlier rule did.

    The last rule in the list, so *"never reached it"* means an earlier rule refused the
    statement and this module is measuring that rule instead. Three of the shapes are
    exactly that on purpose — the slice probes are refused by the route rule one place
    earlier — so they are counted and named rather than treated as failures.
    """
    judged = shapes(gate)
    decided = earlier = 0
    for probe in judged:
        outcome = gate.judge(probe.sql, ANALYST)
        if rule not in outcome.rules:
            earlier += 1
            continue
        decided += not outcome.allowed and outcome.rules[-1] == rule
    report.say(
        f"this rule ran on {len(judged) - earlier} of the {len(judged)} shapes above "
        f"and reached the verdict on {decided} of them; {earlier} were refused before "
        f"it"
    )
    if not decided:
        problems.append(
            "this rule reached no verdict on any shape here, so nothing above is "
            "measuring it"
        )


def check(warehouse: WarehouseAdapter) -> Report:
    """Everything this module has to say, in one report."""
    report = Report("the Access Profile's predicate, on every statement")
    gate = ValidationGate(warehouse)
    rule = rule_named(gate, ValidationGate.scoped, ANALYST)
    if not rule:
        problems.append(
            "the Gate's rule list holds no entry for `scoped`, so nothing below is "
            "judging the rule this module exists to check"
        )
    report.say(
        f"Access Profile: role {ANALYST.role!r}, permitted region "
        f"{ANALYST.permitted_region!r} of the {ACCESS_AXIS!r} axis; the predicate is "
        f"{access_predicate(ANALYST, gate.semantic)}"
    )
    check_the_slice_is_worth_having(gate, report)
    check_a_profile_the_axis_cannot_certify(gate, report)
    report.say("")
    judge_probes(gate, shapes(gate), report, ANALYST)
    report.say("")
    check_this_rules_reading(gate, report)
    report.say("")
    check_the_mutations(gate, rule, report)
    check_this_rule_ran(gate, rule, report)
    return report
