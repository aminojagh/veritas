"""Sub-step 5.3's rule: no Restricted Column reaches the answer, under an Access Profile.

The third of the five modules
[R8](../../docs/plan/step-005-validation-gate.md#r8--the-steps-check-is-a-package-with-one-module-per-rule-from-51--approved-by-amino-2026-08-25)
lays out, and the first that judges a statement against an identity. It puts ten shapes
in front of the Gate and reads each of them **three** ways:

  * **the Gate's verdict**, which is what a caller acts on;
  * **the parse tree's answer** — which Restricted Columns reach the statement's
    answer — which is the rule's own reading, visible even on the shapes the Gate
    refuses one rule earlier;
  * **the text's answer** — the restricted name searched for in the query string, which
    is the alternative
    [ADR-0003](../../docs/adr/0003-validation-gate-is-deterministic-code.md) rejected.

Reading all three is the point. A shape the parse tree and the text agree on measures
nothing; the run prints the pair for every shape and fails if **either** column moves,
so the rejected alternative goes on being shown wrong on every run rather than in an
argument.

**Six shapes carry a Restricted Column into the answer and four do not**, and the four
that do not matter as much as the six that do. A Gate that refuses every query mentioning
a restricted name in a comment, or every query that counts distinct Clients, is a Gate
people route around — and a Gate people route around protects nothing. Three of those
four are this module's positive controls: statements this rule ran on and passed on. The
fourth, `projected inside, aggregated away`, this rule allows and an earlier one
refuses — counting Clients is not a Certified Metric — and two rules disagreeing about
one statement is the clearest evidence they are asking different questions.

**Since Sub-step 5.4 the Gate's verdict and this rule's verdict come apart on two of
those three**, and that is why the first bullet above is not the last word on any of
them. `the name in a comment` and `the name in a filter only` reach `dim_client` through
two joins no Semantic Entry certifies, so the certified-route rule two places later
refuses what this rule passed. Their declared verdict is `rejected` and their declared
`reaches` is False, and both are checked — `check_this_rules_verdicts` reads
`ValidationGateOutcome.rules` so that *"this rule refused it"* and *"the Gate refused
it"* stay two different statements. Sub-step 5.5 certifies those two joins and their
Gate verdict goes back to `allowed`.

**Nine of the ten statements are the spike's, character for character**, and
`probes.check_the_statements_are_the_spikes` reads them out of
`check_validation_feasibility.py`'s **source text** on every run rather than leaving
that claim to a comment — and without importing it, which is
[R14](../../docs/plan/step-005-validation-gate.md#r14--aminos-rulings-on-the-53-review--decided-2026-08-27).
The tenth is this Sub-step's, and it is here because the spike's star probe turns out
not to reach this rule inside the assembled Gate.
"""

from dataclasses import dataclass

from probes import (
    ALLOWED,
    REJECTED,
    Probe,
    Report,
    check_the_statements_are_the_spikes,
    judge_probes,
    problems,
    rule_verdicts,
)

from veritas.validation import (
    ANALYST,
    AccessProfile,
    RejectionReason,
    TracerRefused,
    ValidationGate,
    restricted_columns_in_projection,
)
from veritas.warehouse import WarehouseAdapter


@dataclass(frozen=True, slots=True)
class RestrictedProbe(Probe):
    """A probe, plus the two answers about it that are not the Gate's verdict.

    `reaches` is the parse tree's answer: True when a Restricted Column is among the
    columns this statement's answer carries, once `SELECT *` has been expanded against
    the real schema. It is what this rule acts on — and it is declared separately from
    `verdict` because the two come apart: three shapes here are refused by an earlier
    rule, and their leak would go unmeasured if the Gate's verdict were the only thing
    recorded.

    `found_by_text` is what ADR-0003's rejected alternative says. It is declared beside
    the parse tree's answer so that the rejection is a measurement: a shape where the two
    disagree is a shape text matching gets wrong, in one direction or the other.
    """

    reaches: bool = False
    found_by_text: bool = False


