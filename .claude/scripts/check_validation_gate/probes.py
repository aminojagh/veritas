"""Shared probe machinery for the Validation Gate check: the adapter, the probe
record, and the report every rule module writes into.

Run the check with:  uv run python .claude/scripts/check_validation_gate/

The container is
[R8](../../docs/plan/step-005-validation-gate.md#r8--the-steps-check-is-a-package-with-one-module-per-rule-from-51--approved-by-amino-2026-08-25)'s:
a runner, this module, and one module per rule added with the Sub-step that adds the
rule. The three checks grown by the method this one inherits are each well over a
thousand lines — `wc -l .claude/scripts/*.py` prints where they have got to — and none
of them was ever decided to be a monolith. Splitting a package that does not exist
costs nothing.

**The method is the spike's.** A Gate is a judge, and a judge is tested by putting
cases in front of it: every probe declares the verdict this Sub-step measured for it,
so *"rejected"* is never left to a reader to interpret as good or bad news. A probe
whose verdict changes in **either** direction fails the run.
"""

import ast
import sys
from dataclasses import dataclass, field, replace
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = SCRIPTS_DIR.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from veritas.validation import (  # noqa: E402 — after sys.path, like the checks beside it
    ACCESS_AXIS,
    AccessProfile,
    RejectionReason,
    ValidationGate,
)
from veritas.warehouse import DATABASE_PATH, WarehouseAdapter  # noqa: E402

# Every problem any rule module found. One list so the runner can report the count
# and set the exit code in one place, the way the check scripts beside this one do.
problems: list[str] = []

ALLOWED = "allowed"
REJECTED = "rejected"


@dataclass(frozen=True, slots=True)
class Probe:
    """One statement, the verdict this Sub-step measured for it, and why it is here.

    `reasons` is the Rejection Reason members the probe must come back with, so a
    rejection for the wrong reason fails as loudly as no rejection at all — the
    taxonomy is what Observability groups by, and a rule that rejects everything
    passes every rejection probe.

    `ceiling` judges the probe under a scan ceiling of its own. That is how the
    bounded-read rule is given teeth without a query big enough to trip the real
    ceiling: the rule under test is the comparison, and a probe that had to build a
    million-row scan would be measuring the Warehouse's size instead.
    """

    name: str
    sql: str
    verdict: str
    why: str
    reasons: tuple[RejectionReason, ...] = ()
    ceiling: int | None = None


@dataclass(slots=True)
class Report:
    """What one rule module found: lines to print, and problems to fail on.

    Printed rather than asserted, because Non-Negotiable #4 asks for a committed
    command whose **output** a review can quote, and the numbers in that output are
    half of what a review quotes.
    """

    heading: str
    lines: list[str] = field(default_factory=list)

    def say(self, line: str) -> None:
        self.lines.append(line)

    def print(self) -> None:
        print()
        print(f"  {self.heading}")
        for line in self.lines:
            print(f"    {line}")


def judge_probes(
    gate: ValidationGate,
    probes: tuple[Probe, ...],
    report: Report,
    access_profile: AccessProfile,
) -> None:
    """Put every probe in front of the Gate and compare the verdict with the declared one.

    The Gate is rebuilt with the probe's own ceiling where it declares one, rather
    than the ceiling being reached into and changed: a `ValidationGate` is frozen, and
    a check that mutated the thing under test would be measuring something else.

    `replace` rather than a fresh `ValidationGate(...)` call, so the rebuilt Gate is the
    one under test with one field moved. Constructing a new one names some fields and
    silently re-defaults the rest, which meant a probe with a ceiling was quietly judged
    against a second load of `semantic/` — the same corpus by luck, and a second read of
    the files while the point of this module is to judge one.

    The identity is not one of those fields: `judge` takes it, so every probe here is
    judged under the profile this call names and a ceiling probe cannot pick up a
    different one.
    """
    for probe in probes:
        judged = (
            gate if probe.ceiling is None else replace(gate, scan_ceiling=probe.ceiling)
        )
        outcome = judged.judge(probe.sql, access_profile)
        verdict = ALLOWED if outcome.allowed else REJECTED
        reasons = tuple(outcome.reasons)
        ceiling = "" if probe.ceiling is None else f", ceiling {probe.ceiling}"
        report.say(
            f"{verdict:9} {probe.name:38} "
            f"{', '.join(reason.value for reason in reasons) or '—'}{ceiling}"
        )
        if verdict != probe.verdict:
            problems.append(
                f"{probe.name!r} was measured as {probe.verdict} and came back "
                f"{verdict} — {probe.why}\n      {probe.sql}\n      {outcome.explanation}"
            )
            continue
        if reasons != probe.reasons:
            problems.append(
                f"{probe.name!r} was rejected for "
                f"{[r.value for r in reasons]} where it was measured as "
                f"{[r.value for r in probe.reasons]} — a rejection for the wrong "
                f"reason is a mislabelled bar on the chart ADR-0003 sold determinism "
                f"on\n      {probe.sql}"
            )


