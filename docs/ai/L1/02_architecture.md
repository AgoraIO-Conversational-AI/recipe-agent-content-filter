# 02 · Architecture

> One process, two concerns. The browser talks only to Next.js `/api/*`, which rewrites to the FastAPI agent backend. The agent backend also serves the OpenAI-compatible content-filter LLM endpoint at `/llm` — the same process Agora cloud calls directly.

## Topology

```
Browser (localhost:3000)
  │  fetch /api/*
  ▼
Next.js (web/)  ──rewrite──▶  Agent backend (server/, :8000)
                                 │  builds CustomLLM vendor pointing at CUSTOM_LLM_URL
                                 ▼
                              Agora ConvoAI Cloud
                                 │  user speech → Deepgram STT (managed, nova-3)
                                 │  POST <CUSTOM_LLM_URL>   (Authorization: Bearer)
                                 ▼
                              Content-filter LLM endpoint  (/llm in server/, :8000)
                                 │  echo_reply()  — mock generation
                                 │  filter_reply() — sentence-level redaction
                                 │  moderate()    — pluggable allow/deny seam
                                 │  returns OpenAI SSE
                                 ▼
                              Agora ConvoAI Cloud → MiniMax TTS (managed) → user hears speech
                                                  → RTM transcript / metrics → web UI
```

- **`web/`** — Next.js 16 / React 19 / TypeScript. Owns UI plus the RTC/RTM client lifecycle. Calls only `/api/*`.
- **`server/`** — Python FastAPI (:8000). Owns Agora token generation and agent session lifecycle. SDK: `agora-agents>=2.3.0` (`import agora_agent`). Also mounts `/llm` (the filter endpoint) in the same process.
- **`server/src/llm.py`** — Provider-agnostic FastAPI sub-app. No `agora_agent` import. This is the component a developer extends or replaces.

## Request lifecycle

1. Browser `GET /api/get_config` → Next rewrites to backend `/get_config`; backend mints a Token007 and returns channel + UIDs.
2. Browser joins the RTC channel, then `POST /api/startAgent`; backend builds the `CustomLLM` vendor and starts an async agent session.
3. Agora routes user audio to Deepgram STT, then `POST <CUSTOM_LLM_URL>/chat/completions` (via the public tunnel).
4. The filter endpoint echoes the user text, runs the keyword filter, and streams back OpenAI SSE.
5. Agora synthesizes filtered text via MiniMax TTS and delivers audio to the channel; RTM delivers transcript + metrics to the web UI.
6. `POST /api/stopAgent { agentId }` ends the session.

## One process, two concerns

`server/` runs a single process that serves both the token/agent endpoints **and**, mounted at `/llm`, the content-filter LLM endpoint. The two concerns are kept in separate files with a one-directional dependency (`server.py` imports `llm`, never the reverse). `llm.py` has no `agora_agent` import — it is the provider-agnostic part you replace.

This co-location means the token-minting endpoints (`/get_config`, `/startAgent`, `/stopAgent`) are also public. They are unauthenticated in this recipe; add auth/rate-limiting before a real deployment. See [08_security](08_security.md).

## Filter seam

| Symbol | Role |
| ------ | ---- |
| `run_agent_turn(messages)` | Top-level: generate then filter |
| `echo_reply(user_text)` | Mock generation — echoes the user in one sentence |
| `filter_reply(text)` | Splits on sentence boundaries (`.`, `!`, `?`); calls `moderate()` per sentence |
| `moderate(sentence)` | Returns `True` (allow) or `False` (redact); **the pluggable seam** |
| `FILTER_BANNED_TERMS` | `os.getenv("FILTER_BANNED_TERMS", "strawberries")`, comma-separated |
| `REDACTION` | `"Content filtered."` |

## Key abstractions

- **`Agent`** (`server/src/agent.py`) — async wrapper around `AgoraAgent`; owns the `AsyncAgora` client, env, and the in-memory `_sessions` map keyed by `agent_id`. Builds the vendor chain (`CustomLLM`, `DeepgramSTT`, `MiniMaxTTS`) at `start()`.
- **`CustomLLM`** (SDK vendor) — points the agent's LLM stage at `CUSTOM_LLM_URL`. Stamps `vendor: "custom"` in the wire config; requires both `base_url` and `api_key`.
- **Rewrite proxy** (`web/next.config.ts`) — the only browser→backend boundary; no Next Route Handlers exist for agent/token logic.

## Tech decisions

- **Rewrites, not Route Handlers** — hides backend placement behind `/api/*` so the same client works locally and deployed.
- **In-process `/llm` mount** — keeps the filter endpoint zero-dependency and avoids a second process/port for local dev. Trade-off: the token endpoints become co-public; see [08_security](08_security.md).
- **Zero-key mock** — no LLM API key; `CUSTOM_LLM_URL` is required but `CUSTOM_LLM_API_KEY` defaults to `any-key-here`.

## Related Deep Dives

- [filter_seam](L2/filter_seam.md) — complete filter implementation, swap patterns, and SSE contract.
- [session_lifecycle](L2/session_lifecycle.md) — browser orchestration of config + start/stop, RTC/RTM, transcript mapping.
