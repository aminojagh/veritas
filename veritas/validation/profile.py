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

**The registered row entire, as of Sub-step 5.5.** A profile carries a **role**, its
**Restricted Columns** and its **permitted region**, which is the Glossary row's own
*"role and permitted region"* read literally. The third field arrived with the rule
that reads it, never before it: a field with no rule behind it would be a promise this
module cannot keep.

**The permitted region is a value of the `by region` axis, not a column and a string.**
That is
[R1](../../.claude/docs/plan/step-005-validation-gate.md#r1--the-access-profiles-predicate-and-the-slice-rule-ship-together-in-this-step--approved-and-widened-by-amino-2026-08-25):
the axis already registers `dim_client.client_region`, its grain and its three buckets,
and a profile carrying the column and its own list of regions would be a second
registration of both — the synonym Non-Negotiable 1 exists to prevent. So this module
names the **axis** and the Gate resolves the column and the route from the entry.
`ACCESS_AXIS` below is that name.

**What this enforcement is and is not** is stated where the rule that reads this module
lives, in `gate.py`'s module docstring, and it is
[DEBT-008](../../.claude/docs/debt-ledger.md#debt-008--the-access-control-story-promises-more-than-it-delivers)'s
own sentence rather than a paraphrase of it.
"""

from dataclasses import dataclass

# The certified axis an Access Profile's permitted region is a value of.
#
# A name rather than a column, for the reason in this module's docstring: the
# `by region` Dimension Definition registers `dim_client.client_region`, the grain, the
# three buckets **and** — since Sub-step 5.5 — the routes that reach it from each fact
# table. Everything the Gate needs to turn `permitted_region` into a predicate and into
# the joins that predicate requires is in that one entry, and naming the entry is how
# this module refers to all four without copying any of them.
#
# It is a constant rather than a field on the profile because there is one region axis
# and the Glossary row says so: *"role and permitted region"*. A profile free to pick
# its own axis would be a profile that could scope questions by something nobody
# certified as an access boundary.
ACCESS_AXIS = "by region"


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

    `permitted_region` has **no default**, unlike `restricted_columns`, and the
    asymmetry is the difference between the two fields. A profile that restricts no
    column is an identity that may see everything a query can project, which is a
    coherent thing to be; a profile that permits no region is an identity every
    statement is refused for, which is not an identity but a mistake. The Gate reads
    this as a value of the `ACCESS_AXIS` entry and refuses a value that axis does not
    certify — see `gate.access_predicate`, which is where the corpus is in reach.
    """

    role: str
    permitted_region: str
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
#
# **`EU` is a choice and not a finding.** It is one of the three buckets the `by region`
# axis registers, and which of the three this profile permits changes only which rows
# the analyst sees — the rule, the route and the predicate are identical for all three.
# A second role permitting a second region is a file edit rather than a field change,
# which is why the Step 005 plan files it as a scope boundary rather than as debt.
ANALYST = AccessProfile(
    role="analyst",
    permitted_region="EU",
    restricted_columns=frozenset({RestrictedColumn("dim_client", "client_name")}),
)
