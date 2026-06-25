# 04 · Conventions

> Coding patterns shared across `server/` and `web/`. Follow these to keep local and deployed modes aligned and the filter seam clean.

## Boundary ownership

- Browser code calls only `/api/*`. Backend placement is hidden behind Next rewrites (`web/next.config.ts`).
- **Never** add `web/app/api/**/route.ts` for agent/token logic — `verify-api-contracts.ts` fails the build if a `route.ts` appears under `app/api`.
- Token generation and the App Certificate stay in `server/`.
- `server/src/llm.py` must **not** import `agora_agent` — `test_llm_mount.py` asserts this via AST inspection.

## Backend (Python / FastAPI)

- Async throughout: route handlers are `async def`; the agent uses `AsyncAgora` and `create_async_session`.
- Request bodies are Pydantic models (`StartAgentRequest`, `StopAgentRequest`). Field names are **camelCase** (`channelName`, `rtcUid`, `userUid`) to match the browser client.
- Error mapping is centralized: `_to_http_error()` maps `ValueError → 400`, `RuntimeError → 500`, else 500. `_log_route_error()` logs with safe context + traceback. Raise plain `ValueError`/`RuntimeError`; let the route convert.
- Logging via `logging.getLogger("uvicorn.error")`.
- Env read with `os.getenv`; `.env.local` then `.env` loaded at module import.

## Response envelope

All backend JSON responses (token/agent routes) use:

```json
{ "code": 0, "msg": "success", "data": { } }
```

`data` is present only when the route returns a payload. The browser client treats `code !== 0` (or missing `data`) as an error.

> The `/llm/chat/completions` route uses the **OpenAI SSE format**, not this envelope — it is the Agora-cloud-facing contract.

## Filter seam conventions

- `moderate(sentence: str) -> bool` is the pluggable seam. Return `True` to allow, `False` to redact. Replace only this body; leave `filter_reply` and `run_agent_turn` untouched unless you change sentence-splitting behavior.
- `filter_reply(text)` splits on `(?<=[.!?])\s+` (sentence boundaries). Redacted sentences are replaced with `REDACTION = "Content filtered."`.
- `echo_reply(user_text)` is the mock generator. Replace it with a real LLM call to get real responses that still run through the filter.
- Never call `get_mock_response` — that symbol was removed. Use `run_agent_turn`.

## `/llm/chat/completions` SSE contract

- Accept only `stream: true` requests; return 400 for non-streaming.
- First SSE chunk: `delta: { role: "assistant", content: "" }`.
- Content chunks: `delta: { content: "<token>" }`, `finish_reason: null`.
- Final chunk: `delta: {}`, `finish_reason: "stop"`.
- Terminator: `data: [DONE]`.

## Web (TypeScript / Next.js)

- Lint/format with Biome (`bun run lint`, `bun run lint:fix` in `web/`).
- RTC client creation must be StrictMode-safe (strict mode is on).
- Transcript speaker mapping uses real UIDs; do not heuristically guess speakers.
- API client lives in `src/services/api.ts`; UI never calls `fetch` to the backend directly.

## Testing approach

- Backend: `pytest` in `server/`, standalone — `conftest.py` fakes env and SDK session, so no cloud or real creds are needed.
- Web: contract/proxy/fastapi/llm smoke scripts under `web/scripts/` run without live Agora calls.
- Run the **narrowest** relevant verify command before finishing (see [05_workflows](05_workflows.md)).

## Doc upkeep

When you change request/response contracts, env vars, or workflow, update the web client, backend, contract checks, README, **and** the matching `docs/ai/L1/` file together, then bump `Last Reviewed` in [L0](../L0_repo_card.md).

## Related Deep Dives

- None.