def rule_verdicts(
    gate: ValidationGate,
    probes: tuple[Probe, ...],
    rule: str,
    access_profile: AccessProfile,
) -> tuple[list[str], list[str], list[str]]:
    """Which shapes `rule` refused, which it allowed, and which it never saw.

    **A rule's own verdict is not the Gate's**, and telling them apart is what every rule
    module needs a positive control for: a rule that refuses everything passes every
    rejection probe, so each module has to show its rule letting something through. Until
    Sub-step 5.4 that was read off `ValidationGateOutcome.allowed`, which was the same
    answer while the rule under test was the last one in the list — and stopped being the
    same answer the moment a rule was added after it. Three shapes `restricted.py`'s rule
    allows are refused by the certified-route rule two places later, and reading the
    Gate's verdict would report them as shapes that rule refused.

    `ValidationGateOutcome.rules` is what makes the distinction answerable, and it is the
    field 5.1 added for exactly this. A rule that did not appear never ran; a rule that
    appears **last** on a rejected outcome is the rule that rejected; anything else is a
    rule that ran and passed the statement on.
    """
    refused: list[str] = []
    allowed: list[str] = []
    unseen: list[str] = []
    for probe in probes:
        outcome = gate.judge(probe.sql, access_profile)
        if rule not in outcome.rules:
            unseen.append(probe.name)
        elif not outcome.allowed and outcome.rules[-1] == rule:
            refused.append(probe.name)
        else:
            allowed.append(probe.name)
    return refused, allowed, unseen


def rule_named(
    gate: ValidationGate, method: object, access_profile: AccessProfile
) -> str:
    """One rule's name, read off the Gate's own rule list rather than typed here.

    A name typed into a rule module is a second copy of it and the first thing to go
    stale when the rule is renamed, so every module asks the Gate instead. There were
    three near-copies of this by Sub-step 5.4 and `access.py` would have been the
    fourth, which is when one function became cheaper than four.

    Two unwrappings, and each is for a different reason. `func` gets past the `partial`
    the Gate uses to bind an Access Profile into the two rules that judge against an
    identity — `no_restricted_column` and `scoped` — and a rule that takes no profile is
    not wrapped at all, so `getattr(rule, "func", rule)` covers both. `__func__` then
    gets past the binding to `self`, which is what makes the comparison about the
    function on the class rather than about this Gate instance.

    An empty string when the Gate does not run the rule at all, so that deleting a rule
    from `rules()` — every module's first mutation — is reported as the probes it breaks
    rather than as a traceback.
    """
    for name, rule in gate.rules(access_profile):
        if getattr(getattr(rule, "func", rule), "__func__", None) is method:
            return name
    return ""


