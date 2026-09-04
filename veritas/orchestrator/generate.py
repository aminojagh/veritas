"""Builds the prompt out of retrieved Semantic Entries, and asks a model for SQL.

Steps 3 and 4 of the
[Target State's flow](../../.claude/docs/design/target-state.md#flow) — GROUND,
*"build the prompt from retrieved entries only. Metrics not retrieved are not
available"*, and GENERATE, *"SQL, composed from certified metric expressions"*.

**`GROUNDED_FIELDS` is where the grounding claim holds or fails.** It is the whitelist
of what a Semantic Entry may put in front of a model, one row per entry type, and no
field outside it reaches the prompt. Nothing else about the Warehouse does either: the
table and column names in the prompt are the ones the certified expressions and join
conditions are written with, which is
[ADR-0001](../../.claude/docs/adr/0001-semantic-layer-as-the-retrieval-corpus.md)'s
corpus rather than a schema dump.

**The model composes, it never defines.** Every expression, every join condition and
every certified filter in the statement it writes is text pasted out of an entry, and
the [Validation Gate](../validation/) is what decides whether it actually was. A
statement this module produces is a proposal.

**`PromptForm` is the one thing about the instruction that varies.** Two lengths of the
same contract, so that which of them Veritas uses is a measured choice rather than a
written one — `veritas/evaluation/generation.py` scores both. What surrounds them — the
identity, the entries, and what the rewrite step has already done to the question — is
the same under either.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType

from veritas.llm import LanguageModel, ModelCall, default_model, json_reply
from veritas.semantic import (
    AmbiguousTerm,
    DimensionDefinition,
    JoinPath,
    MetricDefinition,
    SemanticEntry,
)
from veritas.validation import ACCESS_AXIS, AccessProfile

# What each kind of Semantic Entry publishes to a model, and the whole of it. Parallel
# to `retrieval.SEARCHABLE_FIELDS`, `retrieval.REFERENCE_FIELDS` and the loader's
# `SQL_FIELDS`: one row per entry type, so a field added to an entry reaches the prompt
# by being named here rather than by existing.
#
# An Ambiguous Term grounds **nothing**. It is a claim about language, the rewrite step
# has already settled which meaning the question wants, and putting the word's other
# meanings in front of the generator invites it to re-open a question already answered.
GROUNDED_FIELDS: dict[type[SemanticEntry], tuple[str, ...]] = {
    MetricDefinition: (
        "description",
        "expression",
        "unit",
        "reporting_currency",
        "grain",
        "from_table",
        "join_paths",
        "filters",
        "date_column",
        "derives_from",
    ),
    JoinPath: ("from_table", "to_table", "on"),
    DimensionDefinition: ("description", "columns", "grain", "allowed_values", "routes"),
    AmbiguousTerm: (),
}

# What the model is told to do, ahead of the entries themselves. Every rule here is one
# the Validation Gate enforces, written as an instruction rather than as a hope: a
# generator told none of them writes statements the Gate refuses, and a Gate that
# refuses everything is a product that answers nothing.
GENERATION_RULES = """\
You write one DuckDB SELECT statement answering a question about a brokerage, using
only the certified entries listed below. You never define a metric, and you never
write arithmetic of your own.

Answer with one JSON object and nothing else:
  - {"sql": "<the statement>"} when the entries below can answer the question
  - {"sql": null, "why": "<one sentence>"} when they cannot

The statement has exactly this shape, and its clauses come in exactly this order:

  SELECT [<axis column> AS slice,] <metric expression> AS answer
  FROM <the metric's from_table>
  <one JOIN line per join path, see below>
  WHERE <each of the metric's filters> AND <the predicate that scopes the rows>
  [GROUP BY <axis column>]

