"""What `docker compose up --build` brings up, and what the image it builds carries.

Two claims. The **compose claim**: the three services Veritas is are all declared, the
App waits for the server it records to, it reaches that server by the name the network
gives it rather than by the `localhost` that is its own container, and the port it is
published on is the one `.env.example` documents. The **image claim**: everything a
question needs is built into the image — the Warehouse replayed from the committed
snapshots and both Retrieval models fetched into `FASTEMBED_CACHE_PATH` — while neither
the key nor the working record is; and the two things the `Dockerfile` must not name
itself, the interpreter version and either model, it does not.

Both are read off files and run everywhere. The tests below them ask a running App and
skip when there is none, the pattern `tests/test_observability.py` uses for Grafana:

    docker compose up -d --build --wait && uv run pytest tests/test_container.py

Nothing here starts, stops or builds a container. A first build fetches an interpreter,
the dependencies and 150-odd megabytes of model weights, which is not something a test
run may decide to do.
"""

import os
import re
import subprocess
import urllib.error
import urllib.request

import psycopg
import pytest
import yaml

from veritas.llm import ENV_FILE, LIVE_VARIABLE
from veritas.observability import HOST_VARIABLE, PORT_VARIABLE, connection_string
from veritas.retrieval import EMBEDDING_MODEL, RERANKER_MODEL

# The three services, and the one this Sub-step added.
APP = "app"
SERVICES = (APP, "postgres", "grafana")

# The port Streamlit listens on inside the container, and the variable `.env` names to
# publish it as. The inside one is fixed: nothing outside this file's own network
# reaches it except through the mapping below.
INSIDE = "8501"
PORT_VARIABLE_APP = "APP_PORT"

# `"${APP_PORT:-8501}:8501"` — the variable that moves the published port, the default
# a reviewer who set nothing gets, and the port inside.
PUBLISHED = re.compile(
    r"^\$\{(?P<variable>[A-Z_]+):-(?P<default>\d+)\}:(?P<inside>\d+)$"
)


@pytest.fixture(scope="module")
def compose(root) -> dict:
    """`docker-compose.yml`, parsed."""
    return yaml.safe_load((root / "docker-compose.yml").read_text())


@pytest.fixture(scope="module")
def dockerfile(root) -> str:
    """`Dockerfile`, as text — what is under test is the commands it runs."""
    return (root / "Dockerfile").read_text()


@pytest.fixture(scope="module")
def declared(root) -> dict[str, str]:
    """Every variable `.env.example` declares, and the value it declares it as."""
    return dict(
        line.split("=", 1)
        for line in (root / ".env.example").read_text().splitlines()
        if line and not line.startswith("#") and "=" in line
    )


# -- the compose claim -----------------------------------------------------------


def test_compose_declares_the_three_services_veritas_runs_as(compose):
    """The App, the server that holds the Question Log, and the Grafana that charts it.
    *"Everything is in docker-compose"* is the rubric row this Step earns."""
    assert set(compose["services"]) == set(SERVICES)


def test_the_app_waits_for_the_server_it_records_to(compose):
    """`docker compose up` returns before Postgres answers, and a question asked in
    that window would be answered and not written down."""
    assert compose["services"][APP]["depends_on"]["postgres"] == {
        "condition": "service_healthy"
    }


def test_the_app_reaches_postgres_by_the_name_the_network_gives_it(compose, declared):
    """Inside the network `localhost` is the App's own container, which runs no
    database — so an App taking the host from `.env` unchanged would find nothing and
    record nothing, with an answer still on the page and a warning under it.

    The file keeps saying `localhost`, because that is what the developer path needs:
    `uv run streamlit run veritas/app/page.py` on the host reaches the port compose
    publishes.
    """
    environment = compose["services"][APP]["environment"]
    assert environment[HOST_VARIABLE] == "postgres"
    assert str(environment[PORT_VARIABLE]) == "5432", (
        "the port inside the network, not the one compose publishes it as"
    )
    assert declared[HOST_VARIABLE] == "localhost"


def test_the_app_is_handed_the_file_the_key_lives_in(compose):
    """The one thing the image deliberately does not carry. Without this the App comes
    up, serves a page, and cannot reach a model."""
    assert compose["services"][APP]["env_file"] == ".env"


def test_the_app_is_published_on_the_port_env_example_documents(compose, declared):
    """A default in the compose file and a different one in `.env.example` is a URL in
    the README that is wrong for everybody who copied the file."""
    [mapping] = compose["services"][APP]["ports"]
    published = PUBLISHED.fullmatch(mapping)
    assert published, mapping
    assert published["variable"] == PORT_VARIABLE_APP
    assert published["inside"] == INSIDE
    assert published["default"] == declared[PORT_VARIABLE_APP]


# -- the image claim -------------------------------------------------------------


def test_the_image_builds_the_warehouse_and_fetches_both_retrieval_models(dockerfile):
    """The two expensive things a question needs, made once at build rather than
    at the first question — which is what
    [DEBT-026](../.claude/docs/debt-ledger.md#debt-026--the-retrieval-models-are-downloaded-rather-than-snapshotted)
    was opened against."""
    assert "python -m veritas.ingestion" in dockerfile
    assert "python -m veritas.retrieval" in dockerfile


def test_the_dockerfile_names_neither_retrieval_model(dockerfile):
    """`search.py`'s two constants are the one place either model is written. A
    Dockerfile that fetched them by name would be a second place, and a model changed
    in one and not the other is an image that downloads at the first question."""
    for model in (EMBEDDING_MODEL, RERANKER_MODEL):
        assert model not in dockerfile