PROBES = (
    RestrictedProbe(
        name="net revenue by client",
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
        verdict=REJECTED,
        reasons=(RejectionReason.RESTRICTED_COLUMN,),
        reaches=True,
        found_by_text=True,
        why="the plain case: a Client's name beside the metric, which is what "
            "\"net revenue by client\" generates. Every rule before this one "
            "allows it — the expression is Net Revenue's certified one — so "
            "this is the probe that shows the tracing rule and this rule are "
            "two different questions about one statement",
    ),
    RestrictedProbe(
        name="star over a join to dim_client",
        sql="SELECT * "
            "FROM fct_trade AS billed "
            "JOIN dim_account AS account "
            "  ON account.account_id = billed.account_id "
            "JOIN dim_client AS client "
            "  ON client.client_id = account.client_id",
        verdict=REJECTED,
        reasons=(RejectionReason.NO_METRIC_EXPRESSION,),
        reaches=True,
        found_by_text=False,
        why="the restricted name appears nowhere in this query and the query "
            "projects it, which is the shape ADR-0003 named and the one text "
            "matching cannot see at all. **The Gate refuses it a rule "
            "earlier**: a star projection aggregates nothing, so the tracing "
            "rule reaches it first and the leak never gets to be this rule's "
            "verdict. The parse tree still finds the column — the table below "
            "is where that is measured — and `star beside a certified metric` "
            "is the same shape written so that it does reach this rule",
    ),
    RestrictedProbe(
        name="aliased to a benign name",
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
        verdict=REJECTED,
        reasons=(RejectionReason.RESTRICTED_COLUMN,),
        reaches=True,
        found_by_text=True,
        why="the same Client name, output as `name`. Nothing in the result "
            "set says which column it came from, so a Gate reading the "
            "answer's column headings sees a benign one — the parse tree is "
            "read before the alias rather than after it",
    ),
    RestrictedProbe(
        name="hidden behind a derived table",
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
        verdict=REJECTED,
        reasons=(RejectionReason.RESTRICTED_COLUMN,),
        reaches=True,
        found_by_text=True,
        why="the fourth defeat ADR-0003's quote names — a subquery — with the "
            "Client name renamed inside it and only the benign name selected "
            "outside. The statement computes Net Revenue's certified "
            "expression exactly, so every earlier rule allows it and this "
            "rule is the only thing standing between a Client's name and the "
            "answer",
    ),
    RestrictedProbe(
        name="a union branch that names the Client",
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
        verdict=REJECTED,
        reasons=(RejectionReason.NOT_A_READ,),
        reaches=True,
        found_by_text=True,
        why="Net Revenue by region, and Net Revenue by Client name, in one "
            "statement — the leak in a branch a Gate reading the outermost "
            "scope would never reach. The Gate never gets that far, because a "
            "`UNION` is not a single `SELECT`, the refusal "
            "[R12](../../docs/plan/step-005-validation-gate.md#r12--aminos-rulings-on-the-51-review--decided-2026-08-26) "
            "confirmed as deliberate. The lineage walk still reads both "
            "branches, and the table below is where that stays measured",
    ),
    RestrictedProbe(
        name="the name in a comment",
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
        verdict=REJECTED,
        reasons=(RejectionReason.UNCERTIFIED_ROUTE,),
        reaches=False,
        found_by_text=True,
        why="a generator that was told the column is restricted, said so in a "
            "comment, and grouped by region instead. **This rule allows it**, and that "
            "is the false positive this rule is measured on: the query obeys the rule "
            "and names the rule while obeying it. The rejection arrives from Sub-step "
            "5.4's certified-route rule two places later, because the joins that reach "
            "`dim_client` are certified by nothing until 5.5 — so the Gate's verdict "
            "and this rule's verdict come apart here, which is what "
            "`check_this_rules_verdicts` reads `ValidationGateOutcome.rules` to tell "
            "apart",
    ),
    RestrictedProbe(
        name="the name in a string literal",
        sql="SELECT 'client_name' AS withheld_column, "
            "       sum((billed.commission - billed.rebate - billed.fee) "
            "           * rate.fx_rate) AS net_revenue "
            "FROM fct_trade AS billed "
            "JOIN fct_fx_rate AS rate "
            "  ON rate.rate_date = billed.trade_date "
            " AND rate.from_currency = billed.denomination_currency "
            " AND rate.to_currency = 'EUR'",
        verdict=ALLOWED,
        reaches=False,
        found_by_text=True,
        why="the restricted name as data rather than as a column — a label "
            "saying which column was left out. A string is not an identifier, "
            "and the difference is one a parse tree makes and a substring "
            "search cannot",
    ),
    RestrictedProbe(
        name="the name in a filter only",
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
        verdict=REJECTED,
        reasons=(RejectionReason.UNCERTIFIED_ROUTE,),
        reaches=False,
        found_by_text=True,
        why="one Client's revenue, with the name in the WHERE clause and out "
            "of the projection. **This rule allows it**: the rule is the Target "
            "State's — *no restricted column in the projection* — and the Glossary's "
            "`Restricted Column` row says so in the same words: *\"the name in "
            "a comment, in a string literal, or in a filter is not a "
            "projection of it\"*. Whether a filter on a column nobody reads "
            "should be allowed is a different question, and this Step does "
            "not widen into it. The rejection is Sub-step 5.4's, on the two joins that "
            "reach `dim_client` and that nothing certifies until 5.5",
    ),
    RestrictedProbe(
        name="projected inside, aggregated away",
        sql="SELECT count(*) AS clients "
            "FROM ( "
            "  SELECT DISTINCT client.client_name AS label "
            "  FROM fct_trade AS billed "
            "  JOIN dim_account AS account "
            "    ON account.account_id = billed.account_id "
            "  JOIN dim_client AS client "
            "    ON client.client_id = account.client_id "
            ") AS traded",
        verdict=REJECTED,
        reasons=(RejectionReason.SHADOW_METRIC,),
        reaches=False,
        found_by_text=True,
        why="how many distinct Clients traded — an ordinary question whose "
            "answer is one number and carries no name. The Client name is "
            "projected inside a subquery that cannot be folded away and never "
            "reaches the answer, so this rule allows it; the Gate refuses it "
            "anyway, because counting Clients is not a Certified Metric. Two "
            "rules disagreeing about one statement is the point: rejecting it "
            "*here* would be the false positive a Gate that reads every scope "
            "commits",
    ),
    RestrictedProbe(
        name="star beside a certified metric",
        sql="SELECT client.*, "
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
            "GROUP BY 1, 2, 3",
        verdict=REJECTED,
        reasons=(RejectionReason.RESTRICTED_COLUMN,),
        reaches=True,
        found_by_text=False,
        why="the same star, written so that it reaches this rule: `client.*` "
            "beside the certified Net Revenue expression, grouped by ordinal "
            "so that no column is named anywhere in the statement. The "
            "tracing rule is satisfied — there is a metric expression and it "
            "traces — and the projection the star expands to carries a "
            "Client's name. **This is the probe that makes "
            "[C4](../../docs/design/validation-feasibility.md#c4--the-gate-reads-the-schema-at-run-time)'s "
            "run-time schema read load-bearing inside the assembled Gate** "
            "rather than inside the detector alone: without the real column "
            "list there is one `Star` node in the projection, no column name "
            "anywhere in the tree or the text, and nothing to catch. **Added "
            "by Sub-step 5.3**, and the one shape here that is not the "
            "spike's",
    ),
)



