"""What the Question Log records, what it refuses to lose on the way, and what charts it.

Three claims. The **seam claim**: the only module that names Postgres is
`veritas/observability/postgres.py`, and an installation with no server says which value
it is missing rather than raising a driver's exception at whoever asked a question. The
**row claim**: a Grounded Answer becomes one row carrying its ending, its statement, its
verdict with the Rejection Reasons a chart groups by, its Lineage entry by entry and its
model calls call by call — and a cost that is absent rather than zero where the model
that served it is unpriced. Feedback then lands on that row and on no other, and the
latest verdict left on it stands. The **chart claim**: the dashboard is a file rather than
something clicked together, it holds the two charts the Monitoring criterion names, and
every query on it runs against the schema — so a panel broken by the next column to move
fails a test rather than a demo.

The row claim needs a real server, because a claim about a schema proven against a double
is a claim about the double, and the chart claim ends up needing both a server and Grafana
for the same reason. Every test that does takes the `log` or the `grafana` fixture, and
those fixtures are the whole of the gating: with nothing reachable they skip, naming what
they could not reach. Everything else here reads files and runs either way.

Nothing here starts or stops a container — the server is brought up by hand, once, and
left up:

    docker compose up -d && uv run pytest tests/test_observability.py

Afterwards `docker compose down` stops it and keeps the rows, because the volume is named;
`docker compose down -v` empties it, and the next connect applies `schema.sql` to an empty
database again. Either is safe to run straight after a suite: these tests record into the
Question Log this installation is configured for and delete their own rows by identifier
as each finishes, so a run leaves it as it found it. This file reads what it wrote through
its own connection rather than through the writer's, since a writer that reports its own
rows correct proves less than an independent reader does.
"""

import base64
import json
import os
import re
import urllib.error
import urllib.request
from decimal import Decimal

import psycopg
import pytest
import yaml
from psycopg.rows import dict_row

from veritas.llm import ENV_FILE, ModelCall
from veritas.observability import (
    DATABASE_VARIABLE,
    Feedback,
    HOST_VARIABLE,
    PASSWORD_VARIABLE,
    PORT_VARIABLE,
    USER_VARIABLE,
    PostgresQuestionLog,
    QuestionLogError,
    connection_string,
    settings,
)
from veritas.orchestrator import EndedBy, GroundedAnswer, Lineage
from veritas.validation import ANALYST, RejectionReason, ValidationGateOutcome

# A statement and the verdict it earns are not what this file is about, so both are
# written rather than generated: what is under test is the row, not the Gate.
STATEMENT = (
    "SELECT count(fct_trade.trade_id) AS answer FROM fct_trade "
    "JOIN dim_account ON dim_account.account_id = fct_trade.account_id "
    "JOIN dim_client ON dim_client.client_id = dim_account.client_id "
    "WHERE dim_client.client_region = 'EU'"
)

# One call to a model the price table prices, and one to a model it does not — a
# provider serves more models than any page this repository has read carries a figure
# for, and `--model` on the Evaluation sweep will name one sooner or later.
PRICED = ModelCall("openai", "gpt-5.4-mini", prompt_tokens=1200, completion_tokens=90)
UNPRICED = ModelCall(
    "openai", "a-model-no-page-here-carries-a-price-for",
    prompt_tokens=900, completion_tokens=40,
)

ALL_FIVE = (
    HOST_VARIABLE,
    PORT_VARIABLE,
    USER_VARIABLE,
    PASSWORD_VARIABLE,
    DATABASE_VARIABLE,
)


# -- the seam claim --------------------------------------------------------------


def test_only_the_postgres_module_names_the_driver(root):
    """One boundary, checked rather than promised — the shape ADR-0002 gave the
    Warehouse, applied to the store Observability writes to."""
    importing = {
        str(path.relative_to(root))
        for path in sorted((root / "veritas").rglob("*.py"))
        if "__pycache__" not in path.parts
        and re.search(r"^import psycopg|^from psycopg", path.read_text(), re.M)
    }
    assert importing == {"veritas/observability/postgres.py"}


def test_an_installation_with_no_credentials_is_told_all_of_them(monkeypatch, tmp_path):
    """A person who has set none should be told five things once, not one thing five
    times."""
    monkeypatch.setattr("veritas.observability.postgres.ENV_FILE", tmp_path / "absent")
    for name in ALL_FIVE:
        monkeypatch.delenv(name, raising=False)
    with pytest.raises(QuestionLogError) as unreachable:
        settings()
    said = str(unreachable.value)
    assert USER_VARIABLE in said and PASSWORD_VARIABLE in said
    assert DATABASE_VARIABLE in said
    assert HOST_VARIABLE not in said and PORT_VARIABLE not in said, (
        "the host and the port default to what compose publishes"
    )


