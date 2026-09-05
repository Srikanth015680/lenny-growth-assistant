
# 06 — Ship 30 for 30 Skill

## Goal

Add a dedicated skill that turns grounded transcript-based answers into a
Ship 30 for 30-style essay.

## Initial Implementation

The skill was initially added as a placeholder while the RAG and provider
layers were still being developed.

The API contract was wired first so the frontend could be developed against
the expected interface without pretending that essay generation was already
available.

The placeholder returned a `501 Not Implemented` response.

## Implementation

Once the retrieval and LLM provider layers were working, the skill was
implemented.

Added:

- `ship30_prompts.py`
- `ship30_writer.py`

The writing instructions cover:

- strong hook
- clear narrative progression
- headings
- skimmable formatting
- approximately 1,250 words
- actionable takeaway
- grounding in transcript sources

The writer receives the retrieved transcript context and uses the selected
LLM provider to generate the essay.

## Grounding

The skill does not generate an essay when there is no supporting transcript
context.

When retrieval returns no usable context, an `InsufficientContextError` is
returned instead.

This keeps the Ship 30 skill consistent with the grounding behavior used by
normal chat.

## Integration

Connected the skill to the agent orchestrator:

1. Retrieve relevant transcript chunks.
2. Emit the sources.
3. Generate the essay.
4. Wrap the result as a Markdown artifact.
5. Persist the artifact.
6. Link it to the assistant message.

The chat API dispatches to this flow when the `ship30` mode is selected.

## Testing

Added tests for:

- Ship 30 generation with a mocked provider
- insufficient retrieval context
- SSE artifact events
- artifact persistence
- message/artifact relationship

## Result

The Ship 30 skill is now implemented as a separate capability rather than
being embedded directly in the chat endpoint.
