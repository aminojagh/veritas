"""The one boundary through which Veritas calls a Large Language Model.

Veritas supports two providers and no others — OpenAI, which the Large Language
Model Zoomcamp already asks a grader for, and Groq, whose free tier supplies the
second model the evaluation criterion needs. Both speak the OpenAI Chat
Completions API, so `PROVIDERS` is a two-row registry and one client serves both;
the decision, its alternatives and its costs are
[ADR-0005](../../.claude/docs/adr/0005-one-openai-compatible-endpoint-for-every-provider.md),
and a third provider is
[EXT-011](../../.claude/docs/extension-register.md#ext-011--more-large-language-model-providers-behind-the-seam).
Nothing outside this package names a provider, a model, a key or a message role.

`LanguageModel` is the seam: a system instruction and a user message in, the text
the model produced out. `ChatCompletions` is the one implementation that reaches a
provider, and a caller that wants a different model passes its own.
"""

import os
from dataclasses import dataclass
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
        default_model="gpt-4o-mini",
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

# Nothing Veritas asks a model is a matter of taste: a resolution the model is
# free to vary between two runs is a resolution a person cannot check.
TEMPERATURE = 0.0

# One question at a time, in front of a person watching a browser tab.
TIMEOUT_SECONDS = 30.0


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

    def complete(self, system: str, user: str, json_object: bool = False) -> str: ...


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
    ) -> None:
        from openai import OpenAI

        self.model = model
        self.base_url = base_url
        self.temperature = temperature
        self._client: OpenAI = OpenAI(
            api_key=api_key, base_url=base_url, timeout=timeout
        )

    def __repr__(self) -> str:
        """Model and endpoint, never the key."""
        return f"{type(self).__name__}({self.model!r} at {self.base_url!r})"

    def complete(self, system: str, user: str, json_object: bool = False) -> str:
        """The model's reply to one system instruction and one user message."""
        from openai import OpenAIError

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

        text = response.choices[0].message.content if response.choices else None
        if not text:
            raise LanguageModelError(f"{self!r} returned no text")
        return text


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
    )


@cache
def default_model() -> ChatCompletions:
    """The model the environment configures, built once per process."""
    return model_for(
        os.environ.get(PROVIDER_VARIABLE) or DEFAULT_PROVIDER,
        os.environ.get(MODEL_VARIABLE) or None,
    )
