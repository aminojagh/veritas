"""Renders each Semantic Entry as the text Retrieval is allowed to search.

[ADR-0001](../../.claude/docs/adr/0001-semantic-layer-as-the-retrieval-corpus.md)
fixes what may be retrieved over — Semantic Entries, and *"never over raw warehouse
schema or free-text documentation"*. This module is where that holds or fails,
because it is the one place that decides which of an entry's fields a search can
match on.

`SEARCHABLE_FIELDS` is that decision, one row per entry type. It is a whitelist: a
field it does not name cannot be matched, and every field left out holds SQL, a
Warehouse identifier, or a version rather than language. The whole entry still
travels with the hit — Grounding needs the expression and the route — so the
guarantee here is about what a question is *matched against*, not about what an
answer is built from.
"""

from veritas.semantic import (
    AmbiguousTerm,
    DimensionDefinition,
    JoinPath,
    MetricDefinition,
    SemanticEntry,
    SemanticLayer,
)

# Which fields of each entry type carry language a person might use, and therefore
# which a search may match. Parallel to the loader's `SQL_FIELDS`, and disjoint
# from it: a field that publishes SQL never publishes searchable text.
#
# A **Join Path has no row of its own** because it has nothing to contribute. Its
# name, its two tables and its `on` clause are Warehouse identifiers end to end, so
# any searchable text built from it would be schema in the corpus — the one thing
# ADR-0001 forbids. It is reached by reference instead: a Metric Definition's
# `join_paths` and a Dimension Definition's `routes` name the ones an answer needs,
# and no question ever names one in words.
SEARCHABLE_FIELDS: dict[type[SemanticEntry], tuple[str, ...]] = {
    MetricDefinition: (
        "name", "aliases", "description", "grain", "unit", "derives_from",
    ),
    AmbiguousTerm: ("name", "description", "disambiguates", "resolution"),
    DimensionDefinition: ("name", "description", "grain", "allowed_values"),
    JoinPath: (),
}


def searchable_text(entry: SemanticEntry) -> str:
    """Everything about one entry a search may match, as one block of text.

    `Gross Revenue` comes back as its name, then its aliases — `gross commission`,
    `revenue before rebates`, `commission income` — then its description, its grain
    and its unit, in the order `SEARCHABLE_FIELDS` lists them. A search that matches
    any one of them matches the entry, which is how *"how much did we bill in
    commission"* reaches a metric whose own name says neither word.

    One block rather than one field per source field, so a hit on the name counts
    for exactly what a hit on the unit counts for and nothing can weigh them apart.
    Whether anything should is
    [DEBT-027](../../.claude/docs/debt-ledger.md#debt-027--the-searchable-text-is-one-flat-field-so-a-name-match-cannot-outrank-a-description-match).

    A list-valued field contributes its items, and an empty one contributes
    nothing — `aliases: []` and a missing `reporting_currency` both leave no trace,
    so no entry carries a blank line standing in for a field it does not use.
    """
    parts: list[str] = []
    for field in SEARCHABLE_FIELDS[type(entry)]:
        value = getattr(entry, field)
        parts.extend([value] if isinstance(value, str) else value)
    return "\n".join(part for part in parts if part)


def searchable_entries(layer: SemanticLayer) -> list[dict[str, str]]:
    """Every Semantic Entry as a record a search index can be built over.

    Three keys, in the order a search uses them. `name` is identity — every
    reference in the corpus is by name, so it is what a hit is resolved back to an
    entry with. `kind` is what a search narrows on. `text` is the only key a search
    matches, and `searchable_text` above governs what reaches it.
    """
    return [
        {"name": entry.name, "kind": entry.kind, "text": searchable_text(entry)}
        for entry in layer.entries()
    ]
