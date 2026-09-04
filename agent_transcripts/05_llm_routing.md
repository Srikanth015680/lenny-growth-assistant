# 05 — LLM routing / provider abstraction

Built `BaseLLMProvider` first (the interface), then `OllamaProvider`
(httpx against Ollama's `/api/chat`, both streaming and non-streaming) and
`AnthropicProvider` (the `anthropic` SDK's async client), then
`ProviderFactory` last, so the factory could be written against an
interface that already existed rather than growing organically around one
provider.

No live Ollama or Anthropic account was available in this sandbox, so
provider tests use `respx` to intercept the Ollama HTTP calls and a fake
provider class matching `BaseLLMProvider`'s interface for
Anthropic-adjacent chat-flow tests — 11 provider tests, all passing,
covering success, connection failure, timeout, streaming chunk assembly,
and health-check model-missing detection.

Also built the agent routing layer (`router.py`, `orchestrator.py`) here:
`resolve_mode()` is driven by the request's explicit `mode` field rather
than string-matching the message — the spec's own "don't make routing
depend on fragile keyword matching" instruction, satisfied by making mode
a structured enum on the request contract instead. Left a documented,
inert seam (`infer_mode_from_text`) for later free-text intent inference
rather than half-implementing it.
