"""The Access Profile — the identity a question is run as, and the columns it may not
see.

[`Access Profile`](../../.claude/docs/glossary.md#a-the-system) is registered as *"the
identity Veritas runs a question as — role and permitted region. Determines which rows
and columns the Validation Gate allows"*, and it lives here rather than in `semantic/`
because it is not a Semantic Entry: nothing retrieves it, and a question does not
choose it.

**The Restricted Columns are declared on the profile, not on the metrics that touch
them.** That is
[R3 of Step 004](../../.claude/docs/plan/step-004-semantic-layer.md#r3--restricted-columns-are-declared-in-the-access-profile-not-in-a-metric-definition--approved-by-amino-2026-08-21),
ruled before the code existed so this Sub-step would *"inherit a decision rather than an
omission"*: restriction is a property of the identity asking, and putting it on a Metric
Definition would make one column restricted or not depending on which entry happened to
retrieve it.

**Half of the registered row, in this Sub-step.** A profile carries a **role** and its
**Restricted Columns** here; the **permitted region** arrives with Sub-step 5.5, which
is where the Access Profile's predicate becomes a rule and where
[R1](../../.claude/docs/plan/step-005-validation-gate.md#r1--the-access-profiles-predicate-and-the-slice-rule-ship-together-in-this-step--approved-and-widened-by-amino-2026-08-25)
settles its shape — *"a permitted value of the `by region` axis"*, refused at load if
the axis does not certify it, rather than a second registration of the column and its
buckets. A field with no rule behind it would be a promise this module cannot keep.

**What this enforcement is and is not** is stated where the rule that reads this module
lives, in `gate.py`'s module docstring, and it is
[DEBT-008](../../.claude/docs/debt-ledger.md#debt-008--the-access-control-story-promises-more-than-it-delivers)'s
own sentence rather than a paraphrase of it.
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True, order=True)
class RestrictedColumn:
    """One column an Access Profile forbids from reaching a Grounded Answer.

    A **table and a column**, never a bare name, because a parse tree resolves every
    column to the table it came from and a rule that forbade the *name* would forbid it
    everywhere it appeared. Two tables are free to have a `name` column and for only one
    of them to be restricted. The spike held the same pair as an anonymous tuple; the
    Glossary registers
    [`Restricted Column`](../../.claude/docs/glossary.md#a-the-system) as a term, so
    here it is the term.

    `order=True` so a rule can name what it found in a stable order: a rejection
    explanation that lists two columns in a different order on each run is a different
    string for the same verdict.
    """

    table: str
    column: str

    def __str__(self) -> str:
        """`dim_client.client_name` — the way a person and a parse tree both spell it."""
        return f"{self.table}.{self.column}"


@dataclass(frozen=True, slots=True)
class AccessProfile:
    """The identity a question is run as.

    Frozen for the reason a `Validation Gate outcome` is: it is the thing a verdict was
    reached under, and an identity a rule could edit is an identity no verdict can be
    held to.

    `restricted_columns` is a `frozenset` because it is a set of things, membership is
    the only question ever asked of it, and a mutable default on a frozen dataclass is
    not one.
    """

    role: str
    restricted_columns: frozenset[RestrictedColumn] = frozenset()

    def restricted(self) -> list[RestrictedColumn]:
        """The Restricted Columns, in a stable order, for printing and for reporting."""
        return sorted(self.restricted_columns)


# The one Access Profile this slice declares.
#
# `dim_client.client_name` is the column: of the ten tables in
# [Glossary Section B](../../.claude/docs/glossary.md#b-the-warehouse) it is the only
# one naming a firm rather than describing a Trade, a Position or a price, which is what
# makes it the honest thing to restrict rather than a token. It is the column
# [Step 003's spike](../../.claude/docs/design/validation-feasibility.md) measured nine
# statement shapes against, and the spike keeps its own pinned copy of this declaration
# for the same reason it keeps three pinned expressions — see
# [R4 of Step 004](../../.claude/docs/plan/step-004-semantic-layer.md#r4--the-spike-is-pinned-to-the-corpus-rather-than-re-pointed-at-it--approved-by-amino-2026-08-21).
#
# **`role` is a value, not a registered term.** It names who is asking the way `EU` names
# a bucket of the `by region` axis: data carried by an entry, not a component of the
# system. Veritas has no user concept yet — the App Step is where one arrives — and
# registering a vocabulary of roles before anything reads a second one would be
# registering a guess.
ANALYST = AccessProfile(
    role="analyst",
    restricted_columns=frozenset({RestrictedColumn("dim_client", "client_name")}),
)
