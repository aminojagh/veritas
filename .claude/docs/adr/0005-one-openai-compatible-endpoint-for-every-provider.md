# ADR-0005 — Every model call goes through one OpenAI-compatible endpoint

- **Status:** accepted
- **Date:** 2026-08-30
- **Decided in:** Step 006, Sub-step 6.3

## Context

Sub-step 6.3 is the first place Veritas calls a Large Language Model (LLM), so it
is the Sub-step that has to say *which* one. Three constraints were fixed before
it started, and a fourth arrived while it was being reviewed.

The [Target State's credential rule](../design/target-state.md#what-credential-free-means)
settles what a reviewer may be asked for: *"A credential the grader already has
by virtue of taking the course is acceptable. A credential unique to this project
is not."*

The [Zoomcamp criteria map](../design/target-state.md#zoomcamp-criteria-map)
settles that one model is not enough: full marks for LLM evaluation need
*"Execution Accuracy across ≥2 prompts and ≥2 models"*. Whatever 6.3 chooses,
Step 007 has to run a second model through the same code and compare the numbers,
so the model is a value that varies at run time rather than a library that is
imported.

Three more calls are coming behind this one — SQL generation in 6.4, and Step
007's second model and LLM-as-judge — and all of them are text in, text out. None
of them needs streaming, embeddings (Retrieval has its own models), or a
provider-specific feature.

**Amino ruled on 2026-08-30**, before this Sub-step was reviewed, and the ruling
narrows the field the first draft of this ADR left open:

> *"the only non-free llm api key that a reviewer of this project has is the
> open_api_key as requested by the LLM-Zoomcamp course itself. so that will be the
> only non-free one for us as well. we won't use any local api endpoints such as
> ollama because we don't want to make this complicated by setting up and
> maintaining that local service. if we need another LLM provider other than
> open_ai for evaluation criteria, we should use the best provider that also
> provides free-tier service … we should restrict the supported LLM providers to
> these two for now and make it an extension to support more options."*

So the question is not *which endpoint shape* — it is *which two providers*, and
how the code refuses a third.

## Decision

One seam, `LanguageModel` — a system instruction and a user message in, the text
the model produced out. One implementation behind it, `ChatCompletions`, an
OpenAI-compatible Chat Completions client. And a **closed registry of exactly two
providers**, `PROVIDERS`, each carrying its base Uniform Resource Locator (URL),
its key variable and its default model:

| Provider | Base URL | Key variable | Default model | Role |
|---|---|---|---|---|
| `openai` | `https://api.openai.com/v1` | `OPENAI_API_KEY` | `gpt-5.4-mini` | The default. The key the course already asks a grader for, on the model that measured best of four — below. |
| `groq` | `https://api.groq.com/openai/v1` | `GROQ_API_KEY` | `openai/gpt-oss-120b` | The second model. Free tier, no card, optional. |

`VERITAS_LLM_PROVIDER` selects between them and `VERITAS_LLM_MODEL` names a model
on the selected one; a value that is not one of the two raises
`LanguageModelError` naming both. Keys are each provider's own documented variable
name, read from the environment or from `.env`, which the client loads without
overriding what is already set. Nothing outside `veritas/llm/` names a provider, a
model, a key or a message role.

**Why Groq is the second.** It is the only candidate that changes no code: its
endpoint is Chat Completions at a base URL, including `temperature` and
`response_format`, so the second model costs one registry row rather than a second
client. Its free tier needs no card and no billing account, which keeps the
credential rule's *obtained versus assumed* line as short as it can be for a key
that is optional anyway. And it serves a different model — `openai/gpt-oss-120b`,
open weights on Groq's own hardware, against OpenAI's hosted model — which is what
makes Step 007's *"≥2 models"* two models rather than one model twice.

**Why that model and not the one this ADR first named.** The row read
`llama-3.3-70b-versatile` until a key existed to call it, and the first call was a
404: *"The model `llama-3.3-70b-versatile` does not exist or you do not have access
to it."* The
[Sub-step 6.3 review](../reviews/step-006-retrieval-and-orchestrator.md#sub-step-63--resolve-ambiguous-terms-before-retrieval)
carries that run and the one that replaced it. Of what the key does serve,
`openai/gpt-oss-120b` is the largest model Groq lists as production rather than
preview; the two Qwen models are the family-diverse candidates and Groq lists both
as preview, for evaluation and not for production use, so they are what
`VERITAS_LLM_MODEL` names for an arm of Step 007's sweep rather than what the
registry defaults to. **The cost is that both default models are OpenAI-authored**
— `gpt-oss-120b` is open weights served by someone else, not a second OpenAI
product, but the *"different vendor's family"* half of the reason above is now the
sweep's to buy, not the default's.

**Why `gpt-5.4-mini` and not the model this ADR first defaulted to.** The OpenAI row
read `gpt-4o-mini` from the day it was written, and what this ADR argued for was the
**provider** — *"the key the course already asks a grader for"* is a sentence about a
key, not about a catalogue. Step 007 measured what that cost: over the Gold Question
Set it answered two of the eleven answerable questions correctly against Groq's ten.
Sub-step 8.1 measured four OpenAI models against Groq's mark, cheapest first by the
published input price, and took the first to reach it — `gpt-5.4-mini`, at eleven of
eleven. The prices, the date they were read, the page they were read from and the
per-candidate figures are in the
[Sub-step 8.1 review](../reviews/step-008-observability.md#sub-step-81--choose-the-openai-default-model-by-measurement).
**Groq's row is untouched.** The registry is keyed by provider and holds one model
each, so carrying a second *OpenAI* model instead of it is not something this seam can
express, and reworking the seam is not bought before the deadline.

## Alternatives considered

| Option | Why not |
|---|---|
| **Ollama as a zero-key fallback**, which the Target State named | Ruled out by Amino above: *"we don't want to make this complicated by setting up and maintaining that local service"*. It also fails the half of the rubric it was meant to protect — a local 3-billion-parameter model writing SQL against nine Metric Definitions is the weakest link in a project whose whole claim is that the SQL is grounded. The Target State's credential row and `README.md` requirement are narrowed to match. |
| **A base URL the environment sets freely**, as this ADR's first draft had | It is how the two-provider rule would be true in prose and false in code: any endpoint at all becomes reachable by setting a variable, and the third provider arrives without anyone deciding to support it. `base_url` stays an argument on the client, which is what the stub-server test uses, and the environment chooses from `PROVIDERS`. |
| **Google Gemini as the second provider** — the runner-up | Its free tier is at least Groq's equal and `gemini-2.5-flash` is the stronger model. What it is not is the same Application Programming Interface: Gemini serves an OpenAI-compatibility layer beside its own, with its own coverage of `response_format` and its own error shapes. This ADR's whole value is that a second provider is a registry row; a compatibility shim is where that stops being true. |
| **Cerebras, Mistral, OpenRouter** | All have free tiers and all are OpenAI-compatible, so any of them would work. None of them beats Groq on the three things that decided it, and picking more than one is the thing Amino's ruling forbids. Any of them is a row in `PROVIDERS` the day a reason appears — [EXT-011](../extension-register.md#ext-011--more-large-language-model-providers-behind-the-seam). |
| **One provider's own client library** — `anthropic` or `groq` | Each is a better fit for its own provider and none of them is a fit for two. Step 007 has to run a second model, and with a vendor library that is a second import, a second call shape and a second error type, all of which the comparison then has to hold constant. |
| **A provider-abstraction library** — LiteLLM, LangChain | Solves exactly this problem, and solves several others at the same time. What Veritas needs from a model is one function of two strings; what these bring is a framework's worth of surface, its own vocabulary next to the Glossary's, and a dependency whose upgrades are on someone else's schedule. The abstraction being bought is fifteen lines. |
| **OpenAI's Responses API**, its newer endpoint | It is the one OpenAI is building on, and it is the wrong shape for a two-provider registry: Groq serves Chat Completions and does not serve Responses, so choosing it puts a second client behind the seam on the day the second provider arrives — the exact cost this ADR exists to avoid. What it adds over Chat Completions is server-held conversation state, built-in tools, and background runs; Veritas sends one system instruction and one user message, stateless, and reads text back. `temperature` and a JSON-object constraint, which are the only two things it does ask for, are on both. |
| **Hand-rolled HTTP against the same endpoint** | Genuinely close, and it adds no dependency at all — `httpx` is already in the tree. What it gives up is the typed error hierarchy that `LanguageModelError` wraps, retries on a flaky connection, and the certainty that a request Veritas builds by hand is the request every provider documents. |

## Consequences

**What this buys us.** A second model is a second value of one environment
variable, so Step 007's *"≥2 models"* is a parameter sweep rather than a port, and
`model_for(provider, model)` is the function that sweep calls. A reviewer needs
one key, the one the course already told them to get, and the second is free and
optional. A provider Veritas has not decided to support is a `LanguageModelError`
rather than a request on the wire. Tests need no key and no network: the seam
takes a stub, and `tests/test_llm.py` runs the real client against a local server
that speaks the same API.

**What this costs us.**

- **A default model name is a claim about someone else's catalogue, and this one
  was wrong.** The ADR shipped `llama-3.3-70b-versatile` on Groq's published
  catalogue with no key to try it; the first call with a key 404'd, and the row now
  reads `openai/gpt-oss-120b`, which the same committed live test passes against.
  *Classified: accepted, and it has now fired once* — the failure mode is exactly
  what was predicted, a 404 naming the model, and the repair is one string or one
  `VERITAS_LLM_MODEL`. What that costs is stated in the bullet below: two strings
  here name things on a roadmap this project does not control.
- **`temperature` and `response_format` are sent to both providers.** Newer
  OpenAI reasoning models reject a temperature that is not the default, and an
  open model may ignore a JSON-object request and fence its answer instead.
  *Classified: accepted, and the first has now fired* — two of the four candidates
  Sub-step 8.1 priced, `gpt-5-mini` and `gpt-5.6-luna`, answered every call with a
  400 naming the parameter: *"'temperature' does not support 0.0 with this model.
  Only the default (1) value is supported."* That is the loud failure this bullet
  predicted. What the prediction got wrong is the repair. *"The fix is one
  variable"* holds only if running at a temperature the provider chooses is
  acceptable, and it is not — a resolution a model is free to vary between two runs
  is one a person cannot check, which is why `TEMPERATURE` is pinned at all. So the
  cost is narrower and larger than written: **a model that will not take temperature
  0 is not selectable, at any price**, and two of four candidates were ruled out
  before a figure was measured on either. The second case is why `resolutions_in`
  reads a fenced reply as well as a bare one, and why a reply that is not a JSON
  object raises rather than being read as an ambiguity.
- **A default model name will be deprecated by its provider eventually.** Two
  strings in this repository name things on someone else's roadmap.
  *Classified: accepted* — the signal is a 404 from the provider naming the model,
  and the repair is `VERITAS_LLM_MODEL`. Pinning a model that never moves is not
  on offer from either provider here.
- **Two dependencies** — `openai`, which brings pydantic and `httpx2`, and
  `python-dotenv`, which is what makes a key in a file reach the process.
  *Classified: accepted* — the alternative to the first is the hand-rolled client
  above, and the alternative to the second is telling a reviewer to export a
  variable in every shell they open.
- **A third provider is not reachable without a code change.** *Classified:
  extension* — [EXT-011](../extension-register.md#ext-011--more-large-language-model-providers-behind-the-seam),
  which is the shape Amino's ruling asked for: *"make it an extension to support
  more options"*. The seam it lands against is `PROVIDERS`, and the change is a row.

**What it commits us to.** That both providers keep serving Chat Completions at a
configurable base URL. The signal that this had stopped holding is a provider
deprecating the endpoint in favour of its own — OpenAI's Responses API is the live
example — at which point the repair is one more class behind `LanguageModel` and
no caller changes, which is the property this ADR is buying.

## Related

- Extension Register:
  [EXT-011](../extension-register.md#ext-011--more-large-language-model-providers-behind-the-seam)
  — a third provider, and why it is an extension rather than debt.
- Debt Ledger:
  [DEBT-028](../debt-ledger.md#debt-028--no-test-reaches-a-real-provider-so-the-live-path-is-proven-only-by-a-stub-server),
  paid in the same Sub-step.
- Glossary: no new terms. `veritas/llm/` is plumbing behind the
  [Orchestrator](../glossary.md#a-the-system), which owns the flow that calls it.
- Related: [ADR-0003](0003-validation-gate-is-deterministic-code.md) — what a
  model is *not* allowed to be trusted with, which is why this one is a small
  seam rather than a framework.
