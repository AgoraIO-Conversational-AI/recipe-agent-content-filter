# Agora Conversational AI — Content Filter Recipe (Python)

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](./LICENSE)
[![python>=3.10](https://img.shields.io/badge/python-%3E%3D3.10-blue)](https://www.python.org/)
[![bun](https://img.shields.io/badge/bun-%E2%89%A51.0-black)](https://bun.sh/)

The **content-filter** recipe in the Agora Conversational AI recipes family. The
agent's LLM stage is pointed at a local mock endpoint that echoes the user's words
and then runs a **sentence-level keyword filter** before the text is handed to TTS.
Flagged sentences are replaced with "Content filtered." — so you can hear the
redaction by voice just by saying a banned term. STT (Deepgram nova-3) and TTS
(MiniMax) stay Agora-managed.

**Zero-key:** no LLM API key, no external model account.

## Prerequisites

- [Python 3.10+](https://www.python.org/)
- [Bun](https://bun.sh/)
- [Agora CLI](https://github.com/AgoraIO/cli) (easiest way to get App ID + Certificate)
- [ngrok](https://ngrok.com/) (or any tunnel to expose localhost) — required for the
  bundled mock LLM endpoint that Agora cloud must reach

## Run It

```bash
# 1. Install + create both Python venvs
bun run setup

# 2. Add Agora credentials (CLI), or edit server/.env.local by hand
agora login
agora project use <your-project>
agora project env write server/.env.local

# 3. Expose the content-filter LLM endpoint publicly (Agora cloud calls it directly)
ngrok http 8001

# 4. Add the tunnel URL to server/.env.local
#    CUSTOM_LLM_URL=https://<your-tunnel>.ngrok-free.dev/chat/completions

# 5. Run all three services
bun run dev
```

Open [http://localhost:3000](http://localhost:3000) → **Start Conversation** → speak.
Say "strawberries" (or any term in `FILTER_BANNED_TERMS`) to hear that sentence
redacted.

### Working from a clone

After `bun run setup` and credentials, `bun run dev` starts three services:

| Service | Port | Notes |
| --- | :---: | --- |
| Web (Next.js) | 3000 | Browser UI |
| Agent backend | 8000 | Token generation + agent lifecycle |
| Mock LLM endpoint | 8001 | Content-filter; must be publicly tunneled |
| API docs | 8000/docs | FastAPI auto-generated docs |

## Deploy

Deploy `web` (Next.js) and `server` (FastAPI) to any platform. Set
`AGENT_BACKEND_URL` in the web deployment to point at your deployed backend.

**Docker image** (multi-process, bundled): published to
`ghcr.io/AgoraIO-Conversational-AI/recipe-agent-content-filter` on `v*` tags.

The Docker image bundles both `server/` (:8000) and the mock LLM endpoint `llm/`
(:8001). For a live deployment you must expose `:8001` publicly and point
`CUSTOM_LLM_URL` at it — Agora cloud calls that endpoint directly. The local
`docker run` still needs a tunnel (ngrok) for the same reason. The bundled mock is
a development stand-in; replace `moderate()` with a real moderator for production.

```bash
docker run -d -p 8000:8000 -p 8001:8001 \
  -e AGORA_APP_ID=<your-app-id> \
  -e AGORA_APP_CERTIFICATE=<your-certificate> \
  -e CUSTOM_LLM_URL=https://<your-tunnel>.ngrok-free.dev/chat/completions \
  -e CUSTOM_LLM_API_KEY=any-key-here \
  ghcr.io/AgoraIO-Conversational-AI/recipe-agent-content-filter:latest
```

## Environment variables

Backend env file: [`server/.env.example`](server/.env.example).
LLM env file: [`llm/.env.example`](llm/.env.example).

| Variable | Required | Default | Notes |
| --- | :---: | :---: | --- |
| `AGORA_APP_ID` | ✅ | — | Agora Console → Project → App ID |
| `AGORA_APP_CERTIFICATE` | ✅ | — | Agora Console → Project → App Certificate (server only) |
| `CUSTOM_LLM_URL` | ✅ | — | **Public** chat-completions URL of your `llm/` endpoint. Agora cloud calls it; cannot be `localhost`. |
| `CUSTOM_LLM_API_KEY` | ✅ | `any-key-here` | Forwarded by Agora cloud as `Authorization: Bearer`. Required by the `CustomLLM` vendor. |
| `CUSTOM_LLM_MODEL` |  | `filter-mock` | Model name passed to your endpoint |
| `AGENT_GREETING` |  | built-in | Optional opening line override |
| `PORT` |  | `8000` | Agent backend port |
| `CUSTOM_LLM_PORT` |  | `8001` | Port for the content-filter LLM endpoint — lives in **`llm/.env.local`** |
| `FILTER_BANNED_TERMS` |  | `strawberries` | Comma-separated list of banned terms — lives in **`llm/.env.local`** |
| `AGENT_BACKEND_URL` (web deploy) | ✅ | — | Required in a deployed `web` app when proxying to the backend |

## Commands

```bash
bun run setup            # install web deps + create server/ and llm/ venvs
bun run dev              # run llm (:8001) + backend (:8000) + web (:3000)

bun run doctor           # prerequisite check (no creds needed)
bun run doctor:local     # + .env.local + credentials + CUSTOM_LLM_URL checks

bun run verify           # web-only gate (no Agora creds needed)
bun run verify:local     # full local gate: backend compile + smoke tests + web build
bun run clean            # remove venvs and build artifacts
```

Tests run standalone (no Agora cloud needed): `pytest` in `llm/`, plus
`bun run verify` in `web/`. CI runs them on Linux/macOS/Windows × Python 3.10 & 3.13.

## Architecture

```
Browser (localhost:3000)
  │  fetch /api/*
  ▼
Next.js  ──rewrite──▶  Agent backend  (server/, localhost:8000)
                          │  starts agent session (CustomLLM vendor)
                          ▼
                       Agora ConvoAI Cloud
                          │  POST <CUSTOM_LLM_URL>   (Authorization: Bearer)
                          ▼
                       Content-filter LLM endpoint  (llm/, localhost:8001)
                          ▲  public via ngrok tunnel
```

The browser only ever calls Next `/api/*`, which rewrites to the agent backend.
The agent backend owns Agora tokens and agent lifecycle. The **content-filter LLM
endpoint** is separate because Agora cloud — not the browser — calls it, so it
must be publicly reachable. See [ARCHITECTURE.md](./ARCHITECTURE.md).

## What You Get

- **Web client** — zero-config Next.js voice UI; token + session lifecycle handled
  behind Next rewrites.
- **Agent backend** (`server/`) — FastAPI service that generates Agora tokens and
  drives the agent session via the `CustomLLM` vendor.
- **API contract** — the `CustomLLM` vendor expects a public OpenAI-compatible
  `POST /chat/completions` endpoint; the mock fulfils that contract.
- **Output redaction** behind a pluggable `moderate()` seam inside `llm/` with
  `FILTER_BANNED_TERMS` — swap the body for a real moderation model with no other
  changes required.
- **Zero-key mock** — no LLM API key or external model account needed to run the
  demo.

## How It Works

1. The browser opens the Agora RTC channel via the Next.js web client.
2. The agent backend (`:8000`) generates an Agora token and starts an agent session
   pointing the `CustomLLM` vendor at `CUSTOM_LLM_URL`.
3. Agora cloud transcribes speech (Deepgram STT) and sends the transcript to the
   content-filter LLM endpoint via `POST /chat/completions`.
4. `echo_reply()` builds a reply that includes a sentence repeating what the user
   said (the sentence that may get flagged).
5. `filter_reply()` splits the reply at sentence boundaries (`.`, `!`, `?`) and
   passes each sentence to `moderate()`.
6. `moderate()` checks whether any term from `FILTER_BANNED_TERMS` (default:
   `strawberries`) appears in the sentence. Returning `False` replaces the sentence
   with `"Content filtered."`.
7. The filtered text streams back to Agora cloud via OpenAI SSE and is spoken by
   MiniMax TTS.

The content _generation_ is mocked; the filter is real code. Swap `moderate()`'s
body for a real moderator model (e.g. call an LLM) to get the "LLM-powered"
variant with no other changes.

### Replacing the mock

The filter + seam live in `run_agent_turn()` / `moderate()` / `filter_reply()` in
[`llm/src/custom_llm_server.py`](llm/src/custom_llm_server.py).

- Replace `moderate()`'s body with a real moderator model (e.g. an LLM
  classification call) to get the "LLM-powered" variant.
- Replace `echo_reply()` with a real LLM call to get a fully real response pipeline
  that still runs the filter.

The endpoint must keep speaking the OpenAI streaming `/chat/completions` contract
(see [`llm/README.md`](llm/README.md)). A production endpoint should also validate
the `Authorization: Bearer` header.

## Repo Map

```
recipe-agent-content-filter/
├── web/          # Next.js frontend (:3000)
├── server/       # Agent backend (:8000) — tokens + agent lifecycle, CustomLLM vendor
├── llm/          # Mock /chat/completions (:8001); Agora cloud calls this endpoint
├── ARCHITECTURE.md
└── AGENTS.md
```

## Troubleshooting

| Problem | Fix |
| --- | --- |
| Agent starts but never speaks | `CUSTOM_LLM_URL` is not public or omits `/chat/completions`. Use your ngrok URL. |
| `doctor:local` warns about localhost | Replace the local URL with your public tunnel URL. |
| Local calls fail / hang under a global proxy | Configure your proxy to route `127.0.0.1`, `localhost`, and RFC-1918 ranges DIRECT. |
| `Missing llm/venv` during verify | Run `bun run setup` (creates both venvs). |
| Want different banned terms | Set `FILTER_BANNED_TERMS=term1,term2` in `llm/.env.local`. |

## More Docs

- [ARCHITECTURE.md](./ARCHITECTURE.md)
- [AGENTS.md](./AGENTS.md)

## License

Released under the [MIT License](./LICENSE).
