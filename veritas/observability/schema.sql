-- The Question Log: one question a person asked, per row, with what answering it
-- produced and what it took. Applied on every connect, which is why every statement
-- here is idempotent.
--
-- Three tables, because a question has one ending and one cost but any number of
-- Lineage entries and any number of model calls. A chart that groups by a Rejection
-- Reason reads the array on the question row; the Gate has never returned more than
-- one, and the column is the tuple the verdict carries rather than a flattening of it.

CREATE TABLE IF NOT EXISTS question (
    question_id         BIGSERIAL PRIMARY KEY,
    asked_at            TIMESTAMPTZ      NOT NULL DEFAULT now(),
    question            TEXT             NOT NULL,
    rewritten           TEXT             NOT NULL,
    -- An `EndedBy` member: which step of the flow ended this question. A taxonomy, so
    -- that "questions over time by ending" and "refusals by reason" are one GROUP BY.
    ended_by            TEXT             NOT NULL,
    -- The Access Profile the question was judged under.
    role                TEXT             NOT NULL,
    -- NULL where no statement was written, which is not the same as an empty one.
    sql                 TEXT,
    -- How many rows came back. NULL where nothing ran; 0 is an answer.
    row_count           INTEGER,
    -- The Validation Gate outcome. NULL where no statement reached the Gate.
    allowed             BOOLEAN,
    explanation         TEXT,
    reasons             TEXT[]           NOT NULL DEFAULT '{}',
    -- What the person read when there was no number.
    refusal             TEXT,
    clarifying_question TEXT,
    -- Operational Measures. `cost` is NULL for a model the price table does not price,
    -- never 0 — a cost of nothing and a cost nobody knows are different bars.
    seconds             DOUBLE PRECISION NOT NULL,
    cost                NUMERIC
);

-- What the answer was composed from: the Lineage, one entry per row, in the order the
-- answer cites them. The version is here rather than looked up later because it is the
-- version that was read, and the corpus moves.
CREATE TABLE IF NOT EXISTS lineage_entry (
    question_id BIGINT  NOT NULL REFERENCES question (question_id) ON DELETE CASCADE,
    position    INTEGER NOT NULL,
    name        TEXT    NOT NULL,
    kind        TEXT    NOT NULL,
    version     INTEGER NOT NULL,
    PRIMARY KEY (question_id, position)
);

-- Every call to a model the question made, in the order it made them. Veritas makes at
-- most two per question — resolving Ambiguous Terms, then generating — and a question
-- that says no Ambiguous Term makes one.
CREATE TABLE IF NOT EXISTS model_call (
    question_id       BIGINT           NOT NULL
                          REFERENCES question (question_id) ON DELETE CASCADE,
    position          INTEGER          NOT NULL,
    provider          TEXT             NOT NULL,
    model             TEXT             NOT NULL,
    prompt_tokens     INTEGER          NOT NULL,
    completion_tokens INTEGER          NOT NULL,
    seconds           DOUBLE PRECISION NOT NULL,
    cost              NUMERIC,
    PRIMARY KEY (question_id, position)
);
