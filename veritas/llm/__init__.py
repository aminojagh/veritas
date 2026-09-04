"""The Large Language Model boundary — one client, one seam, one place a provider
is named.

`model.py` holds the seam, the two supported providers, the OpenAI-compatible client
behind both, and what a call to one costs.
"""

from veritas.llm.model import (
    DEFAULT_PROVIDER,
    ENV_FILE,
    FENCED,
    LIVE_VARIABLE,
    MODEL_VARIABLE,
    PER_TOKENS,
    PRICES,
    PROVIDER_VARIABLE,
    PROVIDERS,
    TEMPERATURE,
    TIMEOUT_SECONDS,
    ChatCompletions,
    LanguageModel,
    LanguageModelError,
    ModelCall,
    Price,
    Provider,
    Reply,
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
    "PER_TOKENS",
    "PRICES",
    "PROVIDERS",
    "PROVIDER_VARIABLE",
    "TEMPERATURE",
    "TIMEOUT_SECONDS",
    "ChatCompletions",
    "LanguageModel",
    "LanguageModelError",
    "ModelCall",
    "Price",
    "Provider",
    "Reply",
    "default_model",
    "json_reply",
    "model_for",
    "registered_models",
]
