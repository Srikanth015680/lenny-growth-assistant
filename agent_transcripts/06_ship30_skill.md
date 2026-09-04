# 06 — Ship30 skill

First built as an honest `NotImplementedError` placeholder (with the API
contract already wired to a 501 response) while the provider/RAG layers
were still being built underneath it — deliberate, so the API surface was
stable to build the frontend against without pretending the skill worked
yet.

Once retrieval + providers were verified, implemented it for real:
`ship30_prompts.py` (structural rules — hook, headings, ~1,250 words,
grounding) + `ship30_writer.py` (calls the resolved provider's
`generate_response` with that prompt). Raises `InsufficientContextError`
(422) when retrieval found nothing, rather than letting the model write an
essay about nothing — same grounding discipline as plain chat.

Wired into `orchestrator.run_ship30` (retrieve → emit sources → generate
→ wrap as a Markdown artifact → persist) and `api/chat.py`'s mode
dispatch. Verified via mocked-provider tests (`test_ship30.py`) and an
end-to-end SSE test confirming the artifact event, persistence, and
message linkage all happen correctly (`test_api.py`).