def test_the_five_values_become_one_connection_string(monkeypatch, tmp_path):
    """Assembled by the driver rather than by formatting, so a password with a space in
    it is a value and not a syntax error."""
    monkeypatch.setattr("veritas.observability.postgres.ENV_FILE", tmp_path / "absent")
    monkeypatch.setenv(USER_VARIABLE, "veritas")
    monkeypatch.setenv(PASSWORD_VARIABLE, "a pass'word")
    monkeypatch.setenv(DATABASE_VARIABLE, "veritas")
    for name in (HOST_VARIABLE, PORT_VARIABLE):
        monkeypatch.delenv(name, raising=False)
    where = psycopg.conninfo.conninfo_to_dict(connection_string())
    assert where["password"] == "a pass'word"
    assert (where["host"], where["port"]) == ("localhost", "5432")


# -- the row claim ---------------------------------------------------------------


@pytest.fixture(scope="module")
def log():
    """The Question Log this installation is configured for, opened once."""
    try:
        opened = PostgresQuestionLog()
    except QuestionLogError as unreachable:
        pytest.skip(f"no Question Log to record to: {unreachable}")
    with opened:
        yield opened


@pytest.fixture
def writing(log):
    """Record a question, and take every row this test wrote back out at the end."""
    written: list[int] = []

    def record(answer, access_profile=ANALYST) -> int:
        written.append(log.record(answer, access_profile))
        return written[-1]

    yield record
    with psycopg.connect(log.conninfo) as connection:
        connection.execute(
            "DELETE FROM question WHERE question_id = ANY(%s)", (written,)
        )


def read(log, table: str, question_id: int) -> list[dict]:
    """Every row of one table for one question, read through a connection of this
    file's own."""
    with psycopg.connect(log.conninfo, row_factory=dict_row) as connection:
        return connection.execute(
            f"SELECT * FROM {table} WHERE question_id = %s ORDER BY question_id",
            (question_id,),
        ).fetchall()


@pytest.fixture
def answered(semantic):
    """A question that was answered, with everything a row can carry on it."""
    return GroundedAnswer(
        question="how many trades did we make",
        ended_by=EndedBy.ANSWER,
        rewritten="how many trades did we make",
        sql=STATEMENT,
        columns=("answer",),
        rows=((412,),),
        lineage=Lineage((
            semantic.metrics["Trade Count"],
            semantic.join_paths["trade_to_account"],
        )),
        outcome=ValidationGateOutcome(
            allowed=True, rules=("read-only",), metrics=("Trade Count",)
        ),
        calls=(PRICED,),
        seconds=2.75,
    )


def test_the_schema_is_applied_on_connect_and_a_second_connect_keeps_the_rows(
    log, writing, answered
):
    """A fresh container and a container with a month of traffic in it reach the same
    state, so nothing has to be run by hand before the App can record — and a second
    process opening the log applies the same file without emptying it.
    """
    question_id = writing(answered)
    with PostgresQuestionLog(log.conninfo):
        pass
    assert len(read(log, "question", question_id)) == 1


def test_an_answered_question_is_one_row_saying_what_it_was_and_what_it_took(
    log, writing, answered
):
    """The whole of a Grounded Answer that carried a number: the ending a chart groups
    by, the statement, the verdict, how many rows came back, and what answering it
    cost."""
    question_id = writing(answered)
    [row] = read(log, "question", question_id)
    assert row["question"] == answered.question
    assert row["ended_by"] == str(EndedBy.ANSWER)
    assert row["role"] == ANALYST.role
    assert row["sql"] == STATEMENT
    assert row["row_count"] == 1
    assert row["allowed"] is True and row["reasons"] == []
    assert row["refusal"] is None and row["clarifying_question"] is None
    assert row["seconds"] == 2.75
    assert row["cost"] == PRICED.cost
    assert row["asked_at"] is not None


def test_the_lineage_is_one_row_per_entry_at_the_version_it_was_read(
    log, writing, answered
):
    """*"Which Semantic Entries and which Metric Definition versions produced a Grounded
    Answer"* — recorded per entry, in the order the answer cites them, so
    metric-usage frequency is a count and not a parse."""
    question_id = writing(answered)
    entries = read(log, "lineage_entry", question_id)
    assert [(one["position"], one["name"], one["kind"]) for one in entries] == [
        (0, "Trade Count", "metric"),
        (1, "trade_to_account", "join_path"),
    ]
    assert all(one["version"] >= 1 for one in entries)


