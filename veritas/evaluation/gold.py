"""Reads the Gold Question Set and derives each Gold Question's Relevant Set.

[`Gold Question Set`](../../.claude/docs/glossary.md#a-the-system) is *"the evaluation
corpus: question, gold SQL, gold result, and the Semantic Entries the gold SQL
touches"*. The first three are written down, one file per question under `data/gold/`;
the fourth is the [`Relevant Set`](../../.claude/docs/glossary.md#a-the-system), and it
is **derived** here, through the Validation Gate's own readers, so no Relevant Set is a
second opinion about what a statement computes.

**A Gold Question that Veritas should not answer carries no SQL.** `expects` says which
of a Grounded Answer's three endings is correct — a number, a refusal, or a
[`Clarifying Question`](../../.claude/docs/glossary.md#a-the-system) — and the loader
refuses a file that carries a statement for an ending that has none, or none for the
ending that needs one.

**What "touches" means, one reading per entry type:**

  Metric Definition     the statement's projections trace to its expression.
  Dimension Definition  the statement groups by, or filters on, one of its columns.
  Join Path             one of the two above declares it — the metric's own
                        `join_paths`, or an axis's `routes` from that metric's
                        `from_table`.

An [`Ambiguous Term`](../../.claude/docs/glossary.md#d-ambiguous-terms) publishes no SQL,
so no gold SQL touches one and none is ever in a Relevant Set. What a question says
rather than what its statement computes is the rewrite step's reading, not this one's.
"""

from collections.abc import Iterable, Sequence
from dataclasses import MISSING, dataclass, fields
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from pathlib import Path

import yaml
from sqlglot import exp
from sqlglot.optimizer.scope import build_scope

from veritas.semantic import (
    DimensionDefinition,
    MetricDefinition,
    SemanticEntry,
    SemanticLayer,
)
from veritas.validation import (
    Reading,
    TracerRefused,
    ValidationGate,
    base_tables,
    grouped_columns,
    on_base_tables,
    read,
)

EVALUATION_PACKAGE_DIR = Path(__file__).resolve().parent
REPO_ROOT = EVALUATION_PACKAGE_DIR.parent.parent

GOLD_DIR = REPO_ROOT / "data" / "gold"

# How close two result sets must be to be the same answer, as a fraction of the larger
# figure. A policy constant and not a measurement: a correct statement recomputes a gold
# figure exactly, so what this absorbs is the six decimal places a gold result is written
# to and the rounding a differently-written but equivalent computation can reach. It is
# relative because the Certified Metrics span a count of dozens and a notional of tens of
# millions, and one absolute figure cannot mean the same thing at both ends.
#
# It is also the width inside which a wrong answer would score as correct, which is what
# [DEBT-004](../../.claude/docs/debt-ledger.md#debt-004--the-fx-date-distinction-is-too-small-to-be-a-reliable-evaluation-signal)
# and [DEBT-011](../../.claude/docs/debt-ledger.md#debt-011--execution-price-against-market-price-cancels-at-book-level)
# constrain a Gold Question against: `tests/test_gold.py` executes both halves of each
# Glossary Section C pair a Gold Question turns on and fails the run if they are closer
# together than this.
RESULT_TOLERANCE = Decimal("0.0001")

# How many decimal places a gold result is written to in `data/gold/`, and therefore how
# a numeric value is spelled when rows are put in a comparable order. The Warehouse's
# monetary scale — `veritas/warehouse/schema.sql` declares money as `DECIMAL(18, 6)`.
GOLD_SCALE = 6


class Expectation(StrEnum):
    """Which ending a Gold Question says is correct.

    The three a `GroundedAnswer` has, and a `StrEnum` so the member survives into an
    Evaluation table as the word a person reads.
    """

    ANSWER = "answer"
    """A number, with the statement and the allowing verdict behind it."""

    REFUSAL = "refusal"
    """No statement the Semantic Layer can certify — the model's refusal or the Gate's."""

    CLARIFYING_QUESTION = "clarifying question"
    """The question said an Ambiguous Term and did not say which meaning."""


