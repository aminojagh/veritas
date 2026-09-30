# ADR-0005 — Every model call goes through one OpenAI-compatible endpoint

- **Status:** accepted

## Context

Veritas calls a Large Language Model (LLM) to resolve Ambiguous Terms, to generate
SQL, and to judge answers in Evaluation. Every call is text in, text out: none needs
streaming, embeddings (Retrieval has its own models), or a provider-specific feature.
Four forces decide which models those calls reach.

The [Target State's credential rule](../design/target-state.md#what-credential-free-means)
settles what a reviewer may be asked for: *"A credential the grader already has by
virtue of taking the course is acceptable. A credential unique to this project is
not."* The one paid key a Zoomcamp grader holds is the OpenAI key the course asks for.

The rubric's LLM-evaluation row asks that *"Multiple approaches are evaluated, and the
best one is used"*. Its example of an approach is *"one prompt"*, so the model is a
value that varies at run time — a sweep runs several through the same code — rather
than a library that is imported.

Amino's ruling closes the field: the OpenAI key is the only paid one Veritas assumes,
nothing runs a local model service, a second provider must be the best one with a free
tier, and support stops at those two — *"make it an extension to support more
options"*.

## Decision

One seam, `LanguageModel` — a system instruction and a user message in, the text the
model produced out. One implementation behind it, `ChatCompletions`, an
OpenAI-compatible Chat Completions client. And a **closed registry of exactly two
providers**, `PROVIDERS`, each carrying its base Uniform Resource Locator (URL), its
key variable and its default model:

| Provider | Base URL | Key variable | Default model | Role |
|---|---|---|---|---|
| `openai` | `https://api.openai.com/v1` | `OPENAI_API_KEY` | `gpt-5.4-mini` | The default. The key the course already asks a grader for. |
| `groq` | `https://api.groq.com/openai/v1` | `GROQ_API_KEY` | `openai/gpt-oss-120b` | A second registered provider. Free tier, no card, optional; no published figure depends on it. |

`VERITAS_LLM_PROVIDER` selects between them and `VERITAS_LLM_MODEL` names a model on
the selected one; a value that is not one of the two raises `LanguageModelError`
naming both. `registered_models` builds one client per (provider, model) pair a sweep
names, so several of one provider's models are swept together. Keys are each
provider's own documented variable, read from the environment or from `.env`, which
the client loads without overriding what is already set. Nothing outside
`veritas/llm/` names a provider, a model, a key or a message role.

**Groq is the second provider** because it changes no code: its endpoint is Chat
Completions at a base URL, including `temperature` and `response_format`, so a second
provider costs one registry row rather than a second client. Its default is the
largest model Groq lists as production rather than preview.

**The OpenAI default is chosen by measurement**: it is the model of the best
(model, prompt) combination the generation grid finds — [ADR-0007](0007-evaluation-scores-within-a-tolerance-and-picks-defaults-by-measurement.md).

**Every call runs at `TEMPERATURE = 0`**, because a resolution a model is free to vary
between two runs is one a person cannot check. A model that refuses temperature 0 is
therefore not selectable at any price.

**A call is costed at the provider's list price**, from `PRICES`: one row per
(provider, model), each carrying the page it was read from and the date it was read.
A model no row prices costs `None`, never zero — a cost of nothing and a cost nobody
knows are different things on a chart.

## Alternatives considered

| Option | Why not |
|---|---|
| **Ollama as a zero-key fallback** | Ruled out by the ruling above: a local service is one more thing to set up and maintain. It also weakens what it was meant to protect — a small local model writing SQL is the weakest link in a project whose claim is that the SQL is grounded. |
| **A base URL the environment sets freely** | It is how the two-provider rule would be true in prose and false in code: any endpoint becomes reachable by setting a variable, and a third provider arrives without anyone deciding to support it. `base_url` stays an argument on the client, which is what the stub-server test uses, and the environment chooses from `PROVIDERS`. |
| **Google Gemini as the second provider** | Its free tier is at least Groq's equal and its models are strong. What it is not is the same Application Programming Interface: its OpenAI-compatibility layer has its own coverage of `response_format` and its own error shapes, and a compatibility shim is where *a second provider is a registry row* stops being true. |
| **Cerebras, Mistral, OpenRouter** | All have free tiers and all are OpenAI-compatible. None beats Groq on the reasons above, and supporting more than one is what the ruling forbids. Any of them is a row in `PROVIDERS` the day a reason appears — [EXT-011](../extension-register.md#ext-011--more-large-language-model-providers-behind-the-seam). |
| **One provider's own client library** — `anthropic` or `groq` | Each fits its own provider and none fits two. A sweep across providers would then hold constant a second import, a second call shape and a second error type. |
| **A provider-abstraction library** — LiteLLM, LangChain | Solves this problem and several others. What Veritas needs is one function of two strings; what these bring is a framework's surface, a vocabulary beside the Glossary's, and upgrades on someone else's schedule. |
| **OpenAI's Responses API** | The endpoint OpenAI is building on, and the wrong shape for a two-provider registry: Groq serves Chat Completions and not Responses. What Responses adds — server-held state, built-in tools, background runs — Veritas does not use; `temperature` and a JSON-object constraint are on both. |
| **Hand-rolled HTTP against the same endpoint** | Close, and it adds no dependency — `httpx` is already in the tree. It gives up the typed error hierarchy `LanguageModelError` wraps, retries on a flaky connection, and the certainty that a hand-built request is the one every provider documents. |
| **`gpt-4o-mini` as the OpenAI default, `llama-3.3-70b-versatile` as Groq's** | The defaults this registry first carried. The first answered far fewer Gold Questions correctly than the models the grid ranks above it; the second is not served to a Groq key, and the call fails naming the model. |

## Consequences

**What this buys us.** A second model is a second value of one variable, so the
(model, prompt) grid is a parameter sweep rather than a port. A reviewer needs one
key, the one the course already told them to get. A provider Veritas has not decided
to support is a `LanguageModelError` rather than a request on the wire. Tests need no
key and no network: the seam takes a stub, and `tests/test_llm.py` runs the real
client against a local server that speaks the same API.

**What this costs us.**

- **A default model name is a claim about someone else's catalogue**, and a provider
  deprecates models on its own roadmap. *Accepted* — the signal is a 404 naming the
  model, and the repair is one string or `VERITAS_LLM_MODEL`. Pinning a model that
  never moves is not on offer from either provider.
- **`temperature` and `response_format` are sent to both providers.** Newer OpenAI
  reasoning models reject a temperature that is not the default, with a 400 naming
  the parameter, and an open model may fence its JSON answer. *Accepted* — the first
  rules such a model out, loudly; the second is why `json_reply` reads a fenced reply
  as well as a bare one, and raises on a reply that is not a JSON object.
- **A list price is not an invoice, and nothing re-reads the pages.** A price that
  moves produces figures exactly as authoritative-looking as correct ones, and a call
  served on a free tier still carries its list price. *Accepted* — the cost column
  means *"what this would have cost at list prices on the date read"*, and each row
  names that date and page.
- **A question the provider never answered is not a Question Log row.** The row
  is a Grounded Answer, and a failed call is not one: the Orchestrator raises
  `LanguageModelError`, and the App tells the User why and returns before
  recording. So the dashboard's counts by the step that ended a question
  undercount by exactly those questions. *Accepted* — widening `record` to take a failure puts a second shape
  through the Observability seam, for the one failure that says nothing about the
  question.
- **Two dependencies** — `openai`, which brings pydantic and `httpx2`, and
  `python-dotenv`, which is what makes a key in a file reach the process.
  *Accepted* — the alternative to the first is the hand-rolled client above, and to
  the second is telling a reviewer to export a variable in every shell.
- **A third provider is not reachable without a code change.** *Extension* —
  [EXT-011](../extension-register.md#ext-011--more-large-language-model-providers-behind-the-seam).
  The seam it lands against is `PROVIDERS`, and the change is a row.

**What it commits us to.** That both providers keep serving Chat Completions at a
configurable base URL. The signal that this has stopped holding is a provider
deprecating the endpoint in favour of its own — OpenAI's Responses API is the live
example — at which point the repair is one more class behind `LanguageModel` and no
caller changes.

## Related

- [ADR-0003](0003-validation-gate-is-deterministic-code.md) — what a model is *not*
  trusted with, which is why this is a small seam rather than a framework.
- [ADR-0007](0007-evaluation-scores-within-a-tolerance-and-picks-defaults-by-measurement.md)
  — how the default model and prompt are chosen, and how far a single run's figures
  can be read.
- Glossary: no new terms. `veritas/llm/` is plumbing behind the
  [Orchestrator](../glossary.md#a-the-system), which owns the flow that calls it.
