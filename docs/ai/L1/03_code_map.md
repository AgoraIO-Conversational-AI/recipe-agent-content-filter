# 03 · Code Map

> Where things live. Two top-level modules: `web/` (Next.js client) and `server/` (FastAPI backend + filter endpoint). Orchestration is in the root `package.json`.

## Root

| Path                  | Responsibility                                                                        |
| --------------------- | ------------------------------------------------------------------------------------- |
| `package.json`        | Bun workspace; `setup`, `dev`, `doctor*`, `verify*`, `clean` scripts.                |
| `README.md`           | Setup, run modes (incl. tunnel), env, troubleshooting.                                |
| `ARCHITECTURE.md`     | System shape, filter seam, API table, auth.                                           |
| `AGENTS.md`           | Coding-agent handbook + How to Load / Git Conventions / Doc Commands.                 |
| `Dockerfile`          | Single-process image (`:8000`, serves both token/agent and `/llm`).                   |
| `.github/workflows/`  | `ci.yml` (backend pytest matrix + web verify), `docker.yml`, `nightly.yml`.          |

## `server/` — FastAPI backend (:8000)

| Path                              | Responsibility                                                                        |
| --------------------------------- | ------------------------------------------------------------------------------------- |
| `src/server.py`                   | FastAPI app, CORS, route handlers, mounts `/llm` sub-app, error mapping, uvicorn entry. |
| `src/agent.py`                    | `Agent` class: `AsyncAgora` client, vendor chain (`CustomLLM`/`DeepgramSTT`/`MiniMaxTTS`), `start()`/`stop()`, `_sessions`. |
| `src/llm.py`                      | Provider-agnostic filter endpoint: `run_agent_turn`, `echo_reply`, `filter_reply`, `moderate`; no agora deps. |
| `scripts/run_fake_server.py`      | Boots `server.app` with a `FakeAgent` for the local FastAPI smoke test.               |
| `tests/test_filter.py`            | Unit tests for `moderate`, `filter_reply`, `run_agent_turn` (no cloud, no creds).     |
| `tests/test_llm.py`               | Contract tests for `POST /chat/completions` and `GET /health` in isolation.           |
| `tests/test_llm_mount.py`         | Tests `/llm/*` routes through the mounted app; asserts `llm.py` has no Agora import. |
| `tests/test_agent_construction.py`| Builds the real `AgoraAgent`, fakes the SDK session, asserts shape.                   |
| `tests/conftest.py`               | `fake_env` fixture + `FakeAgent`; no cloud, no real creds.                            |
| `.env.example`                    | Env template (do not add `PORT`).                                                     |
| `requirements*.txt`               | Runtime + dev (pytest + httpx) deps.                                                  |

## `server/src/server.py` routes

- `GET /get_config` — token + channel/UID config.
- `POST /startAgent` — start the content-filter agent session.
- `POST /stopAgent` — stop by `agent_id`.
- `/llm` (mounted) — the entire `llm.py` FastAPI sub-app; Agora cloud calls `/llm/chat/completions`.

## `web/` — Next.js client (:3000)

| Path                                      | Responsibility                                                    |
| ----------------------------------------- | ----------------------------------------------------------------- |
| `next.config.ts`                          | `/api/*` rewrites to `AGENT_BACKEND_URL`; strict mode; Turbopack root. |
| `src/services/api.ts`                     | Browser API client: `getConfig`, `startAgent`, `stopAgent`.       |
| `src/lib/conversation.ts`                 | Transcript normalization, timestamp/UID mapping, visualizer state.|
| `src/lib/agora.ts`                        | Agora RTC/RTM helpers.                                            |
| `src/components/`                         | Conversation UI: landing page, RTC component, pre-call/transcript/metrics panels. |
| `scripts/verify-api-contracts.ts`         | Asserts rewrites + client paths + response envelope (no network). |
| `scripts/verify-local-proxy.ts`           | Stub backend; proxies `/api/*` through the rewrite map.           |
| `scripts/verify-local-fastapi.ts`         | Spawns real FastAPI with `FakeAgent`; proxies routes end-to-end.  |
| `scripts/verify-local-llm.ts`             | Spawns `llm.py` standalone; asserts SSE contract end-to-end.      |
| `scripts/doctor.ts`                       | Web prerequisite check.                                           |
| `.claude/skill-*.md`                      | Contributor reference notes for RTC/RTM/ConvoAI integration.      |

## Related Deep Dives

- None. For runtime flow see [02_architecture](02_architecture.md); for contracts see [06_interfaces](06_interfaces.md).
