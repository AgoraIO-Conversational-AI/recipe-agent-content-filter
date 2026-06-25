---
recipe_version: 1.0.0
recipe_status: experimental
extension_points:
  - id: filter.moderate
    name: moderate() seam in server/src/llm.py — swap body for real moderation model
  - id: filter.generation
    name: echo_reply() seam in server/src/llm.py — replace with a real LLM call
  - id: api.routes
    name: Browser-facing API routes
  - id: agent.vendor-config
    name: CustomLLM model, greeting, turn_detection, STT/TTS vendors, session parameters
  - id: web.conversation-ui
    name: Conversation UI panels and controls
  - id: verification.contracts
    name: Contract, proxy, local FastAPI, and local LLM smoke verification
invariants:
  - id: api.rewrite-boundary
    summary: Browser calls stay on /api/* and Next rewrites to FastAPI; no Route Handlers for agent/token logic.
  - id: secrets.server-only
    summary: Agora App Certificate stays in the Python backend; CUSTOM_LLM_API_KEY is backend-only.
  - id: llm.no-agora-dependency
    summary: server/src/llm.py must not import agora_agent — it is the provider-agnostic filter seam.
  - id: llm.public-url
    summary: CUSTOM_LLM_URL must be a public URL; Agora cloud (not the backend) calls it. No localhost default.
  - id: llm.openai-sse-contract
    summary: The /llm/chat/completions endpoint must return OpenAI SSE (streaming only; data:[DONE] terminator).
  - id: token.uid-concrete
    summary: Backend resolves missing, zero, or negative UIDs before issuing an RTC+RTM token.
stable_contracts:
  - id: env.required
    summary: AGORA_APP_ID, AGORA_APP_CERTIFICATE, CUSTOM_LLM_URL, and CUSTOM_LLM_API_KEY are required; AGENT_BACKEND_URL is required by deployed web rewrites.
  - id: api.core-routes
    summary: GET /api/get_config, POST /api/startAgent, and POST /api/stopAgent remain the browser-facing contract.
  - id: llm.core-route
    summary: POST /llm/chat/completions (OpenAI SSE) and GET /llm/health remain the Agora-cloud-facing contract.
  - id: response.envelope
    summary: Successful backend responses use { code, msg, data }.
---

# Recipe Contract

This base recipe defines the reusable surface for a Python-backed Agora Conversational AI **content-filter** quickstart: a cascading STT→CustomLLM→TTS pipeline where the LLM stage is a mock that echoes user input and applies a sentence-level keyword filter before returning text to TTS.

## Recipe Role

- Role: `base` recipe (self-contained, clone-and-run; no `Extends` pin).
- Target audience: developers building a content-moderation layer for a voice agent with a Python FastAPI backend and Next.js web client.
- Reuse model: clone, bind project, expose backend publicly (ngrok), set `CUSTOM_LLM_URL`, run, then swap `moderate()` body for a real moderation model.

## Recipe Scope

- Python FastAPI token generation and managed agent session lifecycle.
- A `CustomLLM` vendor (SDK) pointing the agent's LLM stage at an OpenAI-compatible endpoint.
- A co-located `/llm` FastAPI sub-app (`server/src/llm.py`) implementing that endpoint with an echo mock + sentence-level keyword filter.
- Agora-managed STT (Deepgram nova-3) and TTS (MiniMax).
- Next.js browser UI with RTC audio, RTM transcript/metrics, connection status.
- Rewrite-only `/api/*` browser facade hiding backend placement.
- Contract, proxy, local FastAPI, and local LLM smoke verification that need no live Agora calls.

## Baseline Implementation Guidance

Use this repo's source and progressive disclosure docs as the starting point, then customize. Do not recreate the Agora ConvoAI integration from memory — vendor schemas, SDK builder fields, token behavior, and RTM details drift. Copy verified patterns from this repo.

## Extension Points

| ID | Surface | How to extend | Required follow-up |
| -- | ------- | ------------- | ------------------ |
| `filter.moderate` | `server/src/llm.py` `moderate()` | Replace the body with a real moderation call (e.g. an LLM classifier). Signature: `(sentence: str) -> bool`. | Run `bun run verify:backend` + `pytest tests`; keep all existing filter tests passing. |
| `filter.generation` | `server/src/llm.py` `echo_reply()` | Replace with a real LLM call to get real responses that still run the filter. | Preserve the OpenAI SSE contract in `run_agent_turn`; keep `test_llm.py` passing. |
| `api.routes` | `server/src/server.py`, `web/next.config.ts`, `web/src/services/api.ts` | Add FastAPI route, add rewrite, add browser fetch helper. | Extend `web/scripts/verify-api-contracts.ts`; add proxy/fastapi coverage if it belongs in local verification. |
| `agent.vendor-config` | `server/src/agent.py` | Change `CustomLLM` params, `turn_detection`, `greeting_message`, STT/TTS vendors, session parameters. | Run `bun run verify:backend` + `pytest tests`; document new env in `server/.env.example` (never add `PORT`). |
| `web.conversation-ui` | `web/src/components/*`, `web/src/lib/conversation.ts` | Customize pre-call, transcript, metrics, connection status, mic, or visualizer UI. | Preserve RTC/RTM lifecycle ownership and transcript UID normalization. |
| `verification.contracts` | `web/scripts/*.ts`, root `package.json` | Add checks for new browser/backend/LLM boundaries. | Keep checks runnable without live Agora credentials. |

## Invariants

- Browser code calls only `/api/get_config`, `/api/startAgent`, and `/api/stopAgent` for the default flow.
- Next.js owns `/api/*` through rewrites only; no `web/app/api/**/route.ts` for agent/token logic.
- FastAPI owns token generation, `AGORA_APP_CERTIFICATE`, and agent lifecycle.
- `server/src/llm.py` must not import `agora_agent` — it is the provider-agnostic filter seam.
- `CUSTOM_LLM_URL` must be public; Agora cloud (not the backend) calls it directly.
- The `/llm/chat/completions` endpoint streams OpenAI SSE only (non-streaming requests return 400).
- The backend issues one RTC+RTM-capable token for a concrete non-zero UID.

## Stable Contracts

| Contract | Stable shape |
| -------- | ------------ |
| Required backend env | `AGORA_APP_ID`, `AGORA_APP_CERTIFICATE`, `CUSTOM_LLM_URL`, `CUSTOM_LLM_API_KEY` |
| Optional backend env | `CUSTOM_LLM_MODEL`, `AGENT_GREETING`, `FILTER_BANNED_TERMS`, `PORT` (env only) |
| Required web deploy env | `AGENT_BACKEND_URL` |
| `GET /api/get_config` | Query `channel?`, `uid?`; returns `data.app_id`, `data.token`, `data.uid`, `data.channel_name`, `data.agent_uid`. |
| `POST /api/startAgent` | Body `{ channelName, rtcUid, userUid, parameters? }`; returns `data.agent_id`, `data.channel_name`, `data.status`. |
| `POST /api/stopAgent` | Body `{ agentId }`; returns `{ code: 0, msg: "success" }`. |
| `POST /llm/chat/completions` | Body OpenAI `ChatCompletionRequest` (`stream: true`); returns OpenAI SSE ending with `data: [DONE]`. |
| `GET /llm/health` | Returns `{ status: "ok", service: "content-filter-llm" }`. |
| Success envelope | `{ "code": 0, "msg": "success", "data": ... }` where the route has data. |
| Verification entry points | `bun run verify:web`, `bun run verify:backend`, `bun run verify:web:proxy`, `bun run verify:local:fastapi`, `bun run verify:local:llm`, `bun run verify:local`. |

## Internal / Subject to Change

- Visual layout, component composition, Tailwind classes, and assets under `web/src/components/`.
- Exact `FILTER_BANNED_TERMS` default, `REDACTION` string, and sentence-split regex — as long as they stay documented extension points.
- Mock generation logic in `echo_reply()` — the stable surface is the `run_agent_turn(messages)` top-level call and the OpenAI SSE contract.
- In-memory `Agent._sessions` details; the stable behavior is start by channel/user and stop by returned `agent_id`.
- Verification internals under `web/scripts/`; the stable surface is the root script names and what they assert.
- `agora-agents` SDK minor-version behavior; this recipe lower-bounds `>=2.3.0` but does not freeze every field.

## Related Progressive Disclosure Docs

- `L1/01_setup.md` — setup, env, tunnel, and commands.
- `L1/02_architecture.md` — request flow and filter seam topology.
- `L1/05_workflows.md` — common modification workflows.
- `L1/06_interfaces.md` — route, rewrite, env, CustomLLM, and OpenAI SSE contracts.
- `L1/L2/filter_seam.md` — full filter seam detail and swap patterns.
- `L1/L2/session_lifecycle.md` — RTC/RTM/session orchestration.