def test_a_model_call_is_one_row_carrying_what_it_read_wrote_and_cost(
    log, writing, answered
):
    """Per call rather than per question, because *"cost by model"* is a chart and a
    question can ask two different models one thing each."""
    question_id = writing(answered)
    [call] = read(log, "model_call", question_id)
    assert (call["provider"], call["model"]) == ("openai", "gpt-5.4-mini")
    assert (call["prompt_tokens"], call["completion_tokens"]) == (1200, 90)
    assert call["cost"] == Decimal("0.001305")


def test_a_refused_question_records_the_reasons_a_chart_groups_by(log, writing):
    """*"Validation-Gate rejections by reason"* reads this column. A refused statement
    produced no rows, which is not the same as producing none."""
    refused = ValidationGateOutcome(
        allowed=False,
        explanation="dim_client.client_name is restricted",
        reasons=(RejectionReason.RESTRICTED_COLUMN,),
        rules=("read-only", "restricted columns"),
    )
    question_id = writing(
        GroundedAnswer(
            question="what is our biggest client called",
            ended_by=EndedBy.GATE,
            rewritten="what is our biggest client called",
            sql="SELECT dim_client.client_name FROM dim_client",
            outcome=refused,
            refusal=refused.explanation,
            calls=(PRICED, PRICED),
            seconds=1.5,
        )
    )
    [row] = read(log, "question", question_id)
    assert row["allowed"] is False
    assert row["reasons"] == [str(RejectionReason.RESTRICTED_COLUMN)]
    assert row["explanation"] == refused.explanation
    assert row["row_count"] is None
    assert row["refusal"] == refused.explanation
    assert len(read(log, "model_call", question_id)) == 2


def test_a_question_asked_back_records_the_question_and_no_statement(log, writing):
    """The first way out, and a row: the person was asked which meaning, and nothing
    reached the Gate."""
    question_id = writing(
        GroundedAnswer(
            question="what was our revenue",
            ended_by=EndedBy.REWRITE,
            rewritten="what was our revenue",
            clarifying_question="Do you mean Gross Revenue or Net Revenue?",
            calls=(PRICED,),
            seconds=0.9,
        )
    )
    [row] = read(log, "question", question_id)
    assert row["ended_by"] == str(EndedBy.REWRITE)
    assert row["clarifying_question"].startswith("Do you mean")
    assert (row["sql"], row["allowed"], row["row_count"]) == (None, None, None)
    assert read(log, "lineage_entry", question_id) == []


def test_an_unpriced_model_leaves_a_gap_in_the_cost_column_rather_than_a_zero(
    log, writing, answered
):
    """A cost of nothing and a cost nobody knows are different bars, and only one of
    them is true of a model this repository has read no price for."""
    from dataclasses import replace

    question_id = writing(replace(answered, calls=(PRICED, UNPRICED)))
    [row] = read(log, "question", question_id)
    assert row["cost"] is None
    costs = [one["cost"] for one in read(log, "model_call", question_id)]
    assert costs == [PRICED.cost, None]


def test_where_the_rows_go_is_said_without_the_password(log):
    """What the sidebar prints and what an error message carries."""
    assert str(log).endswith("/veritas")
    assert settings()[PASSWORD_VARIABLE] not in f"{log!r} {log!s}"


def test_feedback_lands_on_the_row_of_the_answer_it_was_left_on(log, writing, answered):
    """Registered as *"attached to that answer's Question Log row and never to the
    question text alone"* — so the same words asked twice are two rows, and a verdict
    belongs to the one the person was shown."""
    question_id = writing(answered)
    the_same_words_again = writing(answered)
    log.leave_feedback(question_id, Feedback(up=True, note="matches the finance pack"))
    [row] = read(log, "feedback", question_id)
    assert (row["up"], row["note"]) == (True, "matches the finance pack")
    assert row["left_at"] is not None
    assert read(log, "feedback", the_same_words_again) == []


def test_the_latest_verdict_on_an_answer_stands(log, writing, answered):
    """A second verdict replaces the first rather than becoming a second bar on the
    chart beside it, and a sentence withdrawn is absent rather than empty."""
    question_id = writing(answered)
    log.leave_feedback(question_id, Feedback(up=True, note="right first time"))
    log.leave_feedback(question_id, Feedback(up=False))
    [row] = read(log, "feedback", question_id)
    assert (row["up"], row["note"]) == (False, None)