def certified_statement(
    gate: ValidationGate,
    name: str,
    access_profile: AccessProfile,
    with_filters: bool = True,
    sliced_by: str = "",
) -> str:
    """The simplest statement that computes one Certified Metric and is allowed to run.

    Built from the entry's own fields rather than written out, which is what makes the
    metric probes nine probes and not nine more literals to keep in step with
    `semantic/`: a tenth Metric Definition is a tenth probe with no edit to any module.
    Three modules build this statement and they build one statement, because two
    builders is two chances to disagree about what the corpus says a metric is.

    **Since Sub-step 5.5 it carries the access route and the access predicate**, and
    that is not a decoration on the probe — it is what a Veritas statement now is. The
    Access-Profile-predicate rule refuses an unscoped statement however certified
    everything else about it is, so *"the simplest statement that computes this metric"*
    and *"the simplest statement that computes this metric and is allowed"* stopped
    being the same string, and this is the second. The route that scopes it is the
    `by region` axis's own `routes` for the metric's `from_table` — the same field the
    Gate reads, so a corpus that could not scope a metric would fail here rather than
    being worked around.

    `with_filters=False` builds the statement the corpus does **not** certify, and it
    exists for
    [DEBT-020](../../docs/debt-ledger.md#debt-020--the-gate-checks-a-metrics-route-and-not-its-certified-filters)'s
    pair alone. `sliced_by` names an axis to group by, and adds that axis's own route
    for the same `from_table`.
    """
    layer = gate.semantic
    metric = layer.metrics[name]
    axis = layer.dimensions[ACCESS_AXIS]
    joins = list(metric.join_paths)
    for reached in ((layer.dimensions[sliced_by],) if sliced_by else ()) + (axis,):
        for join_path in reached.routes[metric.from_table]:
            if join_path not in joins:
                joins.append(join_path)
    route = " ".join(
        f"JOIN {layer.join_paths[join_path].to_table} "
        f"ON {layer.join_paths[join_path].on}"
        for join_path in joins
    )
    predicates = [
        *(metric.filters if with_filters else ()),
        f"{axis.columns[0]} = '{access_profile.permitted_region}'",
    ]
    # `ORDER BY` as well as `GROUP BY`, and it is not decoration: a slice printed in
    # whatever order the engine happens to return is a different line of output on each
    # run, and a review quoting it would be quoting something a reader cannot reproduce.
    # No Gate rule reads an `ORDER BY`.
    axis_column = layer.dimensions[sliced_by].columns[0] if sliced_by else ""
    group = f" GROUP BY {axis_column} ORDER BY {axis_column}" if sliced_by else ""
    sliced = f"{axis_column} AS slice, " if sliced_by else ""
    return (
        f"SELECT {sliced}{metric.expression} AS answer "
        f"FROM {metric.from_table} {route} "
        f"WHERE {' AND '.join(predicates)}{group}"
    )


def warehouse() -> WarehouseAdapter:
    """The built Warehouse, or a refusal that says how to build it.

    The Gate's bounded-read rule asks the engine to plan a statement, so this check
    needs a Warehouse with the star schema in it for the same reason
    `check_semantic_layer.py` does.
    """
    if not DATABASE_PATH.exists():
        raise SystemExit(
            f"no Warehouse at {DATABASE_PATH.relative_to(REPO_ROOT)} — run "
            f"`uv run python -m veritas.ingestion` first"
        )
    return WarehouseAdapter()


# The spike, as a file rather than as a module. See `spike_statements`.
SPIKE = SCRIPTS_DIR / "check_validation_feasibility.py"


def spike_statements(constant: str) -> dict[str, str]:
    """One of the spike's probe tuples as `name` → `sql`, read out of its **text**.

    Two rule modules here judge shapes the spike measured first, and each claims its
    statements are the spike's *character for character*. That is a claim about text, so
    it is checked against text: `ast.parse` reads
    `check_validation_feasibility.py` without executing it, and the `name=` and `sql=`
    literals come off the parse tree.

    **Reading rather than importing is the point.** An import would run a 1,700-line
    script's module-level work, and everything it imports in turn, on every run of a
    check whose question is *"is this string the same string"*. It would also make the
    dependency a live one — this package would stop working the day the spike stopped
    importing — where what is actually depended on is a file at a path, held in this
    repository, whose statements are a **dated measurement** that must not move. The
    spike goes on importing the tracer and the detector from `veritas/validation/` under
    [R2](../../docs/plan/step-005-validation-gate.md#r2--the-spike-imports-the-gate-rather-than-keeping-its-own-tracer--approved-by-amino-2026-08-25);
    nothing imports the spike. That is
    [R14](../../docs/plan/step-005-validation-gate.md#r14--aminos-rulings-on-the-53-review--decided-2026-08-27).

    Adjacent string literals are folded by the parser, so a statement the spike writes
    across fifteen source lines comes back as the one string the spike compiled — which
    is what makes a text comparison possible at all.

    A `SystemExit` rather than a problem when the constant has gone: the run cannot
    answer its question, and a check that reported *"0 of 0 statements differ"* would
    pass by finding nothing, which is the failure this whole file is arranged against.
    """
    module = ast.parse(SPIKE.read_text(encoding="utf-8"), filename=str(SPIKE))
    for node in module.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(
            isinstance(target, ast.Name) and target.id == constant
            for target in node.targets
        ):
            continue
        if not isinstance(node.value, ast.Tuple):
            raise SystemExit(
                f"{SPIKE.name} assigns `{constant}` something other than a tuple of "
                f"probes, so its statements cannot be read out of the file"
            )
        statements: dict[str, str] = {}
        for element in node.value.elts:
            fields = (
                {keyword.arg: keyword.value for keyword in element.keywords}
                if isinstance(element, ast.Call)
                else {}
            )
            if "name" not in fields or "sql" not in fields:
                raise SystemExit(
                    f"a probe in {SPIKE.name}'s `{constant}` does not name both `name` "
                    f"and `sql` as keywords, so this file cannot read its statements"
                )
            statements[ast.literal_eval(fields["name"])] = ast.literal_eval(
                fields["sql"]
            )
        return statements
    raise SystemExit(
        f"{SPIKE.name} holds no `{constant}` at module level — the provenance of the "
        f"statements in this check cannot be established, and an unchecked claim that "
        f"they are the spike's is the thing this function exists to replace"
    )


