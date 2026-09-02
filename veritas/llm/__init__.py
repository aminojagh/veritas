"""The Large Language Model boundary — one client, one seam, one place a provider
is named.

`model.py` holds the seam, the two supported providers, and the OpenAI-compatible
client behind both.
"""

from veritas.llm.model import (
    DEFAULT_PROVIDER,
    ENV_FILE,
    FENCED,
    LIVE_VARIABLE,
    MODEL_VARIABLE,
    PROVIDER_VARIABLE,
    PROVIDERS,
    TEMPERATURE,
    TIMEOUT_SECONDS,
    ChatCompletions,
    LanguageModel,
    LanguageModelError,
    Provider,
    default_model,
    json_reply,
    model_for,
    registered_models,
)

__all__ = [
    "DEFAULT_PROVIDER",
    "ENV_FILE",
    "FENCED",
    "LIVE_VARIABLE",
    "MODEL_VARIABLE",
    "PROVIDERS",
    "PROVIDER_VARIABLE",
    "TEMPERATURE",
    "TIMEOUT_SECONDS",
    "ChatCompletions",
    "LanguageModel",
    "LanguageModelError",
    "Provider",
    "default_model",
    "json_reply",
    "model_for",
    "registered_models",
]
