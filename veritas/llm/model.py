"""The one boundary through which Veritas calls a Large Language Model.

Veritas supports two providers and no others — OpenAI, which the Large Language
Model Zoomcamp already asks a grader for, and Groq, a second registered provider
whose free tier costs a reader nothing and which no published figure depends on.
Both speak the OpenAI Chat
Completions API, so `PROVIDERS` is a two-row registry and one client serves both;
the decision, its alternatives and its costs are
[ADR-0005](../../.claude/docs/adr/0005-one-openai-compatible-endpoint-for-every-provider.md),
and a third provider is
[EXT-011](../../.claude/docs/extension-register.md#ext-011--more-large-language-model-providers-behind-the-seam).
Nothing outside this package names a provider, a model, a key or a message role.

`LanguageModel` is the seam: a system instruction and a user message in, a `Reply`
out — the text the model produced, and the `ModelCall` that produced it.
`ChatCompletions` is the one implementation that reaches a provider, and a caller
that wants a different model passes its own.
"""

import json
import os
import re
import time
from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal
from functools import cache
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from openai import OpenAI

# Keys live here rather than in the shell, because a reviewer following the
# `README.md` puts them in a file. Read without overriding: an environment
# variable already set wins over the file, which is what makes a one-off run
# possible without editing it.
ENV_FILE = Path(__file__).resolve().parent.parent.parent / ".env"


@dataclass(frozen=True, slots=True)
class Provider:
    """One place a model can be called: where it is, what authorises the call, and
    which model it serves unless a caller names another."""

    name: str
    base_url: str
    key_variable: str
    default_model: str


# The whole of what Veritas talks to. Each key variable is the provider's own
# documented name, so a reviewer who already has one has it set already.
PROVIDERS = {
    "openai": Provider(
        name="openai",
        base_url="https://api.openai.com/v1",
        key_variable="OPENAI_API_KEY",
        default_model="gpt-5.4-mini",
    ),
    "groq": Provider(
        name="groq",
        base_url="https://api.groq.com/openai/v1",
        key_variable="GROQ_API_KEY",
        default_model="openai/gpt-oss-120b",
    ),
}

# Which of the two, and which model on it. The default is the provider whose key
# the course itself assumes; Groq is the second model, not the first.
PROVIDER_VARIABLE = "VERITAS_LLM_PROVIDER"
MODEL_VARIABLE = "VERITAS_LLM_MODEL"
DEFAULT_PROVIDER = "openai"

# Consent to spend a key, for anything that would spend one without a person having
# asked this question. A key sitting in `.env` so the App can answer is not consent for
# a test run or a sweep to spend it, and this is the name that says so — read by the
# tests that call a real provider and by the Evaluation sweep that calls one a few
# hundred times.
LIVE_VARIABLE = "VERITAS_LIVE_MODEL"

# Nothing Veritas asks a model is a matter of taste: a resolution the model is
# free to vary between two runs is a resolution a person cannot check.
TEMPERATURE = 0.0

# One question at a time, in front of a person watching a browser tab.
TIMEOUT_SECONDS = 30.0

# How many times a refused call is tried again. A free tier meters tokens per minute
# and answers a call over that meter with a 429 saying how long to wait; the client
# waits that long and asks again, and this is how many times it may. The number is
# above the two the library defaults to because the caller that meets the meter is the
# Evaluation sweep, which asks a few hundred questions as fast as they come back: a
# call it drops is a question its published table then scores as one no model answered.
MAX_RETRIES = 8

# Prices are quoted per million tokens, so a call's cost is its tokens over this.
PER_TOKENS = Decimal(1_000_000)


@dataclass(frozen=True, slots=True)
class Price:
    """What one model's tokens cost per million, and where the figure came from.

    A price is neither a definition nor a measurement of Veritas: nothing in this
    repository can refute it and nothing here can reproduce it, and it changes when a
    vendor decides it does. So each row carries the date it was `read` and the `page`
    it was read from, and a reader who needs to know whether a cost figure is current
    checks the row rather than the code around it.
    """

    prompt: Decimal
    completion: Decimal
    read: str
    page: str


# The one page every row below was read from, and the day it was read.
OPENAI_PRICING = "https://developers.openai.com/api/docs/pricing"
OPENAI_PRICES_READ = "2026-09-03"

# What a call costs, per provider and model. A model absent from this table is not
# free — it is unpriced, and a call on it carries no cost rather than a cost of zero.
#
# The five OpenAI rows are the four candidates Sub-step 8.1 ranked plus the model they
# replaced, all read on one day from one page. **groq is deliberately absent**: its
# price is not on a page this project has read, and the free tier Veritas uses bills
# none of it, so any figure here would be one of two wrong numbers.
PRICES: dict[tuple[str, str], Price] = {
    ("openai", "gpt-5.4-mini"): Price(
        Decimal("0.75"), Decimal("4.50"), OPENAI_PRICES_READ, OPENAI_PRICING
    ),
    ("openai", "gpt-5.4-nano"): Price(
        Decimal("0.20"), Decimal("1.25"), OPENAI_PRICES_READ, OPENAI_PRICING
    ),
    ("openai", "gpt-5-mini"): Price(
        Decimal("0.25"), Decimal("2.00"), OPENAI_PRICES_READ, OPENAI_PRICING
    ),
    ("openai", "gpt-5.6-luna"): Price(
        Decimal("0.20"), Decimal("1.20"), OPENAI_PRICES_READ, OPENAI_PRICING
    ),
    ("openai", "gpt-4o-mini"): Price(
        Decimal("0.15"), Decimal("0.60"), OPENAI_PRICES_READ, OPENAI_PRICING
    ),
}


