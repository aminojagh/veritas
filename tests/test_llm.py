"""What Veritas puts on the wire when it calls a model, and what it makes of the reply.

The provider is a stub HTTP server speaking the OpenAI Chat Completions API, so
these run with no key and no network. What they cannot prove is that a real
provider answers a real question well — that is
[DEBT-028](../.claude/docs/debt-ledger.md#debt-028--no-test-reaches-a-real-provider-so-the-live-path-is-proven-only-by-a-stub-server)
— but everything between `complete()` and the JSON on the socket is exercised
here: the messages, the model name, the temperature, the JSON-object request, the
three ways a call comes back with nothing to read, and what the reply says the call
cost.
"""

import json
import os
import threading
from decimal import Decimal
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from veritas.llm import (
    DEFAULT_PROVIDER,
    MODEL_VARIABLE,
    PRICES,
    PROVIDER_VARIABLE,
    PROVIDERS,
    ChatCompletions,
    LanguageModelError,
    ModelCall,
    default_model,
    model_for,
    registered_models,
)
from veritas.orchestrator import rewrite


def completion(text: str, usage: dict | None = None) -> dict:
    """One Chat Completions response carrying `text`, and what it reports having cost.

    `usage` is optional in the API this speaks, so it is optional here: a reply with no
    accounting on it is a reply a caller still has to be able to read.
    """
    return {
        "id": "stub",
        "object": "chat.completion",
        "created": 0,
        "model": "stub",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": text},
                "finish_reason": "stop",
            }
        ],
        **({"usage": usage} if usage else {}),
    }


class StubEndpoint:
    """A stub OpenAI-compatible endpoint that records what was posted to it."""

    def __init__(self, reply: dict, status: int = 200) -> None:
        self.reply = reply
        self.status = status
        self.requests: list[dict] = []
        recorder = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self) -> None:
                length = int(self.headers["Content-Length"])
                recorder.requests.append(json.loads(self.rfile.read(length)))
                body = json.dumps(recorder.reply).encode()
                self.send_response(recorder.status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *args) -> None:
                """Quiet: pytest captures stderr and the access log is noise."""

        self._server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.base_url = f"http://127.0.0.1:{self._server.server_port}/v1"

    def __enter__(self) -> "StubEndpoint":
        threading.Thread(target=self._server.serve_forever, daemon=True).start()
        return self

    def __exit__(self, *_) -> None:
        self._server.shutdown()
        self._server.server_close()

    def model(self, name: str = "stub-model") -> ChatCompletions:
        """A `ChatCompletions` pointed at this server."""
        return ChatCompletions(name, base_url=self.base_url, api_key="not-a-key")


def test_the_call_carries_the_two_messages_the_model_name_and_the_temperature():
    """The seam's two arguments become the two roles the API takes."""
    with StubEndpoint(completion("hello")) as provider:
        assert provider.model().complete("be terse", "who are you").text == "hello"
    [sent] = provider.requests
    assert sent["model"] == "stub-model"
    assert sent["temperature"] == 0.0
    assert sent["messages"] == [
        {"role": "system", "content": "be terse"},
        {"role": "user", "content": "who are you"},
    ]


def test_a_json_object_is_asked_for_only_when_the_caller_asks_for_one():
    """`json_object` is a request made on the wire, not a promise kept locally."""
    with StubEndpoint(completion("{}")) as provider:
        model = provider.model()
        model.complete("system", "user")
        model.complete("system", "user", json_object=True)
    plain, constrained = provider.requests
    assert "response_format" not in plain
    assert constrained["response_format"] == {"type": "json_object"}


def test_a_provider_that_refuses_raises_rather_than_returns():
    """A refused call has no text, and a caller must not read one out of it."""
    with StubEndpoint({"error": {"message": "no"}}, status=400) as provider:
        with pytest.raises(LanguageModelError, match="refused the call"):
            provider.model().complete("system", "user")


@pytest.mark.parametrize(
    "reply", [completion(""), completion(None), {"id": "stub", "choices": []}]
)
def test_a_reply_with_no_text_raises_rather_than_returns_nothing(reply):
    """Empty content, null content, and no choice at all are one thing to a caller."""
    with StubEndpoint(reply) as provider:
        with pytest.raises(LanguageModelError, match="returned no text"):
            provider.model().complete("system", "user")


