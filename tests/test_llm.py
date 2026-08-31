"""What Veritas puts on the wire when it calls a model, and what it makes of the reply.

The provider is a stub HTTP server speaking the OpenAI Chat Completions API, so
these run with no key and no network. What they cannot prove is that a real
provider answers a real question well — that is
[DEBT-028](../.claude/docs/debt-ledger.md#debt-028--no-test-reaches-a-real-provider-so-the-live-path-is-proven-only-by-a-stub-server)
— but everything between `complete()` and the JSON on the socket is exercised
here: the messages, the model name, the temperature, the JSON-object request, and
the three ways a call comes back with nothing to read.
"""

import json
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from veritas.llm import (
    DEFAULT_PROVIDER,
    MODEL_VARIABLE,
    PROVIDER_VARIABLE,
    PROVIDERS,
    ChatCompletions,
    LanguageModelError,
    default_model,
    model_for,
)
from veritas.orchestrator import rewrite


def completion(text: str) -> dict:
    """One Chat Completions response carrying `text`."""
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
        assert provider.model().complete("be terse", "who are you") == "hello"
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
