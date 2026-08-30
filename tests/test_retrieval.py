"""What Retrieval may search: every Semantic Entry, and no Warehouse schema.

The corpus claim of
[ADR-0001](../.claude/docs/adr/0001-semantic-layer-as-the-retrieval-corpus.md),
checked rather than asserted in prose. Schema identifiers come from the built
Warehouse, so the check reads the same names the engine holds.
"""

import re
from dataclasses import fields

from veritas.retrieval import SEARCHABLE_FIELDS, searchable_entries
from veritas.semantic import ENTRY_KINDS, SQL_FIELDS, JoinPath, entry_files

# Warehouse columns spelled as a single word that is also the domain's own word for
# the thing. `Commission`, `Fee` and `Rebate` are registered Glossary terms; `amount`
# and `quantity` are ordinary English a description cannot avoid — "less Rebate and
# pass-through Fee", "by exactly that amount". A check that banned these would ban
# the vocabulary the corpus exists to publish, so they are the one thing
# `test_corpus_carries_no_table_or_column_text` cannot cover.
#
# What that costs, inside the entries this applies to: a *new* entry could write one
# of these five words meaning the column rather than the concept and nothing here
# would notice. Every other Warehouse identifier — all ten tables, every qualified
# `table.column`, and every column whose name carries an underscore — is banned
# outright.
DOMAIN_WORDS_ALSO_COLUMNS = {"amount", "commission", "fee", "quantity", "rebate"}


def test_corpus_holds_every_semantic_entry(root, semantic):
    """One record per file under `semantic/`, in the order the layer holds them."""
    records = searchable_entries(semantic)
    assert [record["name"] for record in records] == [
        entry.name for entry in semantic.entries()
    ]
    assert len(records) == len(entry_files(root / "semantic"))


def test_corpus_makes_every_alias_searchable(semantic):
    """Every alias a Metric Definition publishes is text a search can match."""
    seen = 0
    for record, entry in zip(searchable_entries(semantic), semantic.entries()):
        for alias in getattr(entry, "aliases", ()):
            seen += 1
            assert alias in record["text"], f"{entry.name}: alias {alias!r} not searchable"
    assert seen, "no aliases in the corpus — this check proved nothing"


def test_corpus_carries_no_table_or_column_text(semantic, warehouse):
    """No Warehouse table, qualified column, or underscored column name is matchable."""
    # Three shapes of identifier, all banned as a substring anywhere in the text. The
    # underscore is what earns the outright ban: `cash_balance`, `market_price` and
    # `movement_type` are spellings only a schema uses, so a hit on one is the schema
    # leaking and never prose. Single-word columns are deliberately left out here —
    # banning `fee` as a substring would ban the English word, and every mention of it
    # inside "coffee" besides. The next check covers those instead.
    columns = warehouse.columns_by_table()
    identifiers = (
        set(columns)
        | {f"{table}.{column}" for table, held in columns.items() for column in held}
        | {column for held in columns.values() for column in held if "_" in column}
    )
    assert identifiers, "no schema read — this check proved nothing"
    for record in searchable_entries(semantic):
        text = record["text"].lower()
        found = sorted(name for name in identifiers if name in text)
        assert not found, f"{record['name']}: searchable text carries {found}"


def test_corpus_shares_only_domain_words_with_the_schema(semantic, warehouse):
    """The single-word overlap with the schema is the domain's vocabulary, and no more."""
    # The columns the check above cannot ban: no underscore, so the name is also an
    # ordinary word. Two consequences. Matching is on a word boundary, not a substring,
    # so "coffee" is not a `fee`. And the finding is judged against
    # `DOMAIN_WORDS_ALSO_COLUMNS` rather than banned outright, which makes this a
    # tripwire on the *schema* growing: the day a one-word column arrives that is not
    # already the domain's own word, the first entry to write it fails here.
    one_word = {
        column
        for held in warehouse.columns_by_table().values()
        for column in held
        if "_" not in column
    }
    records = searchable_entries(semantic)
    found = {
        column
        for column in one_word
        for record in records
        if re.search(rf"\b{column}\b", record["text"].lower())
    }
    assert found <= DOMAIN_WORDS_ALSO_COLUMNS, (
        f"searchable text carries schema-only word(s) "
        f"{sorted(found - DOMAIN_WORDS_ALSO_COLUMNS)}"
    )


def test_corpus_leaves_join_paths_unsearchable(semantic):
    """A Join Path is reached by reference; every other entry carries text."""
    joins = 0
    for record, entry in zip(searchable_entries(semantic), semantic.entries()):
        if isinstance(entry, JoinPath):
            joins += 1
            assert record["text"] == "", f"{entry.name}: a Join Path publishes no text"
        else:
            assert record["text"], f"{entry.name}: nothing to search on"
    assert joins, "no Join Paths in the corpus — this check proved nothing"


def test_corpus_searches_no_sql_field():
    """Every entry type is classified, its fields are real, and none of them is SQL."""
    assert set(SEARCHABLE_FIELDS) == {entry_type for _, entry_type in ENTRY_KINDS.values()}
    for entry_type, searchable in SEARCHABLE_FIELDS.items():
        declared = {field.name for field in fields(entry_type)}
        assert set(searchable) <= declared, f"{entry_type.__name__}: unknown field(s)"
        assert not set(searchable) & set(SQL_FIELDS.get(entry_type, ())), (
            f"{entry_type.__name__}: a field that publishes SQL is searchable"
        )

