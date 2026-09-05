
# 05 — LLM Routing and Provider Abstraction

## Goal

Support both local and cloud LLMs without coupling the rest of the
application to a specific provider.

## Work Completed

Implemented a common `BaseLLMProvider` interface and added:

- `OllamaProvider`
- `AnthropicProvider`
- `ProviderFactory`

The Ollama provider supports both normal and streaming responses.

The Anthropic provider uses the Anthropic async SDK.

The rest of the application interacts with the provider interface rather than
calling Ollama or Anthropic directly.

## Provider Selection

The provider can be selected through application configuration.

Ollama is the default provider for local development and the demo.

Anthropic can be enabled when an API key is configured.

The application handles provider connection failures and timeouts without
exposing implementation details to the user.

## Testing

There was no live Ollama service or Anthropic API available during this part
of development, so external calls were mocked.

Tests covered:

- successful provider responses
- connection failures
- timeouts
- streaming responses
- missing Ollama models
- provider selection

This allowed the provider layer to be tested without depending on an
external service or API key.

## Agent Routing

Implemented the agent routing layer with:

- `router.py`
- `orchestrator.py`

The request contract contains an explicit mode instead of trying to infer
the mode from message keywords.

Supported modes are:

- `default`
- `ship30`
- `artifact`

This keeps routing predictable and allows the frontend to explicitly request
a particular capability.

A separate extension point was left for future free-text intent detection,
but it is not used by the current routing path.

## Result

The application can switch between local and cloud LLM providers without
changing the rest of the chat implementation.

The next step is to connect the routing/orchestration layer to the RAG
pipeline and the individual skills.