@dataclass(frozen=True, slots=True)
class ModelCall:
    """One call to one model: who served it, how much text it read and wrote, and how
    long it took.

    What Observability records per model call, and what the Orchestrator hands it. It
    carries no text: a Question Log row says what a question cost and how long it took,
    and the prompt a model was shown is reproducible from the question and the corpus.

    A provider that reports no usage leaves the tokens at zero, which is why `cost` is
    `None` for an unpriced model rather than the zero those tokens would multiply out
    to — a cost of nothing and a cost nobody knows are different things on a chart.
    """

    provider: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    seconds: float = 0.0

    @property
    def cost(self) -> Decimal | None:
        """What this call cost, or `None` where the table does not price the model."""
        price = PRICES.get((self.provider, self.model))
        if price is None:
            return None
        return (
            self.prompt_tokens * price.prompt + self.completion_tokens * price.completion
        ) / PER_TOKENS


@dataclass(frozen=True, slots=True)
class Reply:
    """What a model said, and the call that said it.

    `complete` returns this rather than the text alone because every caller wants the
    text and one caller — the Orchestrator, on behalf of the Question Log — wants what
    the text cost. A call whose usage was thrown away at the seam cannot be costed
    afterwards by anything.

    `call` has no default, so a stub model naming itself is the cheapest thing it can
    do and a stub model naming nothing is not available: an unattributed reply is a
    Question Log row that says a model was asked and cannot say which.
    """

    text: str
    call: ModelCall


# A reply wrapped in a Markdown code fence. A provider asked for a JSON object mostly
# returns one bare; an open model behind the same endpoint may fence it instead, and the
# fence is the whole of the difference. Group 1 of
# '```json\n{"revenue": "Net Revenue"}\n```' is what `json.loads` is given;
# `(?:json)?` because the language tag is optional, `re.DOTALL` so `.` crosses the
# newlines of a multi-line object, and the anchors so the fence has to wrap the whole
# reply rather than merely appear somewhere in it.
#
# It is here rather than beside a caller because it is a **provider** difference: two
# endpoints Veritas supports answer the same request in two shapes, and this package is
# where that is the whole subject.
FENCED = re.compile(r"^\s*```(?:json)?\s*(.*?)\s*```\s*$", re.DOTALL)


class LanguageModelError(RuntimeError):
    """A call that did not come back as usable text.

    Covers the provider refusing, timing out or being unreachable, a reply with no
    text in it, a reply whose shape the caller asked for and did not get, and a
    provider or key the environment does not offer. Every one of them is the same
    thing to a caller: this call produced nothing to read, and the next step must
    not run on a guess.
    """


# A Protocol rather than a base class, because nothing that satisfies this seam
# should have to import it: `ChatCompletions` below, a test's stub model, and
# whatever Step 007 sweeps all count as a `LanguageModel` by having the method.
# Structural, so the dependency points at the caller's need and not at us.
class LanguageModel(Protocol):
    """What Veritas needs from a model, and the whole of it.

    `json_object` asks the provider to constrain the reply to one JSON object.
    Support is not universal, so it is a request rather than a guarantee, and a
    caller that sets it still has to read what came back.
    """

    def complete(
        self, system: str, user: str, json_object: bool = False
    ) -> Reply: ...


class ChatCompletions:
    """One OpenAI-compatible Chat Completions endpoint, held open for the process.

    `base_url` is an argument rather than a registry lookup so a test can point the
    client at a local server; what the environment may select is closed to
    `PROVIDERS`, and `model_for` is the only thing that reads it.

    The client is built once per instance and the `openai` import is deferred to
    that moment, so importing this module costs nothing until something calls a
    model.
    """

    def __init__(
        self,
        model: str,
        base_url: str = PROVIDERS[DEFAULT_PROVIDER].base_url,
        api_key: str = "",
        temperature: float = TEMPERATURE,
        timeout: float = TIMEOUT_SECONDS,
        provider: str = DEFAULT_PROVIDER,
        max_retries: int = MAX_RETRIES,
    ) -> None:
        from openai import OpenAI

        self.model = model
        self.base_url = base_url
        self.temperature = temperature
        self.provider = provider
        self._client: OpenAI = OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
        )

    def __repr__(self) -> str:
        """Model and endpoint, never the key."""
        return f"{type(self).__name__}({self.model!r} at {self.base_url!r})"

    def complete(self, system: str, user: str, json_object: bool = False) -> Reply:
        """The model's reply to one system instruction and one user message, with what
        the call read, wrote and took.

        The clock is this side of the seam because the wall time a person waits is the
        wall time the socket took, and a provider that reports no `usage` leaves the
        tokens at zero — the field is optional in the API this speaks, and a reply with
        no accounting on it is still a reply.
        """
        from openai import OpenAIError

        started = time.perf_counter()
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                temperature=self.temperature,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                **({"response_format": {"type": "json_object"}} if json_object else {}),
            )
        except OpenAIError as error:
            raise LanguageModelError(f"{self!r} refused the call: {error}") from error
        seconds = time.perf_counter() - started

        text = response.choices[0].message.content if response.choices else None
        if not text:
            raise LanguageModelError(f"{self!r} returned no text")
        usage = response.usage
        return Reply(
            text,
            ModelCall(
                provider=self.provider,
                model=self.model,
                prompt_tokens=usage.prompt_tokens if usage else 0,
                completion_tokens=usage.completion_tokens if usage else 0,
                seconds=seconds,
            ),
        )