class PhrasingClass(StrEnum):
    """How a Gold Question spells a registered Ambiguous Term, when not as registered.

    The four classes of
    [DEBT-029](../../.claude/docs/debt-ledger.md#debt-029--ambiguous-term-detection-is-literal-so-every-other-phrasing-of-a-registered-word-passes-silently)'s
    own table, carried on the question as data so that the entry's repayment is scored
    over the Gold Question Set rather than over four strings in a test.
    """

    MORPHOLOGY = "morphology"
    """A different inflection of the registered word — *"revenues"* for `revenue`."""

    ORTHOGRAPHY = "orthography"
    """A different spelling of it — *"PnL"* for `P&L`."""

    SYNONYM = "synonym"
    """A different word for the same ambiguity — *"turnover"* for `volume`."""

    PHRASING = "phrasing"
    """A different way of asking it — *"how much is in"* for `how much does X have`."""


class GoldQuestionError(ValueError):
    """A file under `data/gold/` that cannot be read as a Gold Question.

    Raised rather than collected, for the reason `SemanticEntryError` is: a Gold
    Question that half-loads is a measure computed over ground truth nobody wrote.
    """


@dataclass(frozen=True)
class GoldQuestion:
    """One question the Gold Question Set holds, as it is written down.

    `question` is the question as a person asks it and is what Retrieval and the
    Orchestrator are given; `sql` is the statement that answers it correctly and `result`
    is what that statement returns. `expects` says which ending is correct, and
    `phrasing_class` is set only where the question spells an Ambiguous Term some way
    other than the registered one.

    The relevant Semantic Entries are deliberately **not** a field: they are derived from
    `sql` by `relevant_entries`, so ground truth about the corpus is never written by hand
    beside ground truth about the answer.
    """

    name: str
    question: str
    expects: Expectation
    sql: str = ""
    result: tuple[tuple[object, ...], ...] = ()
    phrasing_class: PhrasingClass | None = None

    @property
    def answerable(self) -> bool:
        """Whether a correct Veritas returns a number for this question."""
        return self.expects is Expectation.ANSWER


def read_gold_question(path: Path) -> GoldQuestion:
    """Read one file as a Gold Question, or raise with the file and the key named.

    The dataclass field list above is the file format, as it is for a Semantic Entry:
    a key the format does not name fails to load rather than being ignored, and a key it
    requires and the file omits fails by name.
    """
    if path.suffix != ".yaml":
        raise GoldQuestionError(f"{_here(path)}: a Gold Question is a .yaml file")

    document = yaml.safe_load(path.read_text())
    if not isinstance(document, dict):
        raise GoldQuestionError(
            f"{_here(path)}: reads as {type(document).__name__}, not a mapping of fields"
        )

    expected = {entry_field.name for entry_field in fields(GoldQuestion)}
    optional = {
        entry_field.name
        for entry_field in fields(GoldQuestion)
        if entry_field.default is not MISSING
    }
    missing = sorted(expected - optional - set(document))
    unknown = sorted(set(document) - expected)
    if missing or unknown:
        raise GoldQuestionError(
            f"{_here(path)}: "
            + " and ".join(
                part for part in (
                    f"missing required field(s) {missing}" if missing else "",
                    f"has field(s) {unknown} that a Gold Question does not have"
                    if unknown else "",
                ) if part
            )
        )

    question = GoldQuestion(
        name=str(document["name"]).strip(),
        question=str(document["question"]).strip(),
        expects=_member(path, "expects", Expectation, document["expects"]),
        sql=str(document.get("sql", "")).strip(),
        result=_rows(path, document.get("result", [])),
        phrasing_class=(
            _member(path, "phrasing_class", PhrasingClass, document["phrasing_class"])
            if document.get("phrasing_class") else None
        ),
    )

    # The one cross-field rule, and it is what makes `expects` a claim rather than a
    # label: a question Veritas should not answer has no correct statement to write down,
    # and one it should answer is not ground truth without one.
    if question.answerable and not (question.sql and question.result):
        raise GoldQuestionError(
            f"{_here(path)}: expects an answer, so it carries the gold SQL that answers "
            f"it and the gold result that statement returns"
        )
    if not question.answerable and (question.sql or question.result):
        raise GoldQuestionError(
            f"{_here(path)}: expects {question.expects}, and a question Veritas does not "
            f"answer has no gold SQL and no gold result"
        )
    return question


