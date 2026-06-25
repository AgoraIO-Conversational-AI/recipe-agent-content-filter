# 05 · Workflows

> Step-by-step guides for the common changes in this recipe. Each ends with the narrowest verify command to run.

## Swap the moderation logic (replace `moderate()`)

This is the most common customization. Replace the body of `moderate()` in `server/src/llm.py`:

1. Edit `moderate(sentence: str) -> bool` — make your moderation call (API, local model, keyword list).
2. Add any new env vars for your moderation service; document in `server/.env.example` and README.
3. Keep `filter_reply` and `run_agent_turn` intact.
4. Verify: `bun run verify:backend` (compile) + `cd server && pytest tests -v`.

## Replace the mock generator (replace `echo_reply()`)

To swap the mock for a real LLM call while keeping the filter:

1. Replace the body of `echo_reply(user_text: str) -> str` in `server/src/llm.py` with a real LLM call.
   The function must return a plain string; `filter_reply` splits it into sentences.
2. If the LLM call requires an API key, add it as a new env var (documented in `server/.env.example`).
3. Verify: `bun run verify:backend` + `cd server && pytest tests -v` (filter tests still apply).

> After this change the recipe is no longer zero-key.

## Add or change a browser-facing route

1. Add the FastAPI handler in `server/src/server.py` (return the `{ code, msg, data }` envelope).
2. Add the `/api/<name>` → `/<name>` mapping in `web/next.config.ts` `rewrites()`.
3. Add a client helper in `web/src/services/api.ts`.
4. Extend `web/scripts/verify-api-contracts.ts` with the new path + envelope assertions.
5. Verify: `bun run verify:web` (and `bun run verify:local:fastapi` if it should go through the real backend).

## Change the agent prompt / greeting / vendors

1. Greeting: set `AGENT_GREETING` (env) or edit the default in `server/src/agent.py`.
2. Banned terms: set `FILTER_BANNED_TERMS=term1,term2` in `server/.env.local`.
3. STT/TTS vendors: edit `DeepgramSTT` / `MiniMaxTTS` constructor in `Agent.start()`.
4. `CustomLLM` params (model, temperature, max_tokens, etc.): edit in `Agent.start()`.
5. Verify: `bun run verify:backend` + `cd server && pytest tests -v`.

## Adjust session parameters (codec, scenario)

1. Edit the `parameters` dict in `Agent.start()` (`audio_scenario`, `data_channel`, `enable_metrics`, etc.).
   `output_audio_codec` is also accepted per-request via `parameters` on `POST /startAgent`.
2. Verify: `bun run verify:local:fastapi`.

## Run / debug locally

```bash
bun run dev              # both processes (requires a running ngrok tunnel and CUSTOM_LLM_URL set)
bun run doctor:local     # check creds + .env.local + CUSTOM_LLM_URL before a live call
```

## Verify before finishing

| Change touches…                        | Run                                                                  |
| -------------------------------------- | -------------------------------------------------------------------- |
| Web only                               | `bun run verify:web`                                                 |
| Filter logic / `llm.py`                | `bun run verify:backend` + `cd server && pytest tests -v` + `bun run verify:local:llm` |
| Backend agent / vendor config          | `bun run verify:backend` + `cd server && pytest tests -v`            |
| Route/proxy boundary                   | `bun run verify:web:proxy` and/or `bun run verify:local:fastapi`     |
| Anything end-to-end (local)            | `bun run verify:local`                                               |

## Deploy

1. Deploy `web/` as a Next.js app.
2. Deploy `server/` as a **publicly reachable** FastAPI service (it serves `/llm` for Agora cloud).
   The published image is `ghcr.io/AgoraIO-Conversational-AI/recipe-agent-content-filter` on `v*` tags.
3. Set `AGENT_BACKEND_URL` in the web deployment so rewrites reach the backend.
4. Set `CUSTOM_LLM_URL` to `<public-backend-url>/llm/chat/completions` (no tunnel needed when deployed).

## Related Deep Dives

- [filter_seam](L2/filter_seam.md) — SSE contract detail, full seam internals, and production swap patterns.
- [session_lifecycle](L2/session_lifecycle.md) — client-side join/renewal/teardown.
