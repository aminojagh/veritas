"""What Retrieval may search, and what it returns.

Two claims. The corpus claim of
[ADR-0001](../.claude/docs/adr/0001-semantic-layer-as-the-retrieval-corpus.md) —
Semantic Entries and no Warehouse schema — checked rather than asserted in prose,
with the schema identifiers read from the built Warehouse so the check sees the
same names the engine holds. And the search claim: every strategy finds the entry
a person would name, and what comes back carries the entries those hits reference.
"""

import re
from dataclasses import fields

import pytest

from veritas.retrieval import (
    REFERENCE_FIELDS,
    SEARCHABLE_FIELDS,
    RetrievalStrategy,
    references,
    searchable_entries,
)
from veritas.semantic import (
    ENTRY_KINDS,
    SQL_FIELDS,
    JoinPath,
    MetricDefinition,
    entry_files,
)

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


def test_corpus_makes_every_metric_alias_searchable(semantic):
    """Every alias a Metric Definition publishes is text a search can match.

    A Metric Definition's, and deliberately not every entry type's: an Ambiguous
    Term's `aliases` are spellings the rewrite step matches before any search runs,
    and `SEARCHABLE_FIELDS` says why they are not indexed. This scanned whatever
    carried the field until Sub-step 7.2 gave a second entry type one.
    """
    seen = 0
    for record, entry in zip(searchable_entries(semantic), semantic.entries()):
        if not isinstance(entry, MetricDefinition):
            continue
        for alias in entry.aliases:
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



# The fixed question set: a question as a person would type it, and the one entry
# they would name as the answer's source. Written against the corpus rather than
# sampled from users, so it proves the search reaches an entry through words the
# entry does not itself contain — never how well Veritas answers. That is the Gold
# Question Set's job, and this set is not it.
QUESTIONS = [
    ("how much did we bill in commission before any rebates", "Gross Revenue"),
    ("what did the broker actually keep after paying rebates and fees", "Net Revenue"),
    ("how much uninvested money is sitting in the accounts", "Cash Balance"),
    ("what are our clients' portfolios worth in total", "Account Value"),
    ("how many deals did we execute last month", "Trade Count"),
    ("what was the turnover of everything traded last quarter", "Traded Notional"),
    ("what profit have we locked in on closed positions", "Realised P&L"),
    ("what is the paper gain on holdings we still own", "Unrealised P&L"),
    ("how much did the quantity held move over the week", "Position Change"),
    ("break the answer down by where the client is based", "by region"),
    ("split it by whether it is an equity or a fund", "by instrument type"),
    ("what was our revenue last quarter", "revenue"),
    ("how much does client 42 have", "how much does X have"),
    ("what is our P&L", "P&L"),
    ("how much volume did we do", "volume"),
]

# A question about nothing in the domain. Its point is the difference between the
# two searches: a term search that shares no word with any entry returns nothing,
# and a vector search always returns its nearest neighbours however far away they
# are. Everything downstream of Retrieval has to survive both.
OFF_TOPIC = "photosynthesis in tropical rainforest canopies"


@pytest.mark.parametrize("strategy", list(RetrievalStrategy))
@pytest.mark.parametrize("question,expected", QUESTIONS, ids=[q for q, _ in QUESTIONS])
def test_every_strategy_finds_the_entry_a_person_names(
    retriever, strategy, question, expected
):
    """Each question reaches its entry, under each of the four strategies."""
    found = [entry.name for entry in retriever.rank(question, strategy)]
    assert expected in found, f"{strategy}: {question!r} -> {found}"


@pytest.mark.parametrize("strategy", list(RetrievalStrategy))
def test_rank_returns_at_most_top_k_and_never_a_join_path(retriever, strategy):
    """A ranking is bounded by `top_k`, and holds nothing that publishes no text."""
    for question, _ in QUESTIONS:
        found = retriever.rank(question, strategy, top_k=3)
        assert len(found) <= 3, f"{strategy}: {question!r} returned {len(found)}"
        assert not [entry for entry in found if isinstance(entry, JoinPath)], (
            f"{strategy}: {question!r} ranked a Join Path, which has no searchable text"
        )


def test_text_search_can_find_nothing_where_vector_search_cannot(retriever):
    """The one behavioural difference between the two searches, on one question."""
    assert retriever.rank(OFF_TOPIC, RetrievalStrategy.TEXT) == []
    assert retriever.rank(OFF_TOPIC, RetrievalStrategy.VECTOR) != []


def test_retrieve_adds_the_entries_the_ranking_names(retriever):
    """`Account Value` arrives with the metric it derives from and both their routes."""
    found = retriever.retrieve(
        "what are our clients' portfolios worth in total",
        RetrievalStrategy.RERANKED,
        top_k=1,
    )
    names = [entry.name for entry in found]
    assert names[0] == "Account Value"
    account_value = found[0]
    assert "Cash Balance" in names, f"the metric it derives from is missing: {names}"
    for named in references(account_value) + references(retriever.entries["Cash Balance"]):
        assert named in names, f"{named} is named by a retrieved entry and absent"


def test_retrieve_is_not_bounded_by_top_k_where_rank_is(retriever):
    """Why Evaluation measures `rank`: closure puts entries no search scored.

    "by region" declares a route from each of the four fact tables, and closure
    takes all five Join Paths they name because which route applies is not settled
    until SQL is generated. A question that starts at `fct_trade` needs two of them.
    """
    question = "break the answer down by where the client is based"
    ranked = retriever.rank(question, RetrievalStrategy.RERANKED, top_k=5)
    full = retriever.retrieve(question, RetrievalStrategy.RERANKED, top_k=5)
    assert len(ranked) == 5
    assert len(full) > len(ranked), "closure added nothing — this proved nothing"
    assert [entry.name for entry in full[:5]] == [entry.name for entry in ranked]
    by_region = retriever.entries["by region"]
    assert set(references(by_region)) <= {entry.name for entry in full}


@pytest.mark.parametrize("strategy", list(RetrievalStrategy))
def test_retrieve_returns_no_join_path_nothing_asked_for(retriever, strategy):
    """Every Join Path in a result is named by another entry in that same result."""
    seen = 0
    for question, _ in QUESTIONS:
        found = retriever.retrieve(question, strategy)
        named = {name for entry in found for name in references(entry)}
        for entry in found:
            if isinstance(entry, JoinPath):
                seen += 1
                assert entry.name in named, (
                    f"{strategy}: {question!r} returned Join Path {entry.name} that "
                    f"nothing in the result names"
                )
    assert seen, "no Join Path reached a result — this check proved nothing"


def test_every_entry_type_declares_what_it_references():
    """`REFERENCE_FIELDS` classifies all four types, and its fields are real."""
    assert set(REFERENCE_FIELDS) == {entry_type for _, entry_type in ENTRY_KINDS.values()}
    for entry_type, named in REFERENCE_FIELDS.items():
        declared = {field.name for field in fields(entry_type)}
        assert set(named) <= declared, f"{entry_type.__name__}: unknown field(s)"


def test_every_reference_resolves_to_an_entry(retriever):
    """Closure can only terminate if every name an entry publishes is an entry."""
    seen = 0
    for entry in retriever.entries.values():
        for name in references(entry):
            seen += 1
            assert name in retriever.entries, f"{entry.name} names absent {name!r}"
    assert seen, "nothing in the corpus references anything — this proved nothing"
