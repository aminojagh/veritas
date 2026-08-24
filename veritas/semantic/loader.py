"""Reads the Semantic Layer — the certified registry Veritas retrieves over.

The Semantic Layer is **data**, so it lives at `semantic/` in the repository root
rather than inside this package: Glossary Section A registers that directory as its
home, and hand-written YAML is what
[EXT-003](../../.claude/docs/extension-register.md#ext-003--metric-authoring-at-scale)
calls *"not merely acceptable"* but *"better: inspectable, diffable, and reviewable
in a pull request"* at this scale. This package is the code that reads it, named for
the component the way `veritas/warehouse/` is named for the Warehouse it reaches.

**Nothing here executes SQL, and that is a constraint rather than an omission.**
[C1](../../.claude/docs/design/validation-feasibility.md#c1--a-metric-definition-publishes-a-form-the-orchestrator-pastes)
says a Metric Definition *"publishes a form the Orchestrator pastes"* — so the
expression is text this module hands over untouched, and assembling a query around
it belongs to whatever pastes it. A loader that built the query would be re-deriving
between what a reviewer reads in the file and what the engine runs, which is the one
thing C1 exists to remove.

**The dataclass field lists below are the file format.** There is no second copy of
the field names anywhere: a key the format does not name fails to load instead of
being silently ignored, and a key the format requires and a file omits fails by
name. That is also the *only* thing pinning those key names down — no check reads
YAML keys against the Glossary, which the Sub-step 4.1 review states plainly.
"""

import re
from dataclasses import MISSING, dataclass, fields
from pathlib import Path

import yaml

SEMANTIC_PACKAGE_DIR = Path(__file__).resolve().parent
REPO_ROOT = SEMANTIC_PACKAGE_DIR.parent.parent

SEMANTIC_DIR = REPO_ROOT / "semantic"

# The words that are `true` or `false` and no others.
#
# PyYAML implements YAML 1.1, where `on`, `off`, `yes`, `no`, `y` and `n` are all
# booleans. A Join Path's join condition is written under the key `on` — SQL's own
# word for it, and the one the format publishes — and YAML 1.1 reads that key as
# the boolean True, so the field vanishes and an unnamed True appears beside it.
# YAML 1.2, the current specification, removed those spellings for exactly this
# reason; Go's yaml.v3 and JavaScript's js-yaml already read them as text, so this
# makes the files *more* portable rather than less.
#
# Quoting the key in the file would fix that one key and nothing else. The values
# are where this gets expensive later: a Dimension Definition's allowed values are
# domain text, and YAML 1.1 reads `no`, `on`, `y` and `n` as booleans in any casing
# — Norway's country code, Ontario's province code, and both halves of every yes/no
# flag ever written. Silently turning one of those into False is a certified axis
# that lies, which is the failure Sub-step 4.5's check exists to catch.
YAML_12_BOOLEANS = re.compile(r"^(?:true|True|TRUE|false|False|FALSE)$")


class SemanticEntryLoader(yaml.SafeLoader):
    """`yaml.SafeLoader` with YAML 1.2's booleans instead of YAML 1.1's."""


SemanticEntryLoader.yaml_implicit_resolvers = {
    first_character: [
        (tag, pattern)
        for tag, pattern in resolvers
        if tag != "tag:yaml.org,2002:bool"
    ]
    for first_character, resolvers in yaml.SafeLoader.yaml_implicit_resolvers.items()
}
SemanticEntryLoader.add_implicit_resolver(
    "tag:yaml.org,2002:bool", YAML_12_BOOLEANS, list("tTfF")
)


class SemanticEntryError(ValueError):
    """A file under `semantic/` that cannot be read as the entry it claims to be.

    Raised rather than collected, because every caller of this module wants the
    same thing from a malformed entry: to stop. A Semantic Entry that half-loads is
    worse than one that does not load, since retrieval would then serve it.
    """


@dataclass(frozen=True)
class SemanticEntry:
    """One retrievable document in the Semantic Layer.

    The three fields every kind of entry carries. `version` is what Lineage
    records, so an answer can name the version of each entry that produced it;
    `kind` is what the file says it is, and is checked against the directory it was
    found in so a Metric Definition cannot hide in `semantic/joins/`.
    """

    name: str
    version: int
    kind: str