def test_a_reply_carries_what_the_call_read_wrote_and_took():
    """What the Question Log records per model call, measured where the call is made.

    A caller that was handed the text alone could not cost the call afterwards, and the
    wall time a person waited is the time this socket took.
    """
    usage = {"prompt_tokens": 1200, "completion_tokens": 90, "total_tokens": 1290}
    with StubEndpoint(completion("hello", usage)) as provider:
        reply = provider.model().complete("be terse", "who are you")
    assert reply.text == "hello"
    assert (reply.call.prompt_tokens, reply.call.completion_tokens) == (1200, 90)
    assert reply.call.model == "stub-model" and reply.call.provider == DEFAULT_PROVIDER
    assert reply.call.seconds > 0


def test_a_provider_that_reports_no_usage_is_still_a_reply():
    """`usage` is optional in the API Veritas speaks, and a missing count is zero
    tokens rather than a failed call."""
    with StubEndpoint(completion("hello")) as provider:
        reply = provider.model().complete("be terse", "who are you")
    assert reply.text == "hello"
    assert (reply.call.prompt_tokens, reply.call.completion_tokens) == (0, 0)


def test_a_call_costs_its_tokens_times_the_price_of_the_model_that_served_it():
    """A million tokens in at $0.75 and a million out at $4.50 is $5.25, and the
    arithmetic is exact because a price is a decimal and not a float."""
    priced = ModelCall("openai", "gpt-5.4-mini", 1_000_000, 1_000_000)
    assert priced.cost == Decimal("5.25")
    assert ModelCall("openai", "gpt-5.4-mini", 1200, 90).cost == Decimal("0.001305")


def test_an_unpriced_model_costs_nothing_known_rather_than_nothing():
    """The registry serves a model this table does not price, and a chart must show a
    gap there rather than a zero — the two are different claims about a call."""
    unpriced = PROVIDERS["groq"]
    assert (unpriced.name, unpriced.default_model) not in PRICES
    assert ModelCall(unpriced.name, unpriced.default_model, 900, 40).cost is None


def test_every_price_says_when_it_was_read_and_where_from():
    """A price is neither a definition nor a measurement of Veritas: nothing here can
    reproduce it and a vendor can change it, so each row carries its own provenance."""
    for (provider, model), price in PRICES.items():
        where = f"{provider} {model}"
        assert price.read.startswith("20") and price.page.startswith("https://"), where
        assert price.prompt > 0 and price.completion > 0, where


def test_the_key_never_reaches_the_representation():
    """`repr` is what lands in an error message and a log line."""
    with StubEndpoint(completion("hi")) as provider:
        shown = repr(provider.model())
    assert "not-a-key" not in shown
    assert "stub-model" in shown and provider.base_url in shown


def test_a_question_is_resolved_over_the_wire(semantic):
    """The whole of 6.3 against a provider: question in, certified meaning out."""
    with StubEndpoint(completion('{"revenue": "Net Revenue"}')) as provider:
        resolved = rewrite(
            "what was our revenue after rebates last quarter",
            model=provider.model(),
            layer=semantic,
        )
    assert resolved.resolutions == {"revenue": ("Net Revenue",)}
    assert resolved.resolved
    [sent] = provider.requests
    assert sent["response_format"] == {"type": "json_object"}
    assert "Ask, unless the question names one" in sent["messages"][0]["content"]


@pytest.fixture
def no_env_file(monkeypatch, tmp_path):
    """No `.env` behind the environment, so what a test sets is all there is.

    The repository's own `.env` holds a real key, and a test that reads it would
    both spend it and pass for a reason the test did not arrange.
    """
    monkeypatch.setattr("veritas.llm.model.ENV_FILE", tmp_path / "absent")
    default_model.cache_clear()
    yield
    default_model.cache_clear()


def test_the_default_provider_is_the_one_the_course_already_asks_for(
    monkeypatch, no_env_file
):
    """A clone with only the Zoomcamp's key set runs without configuring anything."""
    monkeypatch.delenv(PROVIDER_VARIABLE, raising=False)
    monkeypatch.delenv(MODEL_VARIABLE, raising=False)
    monkeypatch.setenv(PROVIDERS[DEFAULT_PROVIDER].key_variable, "not-a-key")
    default = PROVIDERS[DEFAULT_PROVIDER]
    assert (default_model().model, default_model().base_url) == (
        default.default_model,
        default.base_url,
    )


