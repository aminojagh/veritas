"""What a Grounded Answer looks like to a person, as values rather than as widgets.

Nothing here imports Streamlit. Each function turns a `GroundedAnswer`, a
`Validation Gate outcome` or an `Access Profile` into the strings a page shows, and
`page.py` is what places them.
"""

from decimal import Decimal

from veritas.llm import LanguageModelError, default_model
from veritas.orchestrator import GroundedAnswer
from veritas.semantic import MetricDefinition
from veritas.validation import AccessProfile, ValidationGateOutcome

# What the App says about the enforcement it demonstrates, in the words
# [DEBT-008](../../.claude/docs/debt-ledger.md#debt-008--the-access-control-story-promises-more-than-it-delivers)
# asks for rather than a paraphrase of them. It sits beside the identity on the page,
# because a qualification a reader meets after the claim is a qualification most readers
# never meet.
ENFORCEMENT_NOTE = (
    "Access Profile enforcement is applied in the application layer, over synthetic "
    "data. It demonstrates the mechanism; it is not a production access control, and "
    "it does not protect the Warehouse from being read another way."
)

# What a NULL is shown as. A blank cell is indistinguishable from a zero-width string
# and from a rendering bug.
NOTHING = "—"


def formatted(value: object) -> str:
    """One value out of the Warehouse, as a person reads it.

    Money and counts carry thousands separators — a brokerage figure is read wrong
    without them — and a decimal keeps two places, which is the grain every Certified
    Metric's `unit` is quoted in. Everything else is its own string.
    """
    if value is None:
        return NOTHING
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, Decimal | float):
        return f"{value:,.2f}"
    if isinstance(value, int):
        return f"{value:,}"
    return str(value)


def labels(answer: GroundedAnswer) -> list[str]:
    """The engine's name for each position in a row, made unique.

    A statement may name two output columns the same thing, and a table keyed by name
    would show one of them and drop the other silently. A repeated name carries its
    position; a name that appears once is left alone.
    """
    return [
        name if answer.columns.count(name) == 1 else f"{name} ({position})"
        for position, name in enumerate(answer.columns)
    ]


def table(answer: GroundedAnswer) -> dict[str, list[str]]:
    """The answer's rows under the names their columns came back with.

    Formatted here rather than at the point of display, so what a test reads is what a
    person sees.
    """
    return {
        label: [formatted(row[position]) for row in answer.rows]
        for position, label in enumerate(labels(answer))
    }


def single_value(answer: GroundedAnswer) -> tuple[str, str] | None:
    """The label and the value of a one-number answer, or `None` for anything else.

    A breakdown, an empty result and an unanswered question are all `None`: they are
    tables or they are not numbers, and both are shown as such.
    """
    if len(answer.rows) == 1 and len(answer.columns) == 1:
        return labels(answer)[0], formatted(answer.rows[0][0])
    return None


def unit_line(answer: GroundedAnswer) -> str:
    """What a one-number answer is in: the Certified Metric that produced it, that
    metric's `unit`, and its Reporting Currency where it has one.

    A single figure comes back under whatever the statement aliased it — `answer` — so
    the number reaches a person labelled with nothing they can read a unit off. The
    metric is identifiable because Lineage now records what the statement used, which is
    the smaller thing
    [DEBT-034](../../.claude/docs/debt-ledger.md#debt-034--lineage-records-what-the-model-was-shown-not-what-the-statement-used)
    was blocking: *"the figure is shown without its unit or its reporting currency,
    because the metric whose `unit` and `reporting_currency` would label it is not
    identifiable from a list that names two."*

    Empty for anything that is not one number, and empty when the Lineage names no
    metric or more than one. A unit no entry pins down is a unit invented for the page.
    """
    if single_value(answer) is None:
        return ""
    metrics = [
        entry
        for entry in answer.lineage.entries
        if isinstance(entry, MetricDefinition)
    ]
    if len(metrics) != 1:
        return ""
    [metric] = metrics
    currency = f", in {metric.reporting_currency}" if metric.reporting_currency else ""
    return f"{metric.name} — {metric.unit}{currency}"


def outcome_line(outcome: ValidationGateOutcome | None) -> str:
    """The Validation Gate's verdict in one line: what it decided and what it read.

    An allowed statement names the rules that ran, because the Gate stops at the first
    rule that rejects and a verdict is only as wide as the rules it got through. A
    rejected one names its Rejection Reasons, which are the same members Observability
    charts.
    """
    if outcome is None:
        return "no statement reached the Validation Gate"
    if outcome.allowed:
        return f"allowed — {len(outcome.rules)} rules ran: {', '.join(outcome.rules)}"
    return f"rejected — {', '.join(outcome.reasons)}"


def lineage_lines(answer: GroundedAnswer) -> list[str]:
    """Each Semantic Entry the answer was built from: name, kind, and version read."""
    return [
        f"{entry.name} — {entry.kind} v{entry.version}"
        for entry in answer.lineage.entries
    ]


def identity_lines(access_profile: AccessProfile) -> list[str]:
    """Who the question is asked as: the role, the region it may see, the columns it
    may not."""
    restricted = ", ".join(str(column) for column in access_profile.restricted())
    return [
        f"role — {access_profile.role}",
        f"region — {access_profile.permitted_region}",
        f"restricted — {restricted or NOTHING}",
    ]


def model_line() -> str:
    """Which model this installation will ask, or the reason it can ask none.

    Building a client opens no socket, so the page can say at rest whether a question
    would reach a provider at all.
    """
    try:
        return default_model().model
    except LanguageModelError as unreachable:
        return str(unreachable)