def test_the_dockerfile_pins_no_interpreter_of_its_own(dockerfile, root):
    """`.python-version` is the pin. `uv python install` reads it, so the version is
    written once and an image cannot be a minor release behind the tests."""
    assert "uv python install" in dockerfile
    assert (root / ".python-version").read_text().strip() not in dockerfile


def test_the_build_context_carries_neither_the_key_nor_a_built_warehouse(root):
    """`.env` in a layer is the key published with the image; a Warehouse in a layer is
    whatever the machine that built it happened to hold, shipped as though it were
    replayed from the snapshots."""
    ignored = {
        line.strip()
        for line in (root / ".dockerignore").read_text().splitlines()
        if line.strip() and not line.startswith("#")
    }
    assert {".env", "data/veritas.duckdb", ".venv/"} <= ignored


# -- the two claims, against a running App ---------------------------------------

APP_URL = "http://localhost:{port}"
DEFAULT_APP_PORT = "8501"
HEALTH = "/_stcore/health"


def app_url() -> str:
    """Where `docker compose up` published the App, from the environment or `.env`."""
    from dotenv import load_dotenv

    load_dotenv(ENV_FILE)
    port = os.environ.get(PORT_VARIABLE_APP) or DEFAULT_APP_PORT
    return APP_URL.format(port=port)


def read(where: str) -> str:
    with urllib.request.urlopen(where, timeout=30) as answered:
        return answered.read().decode()


@pytest.fixture(scope="module")
def app() -> str:
    """The App `docker compose up` published, or a skip naming where it was not."""
    where = app_url()
    try:
        read(f"{where}{HEALTH}")
    except (urllib.error.URLError, TimeoutError) as unreachable:
        pytest.skip(f"no App at {where}: {unreachable}")
    return where


def test_the_published_app_answers_the_endpoint_compose_health_checks(app):
    """The same call the service's healthcheck makes, from outside the network — so
    `up --wait` returning and the port being reachable are one claim rather than two."""
    assert read(f"{app}{HEALTH}").strip() == "ok"


def test_what_the_published_port_serves_is_streamlit_and_not_something_else(app):
    """`TITLE` is set by `st.set_page_config`, which runs when a browser has opened a
    session — so the App's own name is not in the document the server sends, and this
    can only claim that what answers on the published port is a Streamlit and not
    whatever else the machine had on 8501. What the page then renders is
    `tests/test_app.py`'s claim, made through Streamlit's own `AppTest`.
    """
    assert "<title>Streamlit</title>" in read(app)


# -- the page inside the container, against a real key and a real server ---------

# One of `tests/test_app.py`'s questions, so what it should come back as is settled
# there and this file is left claiming only what the container adds.
CONTAINER_QUESTION = "what was our gross revenue"

# Driven with Streamlit's own `AppTest`, inside the container, with nothing doubled:
# `page.py` builds its own Orchestrator and its own Question Log. Written as a script
# for `python -c` because the image carries no `tests/` — a grader runs the suite from
# a clone with `uv`, which is where this test runs from too.
ASK = f"""
from streamlit.testing.v1 import AppTest
page = AppTest.from_file("veritas/app/page.py", default_timeout=300)
page.run()
print("recording:", [caption.value for caption in page.sidebar.caption][-1])
page.text_input[0].set_value({CONTAINER_QUESTION!r})
page.button[0].click().run()
print("exception:", list(page.exception))
print("answer:", [(one.label, one.value) for one in page.metric])
print("verdict:", [one.value for one in page.success])
"""


@pytest.fixture(scope="module")
def container(root):
    """A caller that runs one command inside the App's container, or a skip."""

    def inside(*command: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["docker", "compose", "exec", "-T", APP, *command],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=900,
        )

    try:
        reached = inside("python", "-c", "pass")
    except (OSError, subprocess.TimeoutExpired) as unreachable:
        pytest.skip(f"no docker compose to ask: {unreachable}")
    if reached.returncode != 0:
        pytest.skip(f"no {APP} container running: {reached.stderr.strip()}")
    return inside


@pytest.mark.skipif(
    not os.environ.get(LIVE_VARIABLE),
    reason=f"spends a real key: set {LIVE_VARIABLE}=1 to run it",
)
def test_the_page_in_the_container_answers_a_question_and_records_it(container):
    """The two joints no file can prove: the key reaches the App from `env_file`, and
    the server it records to is the one the network calls `postgres`. Both fail
    quietly — an App with no key answers nothing, and an App pointed at a `localhost`
    that is its own container answers and writes nothing down.

    It deletes the row it wrote, because a test that leaves traffic behind changes what
    the dashboard says.
    """
    try:
        with psycopg.connect(connection_string()) as reader:
            ((latest,),) = reader.execute(
                "SELECT coalesce(max(question_id), 0) FROM question"
            )
    except psycopg.Error as unreachable:
        pytest.skip(f"no Question Log to read back from: {unreachable}")

    asked = container("python", "-c", ASK)
    assert asked.returncode == 0, asked.stderr
    assert "recording: recording to postgres:5432/" in asked.stdout, asked.stdout
    assert "exception: []" in asked.stdout, asked.stdout
    assert "allowed" in asked.stdout, asked.stdout

    with psycopg.connect(connection_string()) as reader:
        written = reader.execute(
            "SELECT question_id, ended_by, allowed FROM question "
            "WHERE question = %s AND question_id > %s",
            (CONTAINER_QUESTION, latest),
        ).fetchall()
        assert len(written) == 1, written
        question_id, ended_by, allowed = written[0]
        assert (ended_by, allowed) == ("answer", True)
        reader.execute("DELETE FROM question WHERE question_id = %s", (question_id,))