def test_the_second_provider_is_one_variable_away(monkeypatch, no_env_file):
    """What Step 007 sweeps: a second model is a value, not a second code path."""
    monkeypatch.setenv(PROVIDER_VARIABLE, "groq")
    monkeypatch.setenv(PROVIDERS["groq"].key_variable, "not-a-key")
    monkeypatch.delenv(MODEL_VARIABLE, raising=False)
    assert (default_model().model, default_model().base_url) == (
        PROVIDERS["groq"].default_model,
        PROVIDERS["groq"].base_url,
    )


def test_a_model_name_is_passed_with_the_provider_it_belongs_to(
    monkeypatch, no_env_file
):
    """`VERITAS_LLM_MODEL` aims the configured provider; a sweep names its own."""
    monkeypatch.setenv(MODEL_VARIABLE, "gpt-4.1-mini")
    for provider in PROVIDERS.values():
        monkeypatch.setenv(provider.key_variable, "not-a-key")
    assert default_model().model == "gpt-4.1-mini"
    assert model_for("groq", "openai/gpt-oss-20b").model == "openai/gpt-oss-20b"


def test_a_provider_outside_the_two_is_refused_naming_the_two(monkeypatch, no_env_file):
    """The registry is closed. A third provider is an extension, not a variable."""
    monkeypatch.setenv(PROVIDER_VARIABLE, "anthropic")
    with pytest.raises(LanguageModelError, match="not a provider Veritas supports"):
        default_model()
    with pytest.raises(LanguageModelError, match="groq or openai"):
        model_for("ollama")


def test_a_provider_with_no_key_names_the_variable_to_set(monkeypatch, no_env_file):
    """The one thing a reader can fix is the one thing the error says."""
    for provider in PROVIDERS.values():
        monkeypatch.delenv(provider.key_variable, raising=False)
    for name, provider in PROVIDERS.items():
        with pytest.raises(LanguageModelError, match=provider.key_variable):
            model_for(name)


def test_a_sweep_over_the_registry_runs_every_provider_on_its_own_model(
    monkeypatch, no_env_file
):
    """The whole registry, unnarrowed, is what a published comparison is run over."""
    for provider in PROVIDERS.values():
        monkeypatch.setenv(provider.key_variable, "not-a-key")
    clients = registered_models()
    assert {name: client.model for name, client in clients.items()} == {
        name: provider.default_model for name, provider in PROVIDERS.items()
    }


def test_a_sweep_can_be_narrowed_to_one_provider_and_one_of_its_models(
    monkeypatch, no_env_file
):
    """What a run ranking one provider's models against each other costs: that provider
    alone, on the model being ranked rather than on the registered one."""
    monkeypatch.setenv(PROVIDERS["openai"].key_variable, "not-a-key")
    monkeypatch.delenv(PROVIDERS["groq"].key_variable, raising=False)
    clients = registered_models(["openai"], "a-candidate")
    assert {name: client.model for name, client in clients.items()} == {
        "openai": "a-candidate"
    }


def test_a_model_asked_of_more_than_one_provider_is_refused(monkeypatch, no_env_file):
    """A model name belongs to the provider serving it, so one name over two providers
    would measure a model one of them never ran."""
    for provider in PROVIDERS.values():
        monkeypatch.setenv(provider.key_variable, "not-a-key")
    with pytest.raises(LanguageModelError, match="asked of one provider"):
        registered_models(model="a-candidate")


def test_a_key_in_the_env_file_is_read_when_the_environment_has_none(
    monkeypatch, tmp_path
):
    """A reviewer following `README.md` puts the key in a file, not in a shell."""
    env_file = tmp_path / ".env"
    env_file.write_text("OPENAI_API_KEY=from-the-file\n")
    monkeypatch.setattr("veritas.llm.model.ENV_FILE", env_file)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert model_for("openai").base_url == PROVIDERS["openai"].base_url
    assert os.environ["OPENAI_API_KEY"] == "from-the-file"