def test_feedback_on_a_question_that_was_never_recorded_is_refused(
    log, writing, answered
):
    """There is no answer to have read, so there is nothing this could be Feedback on.
    The foreign key says so, and the log goes on taking rows afterwards — a refusal
    inside a transaction of its own leaves nothing poisoned behind it."""
    with pytest.raises(QuestionLogError) as orphan:
        log.leave_feedback(2**40, Feedback(up=True))
    assert "feedback" in str(orphan.value)
    assert len(read(log, "question", writing(answered))) == 1


# -- the chart claim -------------------------------------------------------------

GRAFANA = "grafana"
DASHBOARD = "question-log.json"

# The two charts the Monitoring criterion of the
# [Zoomcamp criteria map](../.claude/docs/design/target-state.md) names in its own words —
# *"including Validation-Gate rejections by reason and metric-usage frequency"*.
NAMED_BY_THE_CRITERION = (
    "validation gate rejections by rejection reason",
    "metric-usage frequency",
)


@pytest.fixture(scope="module")
def dashboard(root) -> dict:
    """The dashboard as Grafana reads it — the provisioned file itself, not an export."""
    return json.loads((root / GRAFANA / "dashboards" / DASHBOARD).read_text())


def provisioned(root, kind: str, name: str) -> dict:
    """One provisioning file, parsed."""
    return yaml.safe_load(
        (root / GRAFANA / "provisioning" / kind / name).read_text()
    )


def queries(dashboard: dict) -> list[tuple[str, str, str, str]]:
    """Every query the dashboard runs: its panel, its target, its SQL and the shape it
    asks Grafana to read the answer back in."""
    return [
        (panel["title"], target["refId"], target["rawSql"], target["format"])
        for panel in dashboard["panels"]
        for target in panel["targets"]
    ]


def test_the_dashboard_carries_the_charts_the_criterion_names_by_name(dashboard):
    """*"Grafana dashboard, >=5 charts — including Validation-Gate rejections by reason
    and metric-usage frequency"*. The count is the floor; the two are the requirement."""
    titles = [panel["title"] for panel in dashboard["panels"]]
    assert len(titles) >= 5
    for named in NAMED_BY_THE_CRITERION:
        assert any(named in title.lower() for title in titles), named
    assert all(panel["targets"] for panel in dashboard["panels"])


def test_every_panel_reads_the_datasource_the_repository_provisions(root, dashboard):
    """A panel naming a datasource nobody provisioned renders *"Datasource not found"* —
    on the demo, and nowhere before it."""
    [datasource] = provisioned(root, "datasources", "question-log.yml")["datasources"]
    named = {panel["datasource"]["uid"] for panel in dashboard["panels"]} | {
        target["datasource"]["uid"]
        for panel in dashboard["panels"]
        for target in panel["targets"]
    }
    assert named == {datasource["uid"]}
    assert datasource["type"] == "grafana-postgresql-datasource"


def test_compose_hands_grafana_the_files_and_the_values_it_provisions_from(root):
    """The three joints between this repository and that container, none of which fails
    loudly: a dashboard directory mounted somewhere the provider does not read, a
    datasource asking for an environment variable the service does not pass, and a home
    dashboard named at a path that holds no file. Each leaves a Grafana that starts
    cleanly and shows nothing.
    """
    compose = yaml.safe_load((root / "docker-compose.yml").read_text())
    grafana = compose["services"]["grafana"]
    mounted = dict(volume.split(":")[:2] for volume in grafana["volumes"])

    [source] = provisioned(root, "dashboards", "veritas.yml")["providers"]
    assert mounted[f"./{GRAFANA}/dashboards"] == source["options"]["path"]
    assert mounted[f"./{GRAFANA}/provisioning"] == "/etc/grafana/provisioning"

    wanted = set(
        re.findall(
            r"\$([A-Z_]+)",
            (root / GRAFANA / "provisioning" / "datasources" / "question-log.yml").read_text(),
        )
    )
    assert wanted and wanted <= set(grafana["environment"])

    home = grafana["environment"]["GF_DASHBOARDS_DEFAULT_HOME_DASHBOARD_PATH"]
    assert home == f"{source['options']['path']}/{DASHBOARD}"
    assert (root / GRAFANA / "dashboards" / DASHBOARD).exists()