def model_for(provider: str, model: str | None = None) -> ChatCompletions:
    """A client for one of the supported providers, keyed from the environment.

    The named-model argument is what a comparison across providers holds: each
    provider's models are its own, so a model name is passed with the provider it
    belongs to rather than read from a variable that would follow the sweep.

    Raises `LanguageModelError` naming what is supported when asked for a third
    provider, and naming the key variable when the chosen one has no key.
    """
    from dotenv import load_dotenv

    load_dotenv(ENV_FILE)
    if provider not in PROVIDERS:
        raise LanguageModelError(
            f"{provider!r} is not a provider Veritas supports: set "
            f"{PROVIDER_VARIABLE} to one of {' or '.join(sorted(PROVIDERS))}"
        )
    chosen = PROVIDERS[provider]
    key = os.environ.get(chosen.key_variable, "")
    if not key:
        raise LanguageModelError(
            f"no key for {chosen.name}: put {chosen.key_variable} in the "
            f"environment or in {ENV_FILE.name}"
        )
    return ChatCompletions(
        model=model or chosen.default_model,
        base_url=chosen.base_url,
        api_key=key,
        provider=chosen.name,
    )


@cache
def default_model() -> ChatCompletions:
    """The model the environment configures, built once per process."""
    return model_for(
        os.environ.get(PROVIDER_VARIABLE) or DEFAULT_PROVIDER,
        os.environ.get(MODEL_VARIABLE) or None,
    )


def registered_models(
    providers: Sequence[str] | None = None, models: Sequence[str] | None = None
) -> dict[str, ChatCompletions]:
    """One client per model a sweep runs, keyed by the provider and the model that name
    it — `"openai gpt-5.4-mini"`.

    Unnarrowed, that is every supported provider on its own default model: the whole of
    `PROVIDERS` rather than a list written somewhere else, so a provider reaches an
    evaluation by being registered here and not by being named twice.

    `providers` narrows that to a named subset, and `models` replaces the model the one
    named serves with **as many of its models as are asked for** — which is what a sweep
    comparing one provider's models against each other runs over, and it costs that
    provider alone. Neither widens what is supported: an unregistered provider raises
    through `model_for` exactly as it does anywhere else.

    The key carries the provider because two providers can serve models of the same
    name, and a table of rows that cannot say which endpoint answered is a comparison
    of nothing.

    Raises `LanguageModelError` for the first provider with no key, because a sweep that
    quietly dropped an arm would publish a comparison it never made, and for models
    asked of more than one provider, because a model name belongs to the provider that
    serves it.
    """
    chosen = tuple(PROVIDERS if providers is None else providers)
    if models and len(chosen) != 1:
        raise LanguageModelError(
            f"{', '.join(map(repr, models))} name one provider's models, so they can be "
            f"asked of one provider and not of {len(chosen)}"
        )
    wanted = (
        [(chosen[0], model) for model in models]
        if models
        else [(name, None) for name in chosen]
    )
    built = [(name, model_for(name, model)) for name, model in wanted]
    return {f"{name} {client.model}": client for name, client in built}


def json_reply(reply: str) -> dict[str, object]:
    """The JSON object a reply carries, fence or no fence.

    Every caller that sets `json_object` has to read what came back, because the flag is
    a request rather than a guarantee, and all of them want the same thing from a reply
    that is not one object: to stop. A reply that is valid JSON and not an object — a
    list, a bare string — is the same failure as one that is not JSON at all.

    Raises `LanguageModelError`, because this is the provider failing rather than the
    question being unanswerable, and a caller must be able to tell those apart.
    """
    fenced = FENCED.match(reply)
    try:
        answer = json.loads(fenced.group(1) if fenced else reply)
    except json.JSONDecodeError as error:
        raise LanguageModelError(f"reply is not JSON: {reply!r}") from error
    if not isinstance(answer, dict):
        raise LanguageModelError(f"reply is not a JSON object: {reply!r}")
    return answer