# Two statements the detector cannot read, and they are unreadable in two different
# ways — which is the whole reason both are here.
#
# The first is `traces.py`'s `unresolvable` probe: a DuckDB list comprehension, which
# the engine plans happily and sqlglot's optimizer will not resolve. It refuses with a
# `SqlglotError`.
#
# The second refuses with a bare `AssertionError`, out of sqlglot's own
# `Expression.assert_is` — a star that no schema can expand, referred to by position in
# a `GROUP BY`. It is here because Sub-step 5.3 found that shape while mutating
# `expand_stars` off, and found that an `AssertionError` is not a `SqlglotError` and so
# escaped `resolve` as a crash. Inside the assembled Gate neither statement gets this
# far — the bounded rule refuses anything the engine will not plan, and the tracing rule
# refuses anything that will not resolve — so both are put to the detector directly.
UNREADABLE = {
    "the optimizer will not resolve it": "SELECT [x * 2 FOR x IN [1, 2, 3]] AS doubled",
    "sqlglot asserts rather than raising its own error":
        "SELECT unknown_table.*, count(fct_trade.trade_id) "
        "FROM fct_trade, unknown_table GROUP BY 1",
}


def rule_name(gate: ValidationGate, access_profile: AccessProfile) -> str:
    """This rule's name, read off the Gate's own rule list rather than typed here.

    Two of the checks below ask whether *this* rule ran on a statement, and the answer
    comes from `ValidationGateOutcome.rules`, which holds names. Matching on a name typed
    into this file would be a second copy of it, and the first thing to go stale when the
    rule is renamed — so the name is found by the method it belongs to.

    `rules()` binds this one rule to the identity `judge` was called with, so the entry
    in the list is a `partial` around the bound method rather than the bound method.
    `func` unwraps that; `__func__` unwraps the binding to `self`; and what is left is
    the function on the class, which is the only thing here that cannot be renamed
    without this comparison failing.

    An empty string when the Gate does not run the rule at all. That is not defensive:
    dropping the rule from `rules()` is this module's first mutation, and a check that
    raised there would report the mutation as a traceback instead of as the probes it
    breaks.
    """
    for name, rule in gate.rules(access_profile):
        bound = getattr(rule, "func", rule)
        if getattr(bound, "__func__", None) is ValidationGate.no_restricted_column:
            return name
    return ""


