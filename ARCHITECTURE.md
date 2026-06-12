# Architecture — Content Filter Recipe

Two processes. The browser talks only to Next.js `/api/*`, which rewrites to the
agent backend. The agent backend owns Agora tokens and agent lifecycle, and also
serves the content-filter LLM endpoint mounted at `/llm`, which **Agora cloud**
calls directly.

## Request flow

```
Browser
  │  GET /api/get_config            → token + channel/UIDs
  │  POST /api/startAgent           → start agent session
  ▼
Next.js  (rewrites /api/* → AGENT_BACKEND_URL)
  ▼
Agent backend (server/, :8000)
  │  builds session with CustomLLM(base_url=CUSTOM_LLM_URL)
  ▼
Agora ConvoAI Cloud
  │  user speech → Deepgram STT (managed, nova-3)
  │  POST <CUSTOM_LLM_URL>/chat/completions   (Authorization: Bearer <key>)
  ▼
Content-filter LLM endpoint (mounted at /llm in server/, :8000, public via tunnel)
  │  echo_reply()  — mock generation (echoes user text)
  │  filter_reply() — splits reply at sentence boundaries
  │  moderate()    — flags sentences containing banned terms
  │  flagged sentences → "Content filtered."
  │  returns OpenAI SSE
  ▼
Agora ConvoAI Cloud → MiniMax TTS (managed) → user hears speech
                     → RTM transcript / metrics → web UI
```

`POST /api/stopAgent { agentId }` ends the session.

## One process, two concerns

`server/` runs a single process that serves both the token/agent endpoints and,
mounted at `/llm`, the OpenAI-compatible content-filter LLM endpoint
(`server/src/llm.py`).

The two concerns are kept in separate files with a one-directional dependency
(`server.py` imports `llm`, never the reverse), and `llm.py` has no `agora_agent`
import — it is the provider-agnostic part you replace with your own model and
filter.

Merging them onto one public surface is a deliberate trade. The Agora App
Certificate is only ever used in-memory to mint tokens — it never crosses a wire —
so co-locating the public `/llm` route with the token endpoints does not expose
the certificate. It does, however, make the token-minting endpoints
(`/get_config`, `/startAgent`, `/stopAgent`) publicly reachable. They are
unauthenticated in this recipe; put auth / rate-limiting in front of them
(ingress, gateway, or a proxy) before any real deployment.

## Filter seam

The filter is implemented in `server/src/llm.py`:

| Symbol | Role |
| --- | --- |
| `run_agent_turn(messages)` | Top-level call: generate then filter |
| `echo_reply(user_text)` | Mock generation — echoes the user in one sentence |
| `filter_reply(text)` | Splits on sentence boundaries; calls `moderate()` per sentence |
| `moderate(sentence)` | Returns `True` (allow) or `False` (redact); replace this body for the "LLM-powered" variant |
| `FILTER_BANNED_TERMS` | Env var (`FILTER_BANNED_TERMS`, default `strawberries`), comma-separated |
| `REDACTION` | The replacement string: `"Content filtered."` |

No tools are called, no data is stored — this is output redaction only.

## API (agent backend, port 8000)

| Endpoint | Method | Description |
| --- | --- | --- |
| `/get_config` | GET | Token + channel/UID config |
| `/startAgent` | POST | Start the agent session |
| `/stopAgent` | POST | Stop the agent by `agent_id` |
| `/llm/chat/completions` | POST | OpenAI-compatible completions (filter applied) |
| `/llm/health` | GET | LLM endpoint health check |

The browser calls the first three as `/api/*`; Next rewrites them to
`AGENT_BACKEND_URL`. Agora cloud calls `/llm/chat/completions` directly.

## Auth

- Browser → agent backend: none (local dev).
- Agent backend → Agora cloud: Token007, generated from `AGORA_APP_ID` +
  `AGORA_APP_CERTIFICATE`.
- Agora cloud → content-filter LLM endpoint: `Authorization: Bearer <CUSTOM_LLM_API_KEY>`.
  The mock endpoint does not validate it; a production endpoint should.