Filling it in:
  - The metric expression is that metric's expression pasted character for character.
    Never rewrite it, reorder it, simplify it, or add or remove a cast.
  - A join path is written JOIN <its to_table> ON <its on>, with the condition pasted
    character for character. Always JOIN — never LEFT, RIGHT, FULL, OUTER or CROSS.
  - Write every join in the metric's own "joins to write" list, in that order, and
    never the same one twice. That list is already complete for a question with no
    breakdown in it.
  - A breakdown adds the joins that axis lists for this metric's from_table, after the
    metric's own, skipping any already written.
  - A breakdown and a period are both optional. A question that asks for neither is
    answered over every row the person asking may see, and that is a complete answer.
  - Break the answer down only by an axis that lists a route from this metric's
    from_table. An axis with no route from it cannot break that metric down.
  - A period may be filtered only on the metric's own date_column.
  - Write table names exactly as the entries write them, and never alias a table.
  - Never name a table or a column that does not appear in the entries below.
  - One statement. No semicolon, no Common Table Expression, no second top-level SELECT.

Refuse when no metric below computes what was asked, when no axis reaches the
breakdown that was asked for, or when the question is not about a number this list can
produce. Refusing is a correct answer; inventing SQL is not. A question that leaves the
period or the breakdown unsaid is not a reason to refuse.\
"""

# The same contract in a quarter of the words: the JSON reply, the statement's shape,
# and the three constraints the itemised rules above spell out. Every rule dropped is a
# consequence of one of the three, so this is the shorter statement of one instruction
# rather than a laxer one.
GENERATION_SHAPE = """\
You write one DuckDB SELECT statement answering a question about a brokerage, using
only the certified entries listed below.

Answer with one JSON object and nothing else:
  - {"sql": "<the statement>"} when the entries below can answer the question
  - {"sql": null, "why": "<one sentence>"} when they cannot

The statement has this shape:

  SELECT [<axis column> AS slice,] <metric expression> AS answer
  FROM <the metric's from_table>
  <one JOIN <to_table> ON <on> per join path the entries list, in the order listed>
  WHERE <each of the metric's filters> AND <the predicate that scopes the rows>
  [GROUP BY <axis column>]

Paste every metric expression and every join condition out of the entries character
for character. Never write arithmetic, a table or a column of your own. Refusing is a
correct answer; inventing SQL is not.\
"""

# What the question the model is handed has already had done to it. The rewrite step
# resolves the Ambiguous Terms a person said before anything searches for the question,
# and the model is given what that step produced rather than what was typed — see
# `rewrite.py`. It is stated apart from the rules so that both forms below carry it: it
# describes the input, not the instruction, and an arm that differed in both would
# measure two changes at once.
REWRITTEN_QUESTION = """\
The question has already had its ambiguous words resolved, so where the person typed
one it may now carry a certified metric's name instead, written over their own words
and reading a little oddly. Such a name says which metric to compute. It is never a
table, a column, or a value to filter on, and the words around it are still the
person's — they say which period and which breakdown was asked for.\
"""


class PromptForm(StrEnum):
    """How the generation instruction states what the model must do.

    One instruction, two lengths. Both are given the same entries, the same identity
    and the same `REWRITTEN_QUESTION`, so what an arm of the sweep in
    `veritas/evaluation/generation.py` varies is the rules and nothing else.
    """

    RULES = "rules"
    """Every constraint the Validation Gate enforces, itemised — `GENERATION_RULES`."""

    SHAPE = "shape"
    """The statement's shape and the three constraints under it — `GENERATION_SHAPE`."""


# Which text each form is. A dispatch table rather than a match, because the sweep that
# compares them iterates it — the shape `REWRITE_FORMS` has for the same reason.
PROMPT_FORMS = {
    PromptForm.RULES: GENERATION_RULES,
    PromptForm.SHAPE: GENERATION_SHAPE,
}

# Which form the flow writes. Measured rather than chosen: `veritas/evaluation/
# generation.py` scores both over the Gold Question Set, and the Step Review that set
# this line carries the numbers and the losing form.
DEFAULT_PROMPT_FORM = PromptForm.RULES