def found_by_text(sql: str, profile: AccessProfile) -> list[str]:
    """What ADR-0003's rejected alternative sees: the restricted name, in the text.

    Lower-cased on both sides and nothing else — no tokenising, no stripping of comments
    or string literals — because the alternative ADR-0003 rejected is matching text, and
    handing it a parser first is giving it the very thing it was rejected for lacking.

    It lives here rather than in `veritas/validation/` deliberately. This is the
    alternative the ADR turned down; putting it beside the rule that replaced it would
    leave a function in the Gate that nothing may call and someone might.
    """
    lowered = sql.lower()
    return sorted(
        str(column) for column in profile.restricted() if column.column in lowered
    )


def check_the_profile(profile: AccessProfile, report: Report) -> None:
    """Print the identity every verdict below was reached under.

    The profile is as much of the finding as the verdicts are: *which* columns are
    restricted is the whole content of *"no restricted column in the projection"*, and a
    profile that restricted nothing would pass every probe here while enforcing nothing.

    It takes the profile rather than reading one off the Gate, because there is nothing
    on the Gate to read: an Access Profile is what a question is judged **under**, not
    what a Gate is built with.
    """
    report.say(
        f"Access Profile: role {profile.role!r}, "
        f"{len(profile.restricted_columns)} Restricted Column(s) — "
        f"{', '.join(str(column) for column in profile.restricted()) or 'none'}"
    )
    if not profile.restricted_columns:
        problems.append(
            "the Access Profile restricts no columns, so every probe below passes this "
            "rule for the one reason that proves nothing — an empty declaration is not "
            "an enforced one"
        )


