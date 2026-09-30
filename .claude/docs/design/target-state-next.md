# Target State — next

**Status:** `draft`. It answers
[R2](../plan/redesign-roadmap.md#r2--frame-the-problem) and covers purpose and scope
only. R4 adds the components and the flow, and R6 turns it into the
[Target State](target-state.md). Until then the capstone's Target State is still the
agreed one. Whatever still awaits Amino is marked **Open**.

**Ingestion** is used here in a new sense, which
[Terms this draft needs](#terms-this-draft-needs) holds until this draft becomes the
Target State.

---

## Why this project exists

Veritas lets a User ask questions of the data in a relational database, in the words
of its Domain. Each answer is either correct, or a refusal that names what is missing.
Veritas is meant for any Domain, so connecting one must cost as little as possible: no
code, and as few definitions as the Domain's meaning needs. The prototype is built on
one Domain and proven on a second.

## The problem

A schema says what can be computed. It does not say what should be computed. Take
the question "What was our revenue last quarter?" at a brokerage. It has two correct
answers, Gross Revenue and Net Revenue, and a complete, accurate schema can compute
either. A Large Language Model (LLM) that is given only the schema picks one without
saying so. The result is a correct program that computes the wrong number. The same
gap exists in every Domain:
- which date a period is measured on
- which rows count
- which of two near-synonyms a word means
- which joins count a row twice

The capstone closed the gap by certifying finished answers. Each Certified Metric is a
hand-written Metric Definition carrying its own SQL expression, Join Paths, filters
and date column. Each axis it may be sliced by is a Dimension Definition that lists its
own routes. That is correct, and it fails in three ways:

- **It is narrow.** "How many Clients are in APAC?" has one reading and the data holds
  the answer, yet the capstone refuses it because no Certified Metric counts Clients.
- **It grows with the questions, not with the Domain.** Every new metric is a new
  definition with its own joins, filters and axes, and a new kind of metric can need a
  new Validation Gate rule. At that price the User does what a Business Intelligence
  (BI) tool asks of a saved query, writing the correct query once per metric, with a
  chat box in front.
- **It does not move.** Its definitions are written at the level of tables and
  columns, one per answer, so a new Domain starts from none.

So the problem sits between two failures:
- **General text-to-SQL** is broad, and it is wrong without saying so.
- **Certified metrics** are correct, and they are narrow and expensive to extend or
  move.

**The design principle: declare, at the highest level of abstraction that stays
exact.** A User says once what each of the Domain's things is: its entities, how they
relate, what can be measured about them, and the conventions they are measured by.
Veritas derives how to compute an answer from those declarations, with rules that name
no Domain. A definition that says how to compute one answer is the low, imperative
level this principle exists to avoid.

The roadmap names the idea to test: *"a conceptual model of the data at several levels
of abstraction, with defined moves between levels."* R4 decides whether it works.

## Who uses it

There is one role, the **User**. A User connects a database, writes the definitions
that say what its Domain means, and asks questions in the Domain's words. A User checks
an answer's Interpretation, never its SQL, and runs as an Access Profile, which limits
what an answer may show.

- **One role**, because the aim is to shrink a Domain's definitions until writing them
  is a small part of using Veritas, not a separate job.
- **The User is responsible for the definitions being right.** Veritas is responsible
  for every answer following them exactly.
- **A User certifies every definition.** The LLM may draft one, but never certifies
  one. A definition no User certified would be a fact about the Domain that the LLM
  stated itself, and the governing rule below forbids exactly that. This rules out one
  of R4's options, *"a machine alone"*.

## What an answer promises

Veritas sits between a metrics copilot and a general text-to-SQL system:

| Position | What it answers | How it fails |
|---|---|---|
| The capstone's metrics copilot | a Certified Metric, sliced by certified axes | it refuses questions the data answers in exactly one reading |
| General text-to-SQL | anything the schema can compute | it answers the wrong question with confidence |
| **Veritas** | anything that can be expressed by combining the Domain's definitions, using rules Veritas defines | a definition can be wrong, which the User fixes; or the rules can be too weak to express a question, which [refusal review](#a-refusal-is-not-a-dead-end) finds |

This is the capstone's governing rule, generalised:

> **The LLM never states a fact about a Domain.** Every such fact comes from a
> definition a User certified. Veritas supplies the rules for combining definitions,
> and those rules name no Domain. Code checks everything the LLM produces before it
> runs.

Every answer makes five promises:

1. **Faithful.** It computes exactly what its Interpretation says, and it states the
   Interpretation in the Domain's words. Code can check this only if the
   Interpretation and the SQL come from one source. R4 decides which way that goes:
   either the LLM writes SQL, or it writes a query in the concept language that code
   compiles to SQL. Whichever R4 chooses must make this promise checkable by code.
2. **Grounded.** Every term in the Interpretation is a certified definition. A Shadow
   Metric is refused, as it is in the capstone.
3. **Asks or refuses instead of guessing.** These are a Grounded Answer's three
   Endings:
   - one reading: a number
   - two readings: a Clarifying Question. The reply settles it, and Veritas then
     answers. A Clarifying Question whose reply cannot lead to an answer was not
     clarifying.
   - no reading: a refusal that names the definition that is missing
4. **Governed.** It is read-only and its cost is bounded. Nothing an Access Profile
   may not see appears in it. Code checks all three before execution:
   [ADR-0003](../adr/0003-validation-gate-is-deterministic-code.md#decision) says
   *"No LLM participates in the decision to allow or reject a query."*
5. **Private.** No record from the database reaches the LLM. It sees the question,
   the definitions, and the schema: tables, columns and their types. Code alone runs
   the query and puts the answer together.
   - **What it buys:** Veritas can be used on data that may not leave the organisation
     to go to a model provider, and the LLM can no longer misread a result.
   - **What it costs:** the LLM can no longer narrate a result. A filter's values
     (`'UK'` or `'United Kingdom'`?) also have to reach it some other way, and
     [R3](../plan/redesign-roadmap.md#r3--research-prior-art) is researching how.

**The LLM sees the schema.** That overturns
[ADR-0001](../adr/0001-semantic-layer-as-the-retrieval-corpus.md#decision), whose
Retrieval runs *"never over raw warehouse schema"*, because *"once schema sits in the
same corpus as Metric Definitions the model can compose them and "revenue" gets
computed from `commission` directly."* That danger remains. With the columns in view,
Grounded must hold by construction or by check, not because the LLM does not know the
columns. R4 decides how, and rewrites or deletes ADR-0001.

Questions about the definitions or the schema are answered from them, such as "what
does Net Revenue mean?" or "which columns does `fct_trade` have?". Such an answer
reads no records, so it has none of the three Endings and is not a Gold Question,
until R4 designs how these questions are answered.

### A refusal is not a dead end

Every refusal is recorded, and so is every Clarifying Question whose reply led to no
answer. Each is later decided one of two ways:

- **Unanswerable:** the Domain's data cannot answer it, and the refusal was right.
- **A gap:** Veritas should have answered it. A new definition or a change to
  Veritas's rules closes the gap. The question then joins the Gold Question Set with
  its now-known answer, so the gap stays closed.

Deciding a refusal gives it its correct Ending, as a Gold Question already has one.
Who decides, how much of it is automatic, and whether a gap can be closed inside the
conversation that found it, are [R4's](../plan/redesign-roadmap.md#r4--core-design).

### Follow-ups

A User may ask anything next: a follow-up that builds on the last answer, such as "and
by region?", or a question on a new topic. The LLM never opens a new topic itself.

The finished Veritas follows the conversation: an agentic system with memory reads a
follow-up with the turns before it. Early Steps may simplify this, and the design may
not rule it out. Evaluation changes with it, because a Gold Question is one question
and cannot score a follow-up. How a conversation is scored is decided at
[R4](../plan/redesign-roadmap.md#r4--core-design).

## What connecting a Domain costs

Loading a Domain's data and connecting a Domain are separate, and only connecting is
Veritas's:

- **Loading.** A real Domain's data is already kept in a database, and Veritas
  connects to that database instead of loading one. Ingestion loads a prototype
  Domain's public data where no database holds it yet. It is written per Domain and
  lives outside `veritas/`, and none of the three costs below counts it. Making it
  general is second priority.
- **Connecting** points Veritas at the database and describes what its data means, so
  that questions can be asked in the Domain's words. This part must be general first:
  two businesses' Domains have more in common than their data infrastructure.

Answering questions relies only on what a connected database offers, never on anything
the loading added. Three things loading decides bear on that:

- **Fixed data.** A Domain's Gold Question Set is written against its data as it
  stands, whether Ingestion loaded it or it already existed. Its correct Endings hold
  only while that data does not change, so data Ingestion loads stays fixed as the
  capstone's does: sources *"snapshotted into the repository and replayed by
  default"*. Evaluation depends on this, and answering questions does not.
- **The database's shape.** The capstone designed its own schema to be queried: a star
  schema whose `schema.sql` declares foreign keys. A real database need have neither.
  The second Domain's database keeps the tables, names and keys its publisher gave it,
  so the connection cost is measured on a database Veritas did not shape.
- **The engine.** Veritas reaches a database through the Warehouse Adapter, which
  *"Holds the connection and the engine's dialect"*. Which engines a User can connect
  is [R6's](../plan/redesign-roadmap.md#r6--stack-mapped-to-the-skills-goal).

"Domain-agnostic" is claimed only once a second Domain is connected. Three costs are
measured.

1. **Code: none per Domain.**
   - Connecting a Domain adds its definitions, a connection setting and its Gold
     Question Set. It changes no file under `veritas/` or `tests/`.
   - What may need code is a **kind** of construct no earlier Domain had. The
     construct is code, written once in system language, and every later Domain
     inherits it. Which of a Domain's things use it is a definition:
     - *a measure that must not be summed across time* is a construct. That a Cash
       Balance is one is a brokerage definition, and a hospital's bed occupancy would
       be another.
     - *a lookup keyed on a date together with another column* is a construct. That an
       FX Rate is looked up by its date and currency pair is a brokerage definition.
     - a many-to-many relationship, and a record whose history is versioned, are
       constructs too.
   - Code changes per kind of construct, never per Domain. The failure this line
     catches is a rule that grows with one Domain's metrics.
   - The Glossary splits in two: **system language**, which code may use, and **each
     Domain's language**, which only that Domain's definitions may use. A test holds
     `veritas/` to system language.
   - The evidence is the second Domain's connection. Its changes stay inside its own
     directory, or they add a construct, in system language, that the first Domain
     lacked.
2. **Tests: none per Domain.**
   - A Domain's correctness is claimed by its Gold Question Set, which is data.
   - Veritas's behaviour is tested on a made-up Domain, never on a connected one.
     `tests/` keeps a Domain of its own, a few tables and their definitions, built so
     that every kind of construct appears in it. Connecting a Domain therefore cannot
     break a behaviour test, or need one.
   - A check of a Domain's definitions runs unchanged over every connected Domain.
     Examples: every column a definition names exists, and every relationship's keys
     match.
   - A new Domain adds Gold Questions, never a test.
3. **The User's effort: definitions grow with the Domain, not with its questions.**
   - Each entity, relationship, measure and convention is described once. A question
     that combines them needs no further definition. [The problem](#the-problem) says
     what the capstone charges instead.
   - **What is measured per Domain:**
     - the definitions the User wrote or corrected by hand, counted from the Domain's
       git history, beside the size of its schema
     - the hours spent, recorded as dated evidence in the commit message that
       connects the Domain
     - accuracy on questions no single definition answers, in
       [What says the prototype works](#what-says-the-prototype-works)
   - **Target:** a database the size of the prototype's is connected in one working
     day.

## Non-goals

Veritas does not:

- **Write to a database.** It is read-only, always.
- **Read documents.** It works only on structured data in a relational database. Text
  files, PDFs, and free-text columns searched as prose belong to a different system.
- **Predict or explain.** It computes what the data says. Comparisons over time are in
  scope. Forecasts, and "why did X happen", are not.
- **Guess.** When the definitions cannot express a question, it does not fall back to
  unconstrained text-to-SQL. It refuses, names what is missing, and records the
  refusal for review.
- **Browse records.** Listing a table's rows is out. Asking which columns a table has
  is [in](#what-an-answer-promises).
- **Join across databases.** One Domain is one database.
- **Chase conversational polish.** Charts and export are out. Every turn needed to
  answer one question is in: a Clarifying Question ends in the answer, over as many
  rounds as it takes. So are a User's [follow-ups](#follow-ups).

## What says the prototype works

**Provisional.** The targets are agreed, and the scheme around them is expected to
change: R4 revisits it once it says what a definition is, and
[follow-ups](#follow-ups) change what a Gold Question scores.

Each Domain has a Gold Question Set. Each Gold Question names its correct Ending. When
that Ending is a Clarifying Question, the Gold Question also carries the reply and the
number the reply leads to.

Evaluation scores each Gold Question as a pair: its correct Ending, and the Ending
Veritas gave. Every cell is counted, and each is read by its pair. No cell is a
Glossary term.

| Correct ↓ · Veritas gave → | a number | a Clarifying Question | a refusal |
|---|---|---|---|
| **a number** | right if it is the gold number, otherwise wrong | asked needlessly | missed |
| **a Clarifying Question** | a guess | right if, given the reply, it returns the gold number | missed |
| **a refusal** | invented | asked about the unanswerable | right |

The prototype is scored on these measures:

| Measure | What it counts | Target |
|---|---|---|
| **Wrong numbers**, the headline | Gold Questions in the *a number* column where the number is not correct: a wrong number, a guess or an invention. Divided by all Gold Questions. | at most 1 in 50 |
| **Execution Accuracy** | Gold Questions where Veritas's final number is the gold number, including after a Clarifying Question's reply. Divided by the Gold Questions that have a gold number. | at least 4 in 5 |
| **Execution Accuracy without a single definition** | The same, over the Gold Questions that no single definition answers. Near zero, Veritas is a library of saved queries. | set at R4, once a definition is defined |
| **The gap to a baseline** | Wrong numbers and Execution Accuracy for the same LLM, given the schema and no definitions | Veritas's wrong-number rate is at most a quarter of the baseline's |

- **Every Domain** meets these targets, and the second Domain also meets the
  connection cost above.
- **Resolution:** a set must have at least 50 Gold Questions per Domain, so that the
  headline target can be observed at all.
- **The baseline row is what makes the claim falsifiable.** If an LLM that sees only
  the schema matches Veritas, the definitions have not paid for themselves.
- **Execution Accuracy's Glossary definition changes:** it currently counts over
  *"generated queries"*, and it will count over Gold Questions instead.

## The Product Brief

**The [Product Brief](product-brief.md) is deleted when this draft becomes the Target
State**, together with its row in `CLAUDE.md`'s Documents table.
- It describes the brokerage from a job specification. The Domain-agnostic goal
  replaces that.
- Two documents stating one purpose is what *one explanation, one home* forbids.

What in it is still true now lives here. The brief names three failures to prevent:
*"Sensitive-data leakage"*, *"A shadow-metric layer"* and *"Uncontrolled query
cost"*. Those are promises 4, 2 and 4 above.

With the brief gone, a capability beyond this Target State is an extension. It must be
motivated by a named non-goal or an ADR cost, not by a brief. At R7, the [Extension
Register](../extension-register.md)'s header changes to match. That header currently
says *"speculation belongs in the product brief, not here."*

## Terms this draft needs

**Domain**, **User**, **Interpretation** and **Ending** are registered in the
[Glossary](../glossary.md). Ingestion's new sense waits for this draft to become the
Target State, because the Glossary's row describes code that exists now.

| Term | Status | Means | Not | Alternatives considered |
|---|---|---|---|---|
| **Ingestion** | agreed, a new sense of the registered term | The code that loads one prototype Domain's public data into a database, from sources snapshotted into the repository. Written per Domain, outside `veritas/`. | Connecting a Domain, which is Veritas's, and which needs no Ingestion when a database already holds the data. | *Loading*: a second word for a registered concept. |

*Model* is not used on its own. It has meant the LLM, Veritas itself, and the
roadmap's conceptual model. This draft says *the LLM*, and R4 may register *model* for
the last of the three. *Definition* stays a plain word until R4 decides what a
definition is.

### What describes a Domain

The table below lists what a description of a Domain may need to say, and where each
part can come from. The parts a User must write are the connection cost, and the
design principle says to make that list as short as possible.

| Part | At the brokerage | Comes from |
|---|---|---|
| Tables, columns and their types | `fct_trade.commission` is a decimal | the schema |
| Relationships between records, by their keys | a Trade belongs to one Account | the schema's foreign keys where it declares them; otherwise a User |
| Entities: the things records stand for, and what identifies each | a Client, identified by `client_id` | a User |
| Measures, and how each one aggregates | Commission sums; a Cash Balance does not sum across dates | a User |
| Time: which date places each fact in a period | a Trade falls on its Trade Date, not its Settlement Date | a User |
| Conventions the business measures by | Cost Basis is average cost, per [ADR-0006](../adr/0006-every-certified-metric-follows-one-stated-book-convention.md#decision) | a User |
| Named metrics | Net Revenue is Commission less Rebate and Fee | a User |
| Words, including words with two meanings | "revenue" is Gross Revenue or Net Revenue | a User |
| Access: what each Access Profile may see | a Client's region scopes every answer | a User |

The LLM may draft any part a User writes, and a User certifies it. The schema's share
is real at the capstone: `veritas/warehouse/schema.sql` declares foreign keys with
`REFERENCES`, and some of the capstone's Join Paths only restate one. The rest are
conventions, such as an FX Rate joined on a date and a currency.

R4 decides which parts exist, how each is represented, and what the description is
called.