@dataclass(frozen=True, slots=True)
class Generated:
    """What the model made of the question: a statement, or a reason there is none.

    Exactly one of the two is set. `sql` is a proposal and nothing more — it has not
    been near the Validation Gate — and `refusal` is the model saying the entries it was
    shown cannot answer what was asked. `calls` is what asking cost, which is always
    one call: unlike the rewrite step, this one has no path that answers without a
    model.
    """

    sql: str = ""
    refusal: str = ""
    calls: tuple[ModelCall, ...] = ()


def field_text(value: object) -> str:
    """One entry field, on one line, in the shape the field has.

    An empty list is written as a word rather than as nothing, so a model reading
    *"filters:"* with a blank after it is never left to decide whether the field was
    empty or omitted. The two fields that hold Join Path names are not written by this
    — see `route_text`.
    """
    if isinstance(value, tuple):
        return ", ".join(value) or "none"
    return " ".join(str(value).split()) or "none"


def join_clause(join_path: JoinPath) -> str:
    """One Join Path as the line a statement carries it as."""
    return f"JOIN {join_path.to_table} ON {field_text(join_path.on)}"


def route_text(
    names: Sequence[str], join_paths: Mapping[str, JoinPath], indent: str
) -> str:
    """One route — a list of Join Path names — as the lines a statement carries.

    **Names are resolved into clauses here rather than left as a pointer**, and that is
    the difference between a prompt a model follows and one it improvises around: handed
    `join_paths: trade_to_account` and a block elsewhere holding that entry's fields, a
    model writes `JOIN trade_to_account ON trade_to_account.from_table = fct_trade` —
    the entry's *name* as a table — or skips the join altogether. Measured on
    `gpt-4o-mini`, both.

    A name with no entry among the grounded ones is written as the bare name. It is a
    hole rather than a route, and leaving it visible is what makes the statement fail at
    the Gate instead of quietly missing a join.
    """
    if not names:
        return " none"
    return "\n" + "\n".join(
        f"{indent}{join_clause(join_paths[name]) if name in join_paths else name}"
        for name in names
    )


def entry_text(
    entry: SemanticEntry,
    join_paths: Mapping[str, JoinPath] = MappingProxyType({}),
    access_route: Mapping[str, tuple[str, ...]] = MappingProxyType({}),
) -> str:
    """One Semantic Entry as the model reads it, or the empty string for one that
    grounds nothing.

    **Every field that holds a route is written as the joins it stands for.** A Join
    Path's `to_table` and `on` are never read apart, a Metric Definition's `join_paths`
    and a Dimension Definition's `routes` are never used except as clauses, and each is
    assembled here. Nothing is published that `GROUNDED_FIELDS` does not name.

    **A Metric Definition's join list also carries the joins the identity requires**,
    taken from `access_route` for that metric's own `from_table`. Every statement
    Veritas runs is scoped, so those joins are as mandatory as the metric's own and
    belong in the same list: a generator handed them as a separate rule writes one list
    and forgets the other, which is the failure this shape removes. They are the access
    axis's own `routes` — the same field the Validation Gate certifies them from — and a
    join a metric already names is not repeated.
    """
    grounded = GROUNDED_FIELDS[type(entry)]
    if not grounded:
        return ""
    head = f'{entry.kind} "{entry.name}" (version {entry.version})'
    if isinstance(entry, JoinPath):
        return "\n".join([
            head,
            f"  from_table: {entry.from_table}",
            f"  write: {join_clause(entry)}",
        ])

    lines = [head]
    for name in grounded:
        value = getattr(entry, name)
        if name == "join_paths":
            required = list(value) + [
                path
                for path in access_route.get(entry.from_table, ())
                if path not in value
            ]
            lines.append(
                f"  joins to write, in this order:"
                f"{route_text(required, join_paths, '    ')}"
            )
        elif name == "routes":
            lines.append("  reached by, from each from_table:")
            lines.extend(
                f"    from {table}:{route_text(names, join_paths, '      ')}"
                for table, names in value.items()
            )
            if not value:
                lines.append("    nowhere")
        else:
            lines.append(f"  {name}: {field_text(value)}")
    return "\n".join(lines)