def check_the_parse_tree_against_the_text(
    gate: ValidationGate, profile: AccessProfile, report: Report
) -> None:
    """Judge every shape twice — from the parse tree and from the text — and compare
    both answers with the ones declared.

    Neither answer is assumed. The parse tree missing a Restricted Column is a leak; the
    parse tree finding one where there is none is the false positive that makes a Gate
    unusable; and the text column changing means ADR-0003's rejected alternative is no
    longer the thing being compared against.

    This is also where the three shapes the Gate refuses one rule earlier are measured.
    `judge_probes` reports what a caller gets; this reports what **this rule** reads, on
    every shape, including the ones whose verdict was decided before it ran.
    """
    schema = gate.warehouse.columns_by_table()
    report.say(f"{'tree':<10}{'text':<10}{'shape':<38}reaching the answer")

    unseen_by_text = matched_with_nothing_reaching = 0
    for probe in PROBES:
        try:
            reaching = restricted_columns_in_projection(
                probe.sql, profile.restricted_columns, schema
            )
        except TracerRefused as refusal:
            problems.append(
                f"the columns reaching {probe.name!r}'s answer could not be read "
                f"({refusal}) — its parse-tree answer is a refusal rather than the "
                f"measurement declared here"
            )
            continue
        by_text = found_by_text(probe.sql, profile)
        report.say(
            f"{'FOUND' if reaching else '—':<10}"
            f"{'matched' if by_text else 'missed':<10}"
            f"{probe.name:<38}"
            f"{', '.join(str(column) for column in reaching) or '—'}"
        )

        if probe.reaches and not reaching:
            problems.append(
                f"{probe.name!r} carries a Restricted Column into its answer and the "
                f"parse tree did not find one — the Gate would let it through. "
                f"{probe.why}"
            )
        if not probe.reaches and reaching:
            problems.append(
                f"{probe.name!r} carries no Restricted Column into its answer and the "
                f"parse tree found {[str(c) for c in reaching]} — a false positive, "
                f"which is the failure this probe measures. {probe.why}"
            )
        if probe.found_by_text != bool(by_text):
            problems.append(
                f"{probe.name!r} was measured as "
                f"{'matched' if probe.found_by_text else 'missed'} by text matching and "
                f"is now {'matched' if by_text else 'missed'} — the alternative "
                f"ADR-0003 rejected is no longer the one being measured against"
            )

        unseen_by_text += probe.reaches and not probe.found_by_text
        matched_with_nothing_reaching += probe.found_by_text and not probe.reaches

    report.say(
        f"text matching and the parse tree disagree on "
        f"{unseen_by_text + matched_with_nothing_reaching} of {len(PROBES)} shapes: "
        f"{unseen_by_text} the text cannot see, {matched_with_nothing_reaching} it would "
        f"reject with no Restricted Column reaching the answer at all"
    )


def check_this_rules_verdicts(
    gate: ValidationGate, profile: AccessProfile, rule: str, report: Report
) -> None:
    """The shapes this rule lets through, and the proof that it read them.

    A rule that rejects everything passes every rejection probe, so a rule module needs
    statements its own rule **allows** — and needs to show the rule actually ran on them
    rather than that some earlier rule refused them first. `ValidationGate` reports the
    rules that ran, which is exactly what makes that answerable.

    **What this rule decides is read off `rules`, not off `allowed`.** Until Sub-step 5.4
    the two were the same answer, because this was the last rule in the list; the
    certified-route rule now runs after it and refuses two of the three shapes this rule
    passes. Reading the Gate's verdict would report those two as shapes this rule
    refused, which is the opposite of what happened — see `probes.rule_verdicts`.

    The declaration compared against is `reaches`, not `verdict`. `verdict` is what a
    caller gets from the whole Gate; `reaches` is this rule's own reading — a Restricted
    Column is in the answer or it is not — so it is the honest thing to hold this rule's
    behaviour to.
    """
    refused, allowed, unseen = rule_verdicts(gate, PROBES, rule, profile)
    report.say(
        f"this rule ran on {len(refused) + len(allowed)} of {len(PROBES)} shapes, "
        f"refused {len(refused)} and passed {len(allowed)} on — the other "
        f"{len(unseen)} were refused by an earlier rule"
    )
    if not allowed:
        problems.append(
            "this rule allowed none of the shapes it ran on, so nothing here separates "
            "it from a rule that refuses everything"
        )
    for probe in PROBES:
        if probe.name in unseen:
            continue
        if probe.reaches and probe.name not in refused:
            problems.append(
                f"a Restricted Column reaches {probe.name!r}'s answer and this rule ran "
                f"on it and passed it on — the leak this rule exists to stop. "
                f"{probe.why}"
            )
        if not probe.reaches and probe.name in refused:
            problems.append(
                f"no Restricted Column reaches {probe.name!r}'s answer and this rule "
                f"refused it — the false positive that makes a Gate people route "
                f"around. {probe.why}"
            )