def test_no_panel_query_holds_a_macro(dashboard):
    """What keeps the test below honest. Grafana expands `$__timeFilter` and its
    relatives before sending a query, so a panel carrying one would be executed here as
    something Grafana never runs — and the dashboard would be proven against a string of
    the test's own making. No panel reads the time range; the dashboard hides the picker
    rather than showing one that does nothing.
    """
    for title, ref, sql, _ in queries(dashboard):
        assert "$__" not in sql, f"{title} [{ref}]"


def test_every_panel_query_executes_against_the_schema(log, dashboard):
    """Character for character what Grafana sends. A chart whose query breaks on the
    next column to move should fail here rather than in front of somebody."""
    broken = []
    with psycopg.connect(log.conninfo) as connection:
        for title, ref, sql, _ in queries(dashboard):
            try:
                with connection.transaction():
                    connection.execute(sql)
            except psycopg.Error as refused:
                broken.append(f"{title} [{ref}]: {refused}")
    assert broken == []


# -- the chart claim, through Grafana --------------------------------------------

GRAFANA_URL = "http://localhost:{port}"
DEFAULT_GRAFANA_PORT = "3000"


def grafana_settings() -> tuple[str, str, str]:
    """Where Grafana is and who may edit it, from the environment or from `.env`.

    Read here rather than from `veritas/`, because nothing in the application talks to
    Grafana: the App writes rows and Grafana reads them, and the two never meet.
    """
    from dotenv import load_dotenv

    load_dotenv(ENV_FILE)
    return (
        GRAFANA_URL.format(port=os.environ.get("GRAFANA_PORT", DEFAULT_GRAFANA_PORT)),
        os.environ.get("GRAFANA_USER", ""),
        os.environ.get("GRAFANA_PASSWORD", ""),
    )


@pytest.fixture(scope="module")
def grafana():
    """A caller for the Grafana `docker compose up` starts, or a skip.

    Returns a function that reads one Application Programming Interface (API) path,
    signed in as the administrator `.env` declares.
    """
    where, user, password = grafana_settings()
    token = base64.b64encode(f"{user}:{password}".encode()).decode()

    def call(path: str, body: dict | None = None):
        request = urllib.request.Request(
            f"{where}{path}",
            data=None if body is None else json.dumps(body).encode(),
            headers={
                "Authorization": f"Basic {token}",
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(request, timeout=30) as answered:
            return json.load(answered)

    try:
        call("/api/health")
    except (urllib.error.URLError, TimeoutError) as unreachable:
        pytest.skip(f"no Grafana at {where}: {unreachable}")
    return call


def test_grafana_serves_the_dashboard_this_repository_keeps(grafana, dashboard):
    """Provisioned, not clicked together: the file in `grafana/dashboards/` is the
    dashboard Grafana serves, under the identifier the file itself declares."""
    served = grafana(f"/api/dashboards/uid/{dashboard['uid']}")
    assert served["dashboard"]["title"] == dashboard["title"]
    assert len(served["dashboard"]["panels"]) == len(dashboard["panels"])
    assert served["meta"]["provisioned"] is True


def test_grafana_runs_every_panel_through_the_datasource_compose_gave_it(
    log, grafana, dashboard
):
    """The whole joint, end to end: the credentials `.env` holds reached Grafana, the
    datasource file interpolated them, and each panel's query came back as data.

    The panel queries are executed against Postgres directly by the test above this
    section; what this adds is that Grafana is the one executing them, which is the only
    way the interpolated password is proven to be the right one — a wrong one leaves a
    dashboard that starts cleanly and shows nothing.

    Under `-s` it prints what each panel came back holding, which is as close to reading
    the dashboard as a terminal gets.
    """
    broken = []
    print()
    for title, ref, sql, shape in queries(dashboard):
        answered = grafana(
            "/api/ds/query",
            {
                "queries": [
                    {
                        "refId": ref,
                        "datasource": {
                            "type": "grafana-postgresql-datasource",
                            "uid": dashboard["panels"][0]["datasource"]["uid"],
                        },
                        "format": shape,
                        "rawQuery": True,
                        "rawSql": sql,
                    }
                ],
                "from": "now-90d",
                "to": "now",
            },
        )
        result = answered["results"][ref]
        if result.get("status") != 200 or result.get("error"):
            broken.append(f"{title} [{ref}]: {result.get('error', result)}")
        elif not result.get("frames"):
            broken.append(f"{title} [{ref}]: came back with no frame")
        else:
            [frame] = result["frames"]
            values = frame["data"]["values"]
            print(
                f"  {len(values[0]) if values else 0:>3} rows  "
                f"{'/'.join(field['name'] for field in frame['schema']['fields']):<34}"
                f"{title} [{ref}]"
            )
    assert broken == []