def check_the_statements_are_the_spikes(
    ours: tuple[Probe, ...],
    constant: str,
    label: str,
    added_by: str,
    covered_elsewhere: dict[str, str],
    report: Report,
) -> None:
    """This module's statements are the spike's, character for character — checked.

    The spike's probes are a **dated measurement**: each shape carries a recorded
    reading, and a rule module here is only comparable with that measurement while it
    judges the same text. A statement quietly reworded — a rename, a reflowed line, a
    tidied alias — would leave two runs that look like they agree about a shape and do
    not. So the claim is read out of the spike's source rather than left in a comment.

    Three outcomes per statement, and each says something different:

      * **the same name and the same text** — the shape is the spike's, unchanged;
      * **the same name and different text** — a problem, and the loudest one here: the
        two files have drifted apart while still looking like they agree;
      * **a name this module coined** — counted and reported, never a problem. A rule
        module is free to add shapes the spike never had, and 5.2 and 5.3 both did.

    A statement the spike measures that this module does not judge is a **problem
    unless it is declared** in `covered_elsewhere`, which names where the shape is
    covered instead. A declaration that has stopped being true — the spike dropped the
    statement, or this module judges it after all — fails too, because an allowance
    nobody re-reads is how coverage quietly shrinks.
    """
    theirs = spike_statements(constant)
    mine = {probe.name: probe.sql for probe in ours}
    theirs_by_sql = {sql: name for name, sql in theirs.items()}

    identical = added = 0
    renames: list[str] = []
    for name, sql in mine.items():
        if name in theirs:
            if theirs[name] == sql:
                identical += 1
            else:
                problems.append(
                    f"the statement for {name!r} differs from the spike's, so this "
                    f"module and the spike's dated measurement are no longer judging "
                    f"the same shape\n      spike: {theirs[name]}\n      here:  {sql}"
                )
        elif sql in theirs_by_sql:
            identical += 1
            renames.append(
                f"{name!r} is the spike's {theirs_by_sql[sql]!r}, character for "
                f"character, under a shorter name"
            )
        else:
            added += 1

    report.say(
        f"{identical} of the spike's {len(theirs)} {label} statements are here "
        f"character for character{f' ({len(renames)} renamed)' if renames else ''}; "
        f"{added} added by {added_by}"
    )
    for rename in renames:
        report.say(rename)

    unjudged = {
        name: sql
        for name, sql in theirs.items()
        if name not in mine and sql not in set(mine.values())
    }
    for name in sorted(unjudged):
        if name in covered_elsewhere:
            report.say(
                f"the spike's {name!r} is not judged here — {covered_elsewhere[name]}"
            )
        else:
            problems.append(
                f"the spike measures {name!r} and this module does not judge it — a "
                f"shape the feasibility run covered and the Gate's own check does not"
            )
    for name, where in covered_elsewhere.items():
        if name not in unjudged:
            problems.append(
                f"{name!r} is declared as covered elsewhere ({where}) and the spike no "
                f"longer has a statement this module skips under that name — the "
                f"allowance has stopped describing anything and should be removed"
            )
