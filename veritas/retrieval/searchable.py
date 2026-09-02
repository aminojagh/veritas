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
#
# An **Ambiguous Term's `aliases` are left out** though a Metric Definition's are in,
# because nothing here would match on one: the rewrite step reads those spellings
# before any search runs, and a question that says one arrives already asked back
# about or already carrying the certified meaning it resolved to. Measured as well as
# argued: indexing them moves a fixed-set question out of the vector search's top
# five, and `tests/test_retrieval.py` is what says so.
SEARCHABLE_FIELDS: dict[type[SemanticEntry], tuple[str, ...]] = {
    MetricDefinition: (
        "name", "aliases", "description", "grain", "unit", "derives_from",
    ),
    AmbiguousTerm: ("name", "description", "disambiguates", "resolution"),
    DimensionDefinition: ("name", "description", "grain", "allowed_values"),
    JoinPath: (),
}

# Every field any entry type publishes, once, in the order the table above reaches
# them. It is what a per-field index carries a column for, so every record publishes
# all nine and a field an entry type does not have is empty rather than absent —
# `unit` is a metric's, `resolution` an Ambiguous Term's, `allowed_values` an axis's,
# and the index needs one shape of record for all three.
TEXT_FIELDS: tuple[str, ...] = tuple(
    dict.fromkeys(
        field for published in SEARCHABLE_FIELDS.values() for field in published
    )
)


def searchable_fields(entry: SemanticEntry) -> dict[str, str]:
    """Each field a search may match on this entry, kept apart.

    One key per `TEXT_FIELDS`, so two entries of different types are the same shape
    of record. A list-valued field contributes its items one per line, and a field
    this entry type does not publish — or holds nothing in — is the empty string:
    `aliases: []` and a missing `reporting_currency` both leave no trace, so no entry
    carries a blank line standing in for a field it does not use.
    """
    published = SEARCHABLE_FIELDS[type(entry)]
    fields: dict[str, str] = {}
    for field in TEXT_FIELDS:
        value = getattr(entry, field) if field in published else ""
        parts = [value] if isinstance(value, str) else list(value)
        fields[field] = "\n".join(part for part in parts if part)
    return fields


def searchable_text(entry: SemanticEntry) -> str:
    """Everything about one entry a search may match, as one block of text.

    `Gross Revenue` comes back as its name, then its aliases — `gross commission`,
    `revenue before rebates`, `commission income` — then its description, its grain
    and its unit, in the order `SEARCHABLE_FIELDS` lists them. A search that matches
    any one of them matches the entry, which is how *"how much did we bill in
    commission"* reaches a metric whose own name says neither word.

    One block rather than one field per source field, so a hit on the name counts
    for exactly what a hit on the unit counts for and nothing can weigh them apart.
    The alternative is `searchable_fields` above, kept apart and indexed apart, and
    which of the two Retrieval scores better is
    [DEBT-027](../../.claude/docs/debt-ledger.md#debt-027--the-searchable-text-is-one-flat-field-so-a-name-match-cannot-outrank-a-description-match).
    """
    return "\n".join(text for text in searchable_fields(entry).values() if text)


def searchable_entries(layer: SemanticLayer) -> list[dict[str, str]]:
    """Every Semantic Entry as a record a search index can be built over.

    Three keys either index needs, and then one per `TEXT_FIELDS`. `name` is
    identity — every reference in the corpus is by name, so it is what a hit is
    resolved back to an entry with. `kind` is what a search narrows on. `text` is the
    whole of what a flat index matches; the nine fields beside it are the same words
    split the way a per-field index matches them.

    The identity keys are written **after** the fields, so `name` is the entry's name
    even for a Join Path, which publishes no searchable field and would otherwise
    have its identity overwritten by the empty string standing in for one.
    """
    return [
        {
            **searchable_fields(entry),
            "name": entry.name,
            "kind": entry.kind,
            "text": searchable_text(entry),
        }
        for entry in layer.entries()
    ]