@dataclass(frozen=True)
class MetricDefinition(SemanticEntry):
    """A named, versioned, certified computation over the Warehouse.

    The fields past `SemanticEntry`'s three are the Glossary's own definition —
    *"its SQL expression, grain, filters, units, and the aliases people use for
    it"* — plus the two
    [C2](../../.claude/docs/design/validation-feasibility.md#c2--a-metric-definition-carries-its-join-path-and-its-date-predicate)
    requires, because *"a certified expression pins down the arithmetic and not the
    rows it is computed over"*:

      `from_table`  the table the query starts at. `Trade Count` joins nothing, so
                    nothing else in the entry would name a table.
      `join_paths`  the Join Path entries the expression is computed across, in the
                    order they are joined. A route this file does not name is a
                    route the Orchestrator would have to invent.
      `filters`     the certified predicates, ANDed into the WHERE. `Realised P&L`
                    shares a table with three other movement types and the filter
                    is the whole difference between them.
      `date_column` the column a period filter keys on. Trade Date and Settlement
                    Date are a Glossary Section C pair precisely because choosing
                    between them moves the number.

    `expression` is the text an Orchestrator pastes verbatim, and `reporting_currency`
    is the currency it comes back in — the conversion is *inside* the expression and
    the Join Path, never applied afterwards by something that read this field. It is
    the one field a file may omit, and omitting it is a claim: `Reporting Currency` is
    registered as something *"every **monetary** metric must state"*, so a count and a
    quantity must not state one. `.claude/scripts/check_semantic_layer.py` checks that
    biconditional against `unit`; nothing here can, because a loader reads one file and
    this is a rule about what a file says about itself.

    **`derives_from` names the Certified Metrics whose value is added to this
    metric's own expression**, which is how `Account Value` is *"Cash Balance plus
    all Positions marked to market"* without restating the certified Cash Balance
    expression. It is narrower than the word suggests — see
    [R8](../../.claude/docs/plan/step-004-semantic-layer.md#r8--the-route-a-metric-definition-carries--decided-in-sub-step-42-under-aminos-ruling-of-2026-08-22).

    The shape of the four fields above is R8's, decided in Sub-step 4.2 after reading
    all nine metrics against the shape Sub-step 4.1 published.
    """

    description: str
    expression: str
    grain: str
    unit: str
    from_table: str
    join_paths: tuple[str, ...]
    filters: tuple[str, ...]
    date_column: str
    aliases: tuple[str, ...]
    derives_from: tuple[str, ...]
    # Last because a dataclass field with a default must follow every field without
    # one. The file writes it where the format writes it, next to `unit`, since a
    # mapping has no order a reader is obliged to honour.
    reporting_currency: str = ""


@dataclass(frozen=True)
class JoinPath(SemanticEntry):
    """A certified route between two Warehouse tables, so the model never invents one.

    `on` is the join condition as written, including any literal in it. It is not a
    template with a placeholder for the Reporting Currency: C1 forbids a form
    something else has to fill in, so a second Reporting Currency is a second file
    rather than a substitution.
    """

    from_table: str
    to_table: str
    on: str


@dataclass(frozen=True)
class AmbiguousTerm(SemanticEntry):
    """A word users genuinely say that resolves to more than one Certified Metric.

    [Glossary Section D](../../.claude/docs/glossary.md#d-ambiguous-terms) is the
    registry of these — *"words users genuinely say that are **not** metrics"*,
    which Veritas *"must resolve ... before generating SQL — never guess silently"*.
    This entry type is that sentence made retrievable, and it is the one
    [ADR-0001](../../.claude/docs/adr/0001-semantic-layer-as-the-retrieval-corpus.md)
    rejected schema retrieval over: a table listing cannot represent *"the one fact
    that matters: that 'revenue' has two certified meanings"*.

      `disambiguates` the Certified Metrics the word could mean, by `name` — the
                      field [EXT-005](../../.claude/docs/extension-register.md#ext-005--semantic-layer-coherence-checks)
                      chose for this edge. Two or more, because a word with one
                      meaning is not ambiguous.
      `resolution`    what Veritas does about it, from Section D's own third
                      column. Four of the five rows say *"Ask"* and one says
                      *"Ask, unless the question names one"*, and the difference is
                      a rule the Orchestrator acts on rather than a note.

    **It publishes no SQL, and that is the point.** An Ambiguous Term is a claim
    about *language* — it can be wrong while every expression in the corpus is
    right, and its fix is in the Glossary rather than in a query. `SQL_FIELDS` below
    therefore has no row for it, and the two readers that ask get nothing back.

    There is no `aliases` field, and that is a deferral rather than an omission —
    see the Sub-step 4.4 review.
    """

    description: str
    disambiguates: tuple[str, ...]
    resolution: str