def load_gold_questions(root: Path = GOLD_DIR) -> list[GoldQuestion]:
    """The whole Gold Question Set, alphabetically, or raise on the first bad file.

    Every file rather than every `*.yaml`, for the reason `entry_files` reads every file
    under `semantic/`: a stray file the loader does not recognise is a finding, not
    something to walk past.
    """
    questions: list[GoldQuestion] = []
    named: dict[str, Path] = {}
    for path in sorted(path for path in root.rglob("*") if path.is_file()):
        question = read_gold_question(path)
        if question.name in named:
            raise GoldQuestionError(
                f"{_here(path)}: a second Gold Question named {question.name!r} — "
                f"{_here(named[question.name])} already claims that name"
            )
        named[question.name] = path
        questions.append(question)
    return questions


def reading_of(sql: str, gate: ValidationGate) -> Reading:
    """One statement, read the way a judgement reads it.

    The same catalogue and the same corpus `ValidationGate.judge` supplies, so what is
    derived here is derived from the tree the Gate judged rather than from a second
    parse of the same text.
    """
    return read(
        sql,
        catalogue=gate.catalogue,
        certified_expressions={
            name: metric.expression for name, metric in gate.semantic.metrics.items()
        },
    )


def filtered_columns(resolved: exp.Expression) -> set[tuple[str, str]]:
    """Every base-table column a WHERE clause in this statement keys on.

    `date_columns_filtered` without the test that the column is a date, and every scope
    for the same reason: a period, a certified filter and the Access Profile's predicate
    are all written in a WHERE, and each of them names the axis the answer is narrowed
    along.

    The JOIN conditions are deliberately not read. Every Join Path that reaches
    `fct_fx_rate` keys on a date, so a reading that took join conditions too would find
    the trade-date axis in every converted metric and have nothing left to say.
    """
    root = build_scope(resolved)
    if root is None:
        raise TracerRefused("sqlglot built no scope for the statement")
    filtered: set[tuple[str, str]] = set()
    for scope in root.traverse():
        if not isinstance(scope.expression, exp.Select):
            continue
        where = scope.expression.args.get("where")
        if where is None:
            continue
        base = base_tables(scope)
        for column in on_base_tables(where, base).find_all(exp.Column):
            filtered.add((column.table, column.name))
    return filtered


def metrics_touched(
    reading: Reading, gate: ValidationGate
) -> list[MetricDefinition]:
    """The Certified Metrics a statement computes, in the order it computes them."""
    return [gate.semantic.metrics[name] for name in gate.traced_metrics(reading)]


def axes_touched(
    resolved: exp.Expression, gate: ValidationGate
) -> list[DimensionDefinition]:
    """The certified axes a statement slices by or narrows along, by name.

    `ValidationGate.axes_sliced_by` is the corpus lookup from a column to the axis that
    publishes it; what changes here is which columns it is asked about. The route rule
    asks only about `GROUP BY`, because a slice is the one thing that earns a join. A
    Relevant Set is a wider question — the axis a period is filtered on and the axis an
    identity is scoped along are both what the statement is about.
    """
    return gate.axes_sliced_by(grouped_columns(resolved) | filtered_columns(resolved))


def join_paths_touched(
    metrics: Iterable[MetricDefinition],
    axes: Iterable[DimensionDefinition],
    layer: SemanticLayer,
) -> list[str]:
    """The Join Paths those metrics and axes declare, named once and in join order.

    The same three sources of permission `ValidationGate.permitted_route` assembles a
    Route from, kept as names instead of as canonicalised join conditions: the metric's
    own `join_paths`, then the `routes` each axis declares from that metric's
    `from_table`. Nothing searches `semantic/joins/` for a chain that would reach a
    table, so a Join Path is relevant because an entry names it.
    """
    wanted = list(axes)
    names: list[str] = []
    for metric in metrics:
        for name in [
            *metric.join_paths,
            *(name for axis in wanted for name in axis.routes.get(metric.from_table, ())),
        ]:
            if name not in names and name in layer.join_paths:
                names.append(name)
    return names