def check_the_rule_fails_closed(
    gate: ValidationGate, profile: AccessProfile, rule: str, report: Report
) -> None:
    """A statement the detector cannot read is a refusal, not an absence.

    `no_restricted_column`'s `UNRESOLVABLE` branch is **unreached inside the assembled
    Gate**: an earlier rule refuses both statements below, and the run says which one
    rather than leaving it to be assumed. The branch is kept anyway, and so is this
    check, because *"no Restricted Column found"* and *"could not look"* are the two
    answers this rule must never confuse — a detector that returned the first when it
    meant the second would fail **open** on exactly the statement nobody wrote a probe
    for.

    Both spellings of a refusal are measured. sqlglot raises `SqlglotError` for one and
    the built-in `AssertionError` for the other, and until Sub-step 5.3 the second
    escaped `resolve` as a crash — an error where the caller had asked for a verdict.
    """
    schema = gate.warehouse.columns_by_table()
    for description, sql in UNREADABLE.items():
        outcome = gate.judge(sql, profile)
        if rule in outcome.rules:
            problems.append(
                f"the unreadable statement ({description}) reached {rule!r}, so the "
                f"claim that an earlier rule refuses it first has stopped being true "
                f"and this shape now belongs in a declared probe"
            )
        try:
            reaching = restricted_columns_in_projection(
                sql, profile.restricted_columns, schema
            )
        except TracerRefused as refusal:
            report.say(
                f"{description}: the Gate refuses it at {outcome.rules[-1]!r}, and "
                f"asked directly the detector raises {refusal.args[0].split(':')[0]} "
                f"rather than reporting nothing found"
            )
            continue
        problems.append(
            f"the detector read a statement it cannot read ({description}) and "
            f"reported {[str(column) for column in reaching]} instead of refusing it — "
            f"a statement with no readable projection has nothing to judge, and "
            f"answering 'nothing found' about it is a hole\n      {sql}"
        )


def check(warehouse: WarehouseAdapter) -> Report:
    """Everything this module has to say, in one report."""
    report = Report("no Restricted Column reaches the answer")
    gate = ValidationGate(warehouse)
    rule = rule_name(gate, ANALYST)
    if not rule:
        problems.append(
            "the Gate's rule list holds no entry for `no_restricted_column`, so nothing "
            "below is judging the rule this module exists to check"
        )
    check_the_profile(ANALYST, report)
    check_the_statements_are_the_spikes(
        PROBES,
        constant="RESTRICTED_COLUMN_PROBES",
        label="claim-2",
        added_by="Sub-step 5.3",
        covered_elsewhere={},
        report=report,
    )
    judge_probes(gate, PROBES, report, ANALYST)
    report.say("")
    check_the_parse_tree_against_the_text(gate, ANALYST, report)
    report.say("")
    check_this_rules_verdicts(gate, ANALYST, rule, report)
    check_the_rule_fails_closed(gate, ANALYST, rule, report)
    return report