# Directory -> the `kind` files in it must declare, and the type they load as. The
# directory names are Glossary Section A's own homes: `semantic/metrics/`,
# `semantic/joins/`, `semantic/ambiguous/`. This mapping is deliberately not a scan
# of the tree — a file in a directory it does not know fails to load rather than
# being skipped, which is why Sub-step 4.4 had to come here and add its row rather
# than dropping five files into a new directory and having them silently ignored.
# `semantic/dimensions/` is the one remaining entry type and stays absent on the
# same terms, so Sub-step 4.5 comes here too.
ENTRY_KINDS: dict[str, tuple[str, type[SemanticEntry]]] = {
    "metrics": ("metric", MetricDefinition),
    "joins": ("join_path", JoinPath),
    "ambiguous": ("ambiguous_term", AmbiguousTerm),
}

# Fields whose value is a list of strings rather than one string. Read off the
# annotation would be tidier and is not worth the reflection: five names, in one
# place, next to the dataclasses that declare them.
STRING_LISTS = frozenset({
    "aliases", "derives_from", "join_paths", "filters", "disambiguates"
})

# Fields whose value is SQL — text pasted into a query and therefore text that
# reaches the engine. Here rather than in whatever happens to need it, for the
# reason the dataclasses above are the file format: a reader that decides for
# itself which fields hold SQL is a second copy of the format, and the two go on
# disagreeing after one of them is updated. Two readers already ask —
# `check_warehouse.py`'s dialect scan and `check_language.py`'s keyword
# derivation — and the Orchestrator that assembles a query will be the third.
SQL_FIELDS: dict[type[SemanticEntry], tuple[str, ...]] = {
    MetricDefinition: ("expression", "filters"),
    JoinPath: ("on",),
}


@dataclass(frozen=True)
class SemanticLayer:
    """The certified registry, loaded.

    Three of the four entry types are here. Dimension Definitions are Sub-step 4.5,
    and this class gains a mapping each time — which is an addition rather than a
    change, because nothing keys off the absence. Sub-step 4.4 adding
    `ambiguous_terms` is that prediction holding: no existing field moved and no
    caller of the other two noticed.

    Entries are held by their `name` and not by their filename, because `name` is
    what every reference in the corpus uses: a Metric Definition names its Join Path
    by name, and an Ambiguous Term names the Certified Metrics it disambiguates
    between the same way. One `name` may be claimed once across the **whole** tree
    rather than once per kind, which is what makes an Ambiguous Term named after a
    Certified Metric fail to load — Section D's words are *"words users genuinely
    say that are **not** metrics"*, and the corpus enforces that by construction
    instead of by a check.
    """

    metrics: dict[str, MetricDefinition]
    join_paths: dict[str, JoinPath]
    ambiguous_terms: dict[str, AmbiguousTerm]

    def entries(self) -> list[SemanticEntry]:
        """Every entry, whatever its kind, in the order the files were read."""
        return [
            *self.metrics.values(),
            *self.join_paths.values(),
            *self.ambiguous_terms.values(),
        ]


def entry_files(root: Path = SEMANTIC_DIR) -> list[Path]:
    """Every file under `semantic/`, alphabetically.

    Deliberately not `*.yaml`: a file the tree holds and this loader does not
    recognise is a finding, not something to walk past. The Semantic Layer is small
    and hand-written, and a stray `gross_revenue.yml` that retrieval never sees is
    exactly the kind of quiet hole this project keeps finding.
    """
    return sorted(path for path in root.rglob("*") if path.is_file())


def read_entry(path: Path) -> SemanticEntry:
    """Read one file as the Semantic Entry its directory says it is.

    Every failure is raised with the file named, because the caller is a person
    editing YAML and the useful message says which key in which file.
    """
    directory = path.parent.name
    if path.suffix != ".yaml" or directory not in ENTRY_KINDS:
        raise SemanticEntryError(
            f"{_here(path)}: not a Semantic Entry — expected a .yaml file in one of "
            f"{sorted(ENTRY_KINDS)}"
        )
    declared_kind, entry_type = ENTRY_KINDS[directory]

    document = yaml.load(path.read_text(), Loader=SemanticEntryLoader)
    if not isinstance(document, dict):
        raise SemanticEntryError(
            f"{_here(path)}: reads as {type(document).__name__}, not a mapping of "
            f"fields"
        )

    expected = {entry_field.name for entry_field in fields(entry_type)}
    # A field carrying a default is one the format lets a file leave out, and
    # `reporting_currency` is the only one. Everything else missing is an error
    # named after the key, which is what a person editing YAML needs to read.
    optional = {
        entry_field.name
        for entry_field in fields(entry_type)
        if entry_field.default is not MISSING
    }
    missing = sorted(expected - optional - set(document))
    unknown = sorted(set(document) - expected)
    if missing or unknown:
        raise SemanticEntryError(
            f"{_here(path)}: "
            + " and ".join(
                part for part in (
                    f"missing required field(s) {missing}" if missing else "",
                    f"has field(s) {unknown} that a {declared_kind} does not have"
                    if unknown else "",
                ) if part
            )
        )

    if document["kind"] != declared_kind:
        raise SemanticEntryError(
            f"{_here(path)}: declares kind {document['kind']!r} but sits in "
            f"{directory}/, where every entry is a {declared_kind!r}"
        )
    if not isinstance(document["version"], int):
        raise SemanticEntryError(
            f"{_here(path)}: version is {document['version']!r} — Lineage records a "
            f"version number, so it must be an integer"
        )

    return entry_type(**{
        key: (
            _strings(path, key, value) if key in STRING_LISTS
            else _text(path, key, value)
        )
        for key, value in document.items()
    })