def relevant_entries(
    gold: GoldQuestion, gate: ValidationGate
) -> list[SemanticEntry]:
    """The Semantic Entries this Gold Question's SQL touches — its Relevant Set.

    Metric Definitions first, then the axes, then the Join Paths those two declare. A
    Gold Question with no gold SQL touches nothing and returns an empty list: there is
    no statement to read, which is the honest answer for a question whose correct
    ending is a refusal or a Clarifying Question.
    """
    if not gold.sql:
        return []
    reading = reading_of(gold.sql, gate)
    metrics = metrics_touched(reading, gate)
    axes = axes_touched(reading.resolved, gate)
    return [
        *metrics,
        *axes,
        *(gate.semantic.join_paths[name]
          for name in join_paths_touched(metrics, axes, gate.semantic)),
    ]


def same_result(
    gold: Sequence[Sequence[object]],
    actual: Sequence[Sequence[object]],
    tolerance: Decimal = RESULT_TOLERANCE,
) -> bool:
    """Whether two result sets are the same answer.

    The same rows, in any order, each of the same width, with numbers within `tolerance`
    of each other as a fraction of the larger and everything else equal as text. Order
    does not count because two statements that group the same way and sort differently
    have answered the same question; position inside a row does, because a breakdown's
    label and its number are not interchangeable.
    """
    if len(gold) != len(actual):
        return False
    for expected, got in zip(
        sorted(gold, key=_sort_key), sorted(actual, key=_sort_key)
    ):
        if len(expected) != len(got):
            return False
        if not all(_same_value(a, b, tolerance) for a, b in zip(expected, got)):
            return False
    return True


def _same_value(gold: object, actual: object, tolerance: Decimal) -> bool:
    """One value against another — numerically within tolerance, or equal as text."""
    a, b = _number(gold), _number(actual)
    if a is None or b is None:
        return str(gold) == str(actual)
    return abs(a - b) <= tolerance * max(abs(a), abs(b))


def _number(value: object) -> Decimal | None:
    """One value as a `Decimal`, or `None` if it is not a number.

    Through `str` rather than `float`, so a YAML float is read as the digits the file
    holds instead of as the nearest binary fraction to them.
    """
    if isinstance(value, bool) or value is None:
        return None
    try:
        return Decimal(str(value))
    except InvalidOperation:
        return None


def _sort_key(row: Sequence[object]) -> tuple[str, ...]:
    """One row as the text that puts two result sets in the same order.

    Numbers are written to `GOLD_SCALE`, which is the scale a gold result is written
    to, so a gold row and the row it stands for sort together. It orders rows; whether
    two of them are the same answer is `_same_value`'s question.
    """
    return tuple(
        f"{number:.{GOLD_SCALE}f}" if (number := _number(value)) is not None
        else str(value)
        for value in row
    )


def _here(path: Path) -> str:
    """The path as a reader would type it, relative to the repository root.

    A file outside the repository is named in full, because a loader is also pointed at
    a temporary directory by the tests that exercise its refusals.
    """
    if path.is_relative_to(REPO_ROOT):
        return path.relative_to(REPO_ROOT).as_posix()
    return path.as_posix()


def _member(path: Path, key: str, kind: type[StrEnum], value: object) -> StrEnum:
    """One field whose value is a member of a closed set, or raise naming the set."""
    try:
        return kind(str(value).strip())
    except ValueError:
        raise GoldQuestionError(
            f"{_here(path)}: {key} is {value!r} — it is one of "
            f"{[str(member) for member in kind]}"
        ) from None


def _rows(path: Path, value: object) -> tuple[tuple[object, ...], ...]:
    """The gold result as rows of values, frozen so a loaded question stays frozen."""
    if not isinstance(value, list) or not all(isinstance(row, list) for row in value):
        raise GoldQuestionError(
            f"{_here(path)}: result is {value!r} — it is a list of rows, each row a "
            f"list of the values one row of the answer holds"
        )
    return tuple(tuple(row) for row in value)


__all__ = [
    "GOLD_DIR",
    "GOLD_SCALE",
    "RESULT_TOLERANCE",
    "Expectation",
    "GoldQuestion",
    "GoldQuestionError",
    "PhrasingClass",
    "axes_touched",
    "filtered_columns",
    "join_paths_touched",
    "load_gold_questions",
    "metrics_touched",
    "read_gold_question",
    "reading_of",
    "relevant_entries",
    "same_result",
]