def grounding(
    entries: Sequence[SemanticEntry],
    access_route: Mapping[str, tuple[str, ...]] = MappingProxyType({}),
) -> str:
    """The retrieved entries, in the order they were retrieved, as the prompt's corpus.

    Retrieval order is relevance order, so the entry a question most nearly names is the
    first the model reads. The Join Paths among them are the map every route in the
    other entries is written out of.
    """
    join_paths = {
        entry.name: entry for entry in entries if isinstance(entry, JoinPath)
    }
    return "\n\n".join(
        text
        for entry in entries
        if (text := entry_text(entry, join_paths, access_route))
    )


def access_axis_in(entries: Sequence[SemanticEntry]) -> DimensionDefinition:
    """The axis an Access Profile's permitted region is a value of, among the grounded
    entries.

    It has to be there, and this raises when it is not. A prompt that named a column the
    entries do not publish would be grounding the model in something it cannot check,
    and a prompt that left the scope out would ask for a statement the Gate refuses every
    time.
    """
    axis = next((entry for entry in entries if entry.name == ACCESS_AXIS), None)
    if not isinstance(axis, DimensionDefinition):
        raise ValueError(
            f"the {ACCESS_AXIS!r} axis is not among the grounded entries, so no "
            f"statement written from them can be scoped to the identity asking"
        )
    return axis


def scope_text(axis: DimensionDefinition, access_profile: AccessProfile) -> str:
    """What the model is told about the identity the question is being asked as.

    The predicate is built from the axis's own `columns` and the profile's own
    `permitted_region`, so there is no second declaration of either: the Gate builds the
    same predicate from the same two fields and compares it canonically. The joins that
    reach the column are not here — they are in each metric's own join list, where a
    generator writing that metric cannot miss them.
    """
    return (
        f"The person asking has the role {access_profile.role!r} and may see "
        f"{access_profile.permitted_region} only, so the WHERE clause of every "
        f"statement must require\n\n"
        f"  {axis.columns[0]} = '{access_profile.permitted_region}'\n\n"
        f"whether or not the question says anything about it. The joins that reach that "
        f"column are already in each metric's join list below."
    )


def generation_instruction(
    entries: Sequence[SemanticEntry],
    access_profile: AccessProfile,
    form: PromptForm = DEFAULT_PROMPT_FORM,
) -> str:
    """The system instruction: the rules, what the question has had done to it, the
    identity, then the entries themselves."""
    axis = access_axis_in(entries)
    return "\n\n".join([
        PROMPT_FORMS[form],
        REWRITTEN_QUESTION,
        scope_text(axis, access_profile),
        "Certified entries:",
        grounding(entries, axis.routes),
    ])


def generate(
    question: str,
    entries: Sequence[SemanticEntry],
    access_profile: AccessProfile,
    model: LanguageModel | None = None,
    form: PromptForm = DEFAULT_PROMPT_FORM,
) -> Generated:
    """Ask a model for the statement these entries can answer this question with.

    A reply with no statement in it is read as a refusal, and one that gives no reason
    is given the only honest one there is. A reply that is not a JSON object at all
    raises through `json_reply`: that is the provider failing, not the question being
    unanswerable, and the two must not arrive at a caller as the same thing.
    """
    model = default_model() if model is None else model
    reply = model.complete(
        generation_instruction(entries, access_profile, form),
        question,
        json_object=True,
    )
    written = json_reply(reply.text)
    sql = written.get("sql")
    if isinstance(sql, str) and sql.strip():
        return Generated(sql=sql.strip(), calls=(reply.call,))
    why = written.get("why")
    return Generated(
        refusal=" ".join(why.split())
        if isinstance(why, str) and why.strip()
        else "the model wrote no statement and gave no reason",
        calls=(reply.call,),
    )