def load_semantic_layer(root: Path = SEMANTIC_DIR) -> SemanticLayer:
    """Read the whole tree, or raise on the first file that will not load.

    Cross-entry coherence is not checked here — that a Metric Definition's
    `join_path` names a Join Path that exists, that an Ambiguous Term names metrics
    that exist. Those are claims about the corpus rather than about a file, they are
    what `.claude/scripts/check_semantic_layer.py` is for, and one of them is
    [EXT-005](../../.claude/docs/extension-register.md#ext-005--semantic-layer-coherence-checks)'s
    fourth rule, built in Sub-step 4.4.

    The one cross-entry rule that *is* here is name uniqueness, because it is what
    makes `name` usable as the key of the three mappings below at all.
    """
    metrics: dict[str, MetricDefinition] = {}
    join_paths: dict[str, JoinPath] = {}
    ambiguous_terms: dict[str, AmbiguousTerm] = {}
    seen: dict[str, Path] = {}

    for path in entry_files(root):
        entry = read_entry(path)
        if entry.name in seen:
            raise SemanticEntryError(
                f"{_here(path)}: a second entry named {entry.name!r} — "
                f"{_here(seen[entry.name])} already claims that name, and every "
                f"reference in the corpus is by name"
            )
        seen[entry.name] = path
        match entry:
            case MetricDefinition():
                metrics[entry.name] = entry
            case JoinPath():
                join_paths[entry.name] = entry
            case AmbiguousTerm():
                ambiguous_terms[entry.name] = entry

    return SemanticLayer(
        metrics=metrics, join_paths=join_paths, ambiguous_terms=ambiguous_terms
    )


def sql_fields(entry: SemanticEntry) -> list[tuple[str, str]]:
    """Every piece of SQL one entry publishes, as (which field, the SQL).

    The label is the field name, and the certified filters are numbered from one
    because a Metric Definition may carry several and *which* one a reader is being
    told about is the whole use of the label.

    An entry type absent from `SQL_FIELDS` publishes no SQL and returns nothing.
    That is how Ambiguous Terms arrived in Sub-step 4.4 — one names Certified
    Metrics, which is a claim about language rather than text a query pastes — and
    it is why adding the type cost the two readers nothing: they ask this function
    and get an empty list. Dimension Definitions arrive on the same terms.
    """
    published: list[tuple[str, str]] = []
    for field in SQL_FIELDS.get(type(entry), ()):
        value = getattr(entry, field)
        if isinstance(value, str):
            published.append((field, value))
            continue
        published.extend(
            (f"{field.removesuffix('s')} {position}", sql)
            for position, sql in enumerate(value, start=1)
        )
    return published


def _here(path: Path) -> str:
    """The path as a reader would type it, relative to the repository root."""
    return path.relative_to(REPO_ROOT).as_posix()


def _text(path: Path, key: str, value: object) -> object:
    """One scalar field, with the whitespace YAML's block styles add stripped off.

    `version` passes through untouched: it is the one field that is not text.

    Stripping the ends is normalisation and not re-derivation. A folded scalar —
    the `>` that `description` and a Join Path's `on` are written with — always
    ends in a newline, and nothing inside the string is touched, so the pasteable
    form C1 requires survives exactly. `expression` is written as a quoted scalar
    and has nothing to strip.
    """
    if key == "version":
        return value
    if not isinstance(value, str):
        raise SemanticEntryError(
            f"{_here(path)}: {key} is {value!r}, and every field but version and "
            f"the list fields is text"
        )
    return value.strip()


def _strings(path: Path, key: str, value: object) -> tuple[str, ...]:
    """One list-valued field, as a tuple so a loaded entry stays frozen.

    Three of the five hold names — `join_paths`, `derives_from`, `disambiguates` —
    and two hold text a person wrote, `aliases` and `filters`. Whether the names
    resolve to entries that exist is a claim about the corpus rather than about this
    file, and is checked where the other cross-entry claims are.
    """
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise SemanticEntryError(
            f"{_here(path)}: {key} is {value!r} — it is a list, written `[]` when "
            f"it is empty"
        )
    return tuple(item.strip() for item in value)
