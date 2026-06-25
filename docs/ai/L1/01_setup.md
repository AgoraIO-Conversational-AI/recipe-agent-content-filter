# 01 · Setup

> Install dependencies, configure env, expose the backend publicly, and run the content-filter recipe locally. This recipe is **zero-key**: no LLM API key or external model account is needed for the mock. A public tunnel is required so Agora cloud can reach the `/llm` endpoint.

## Prerequisites

- Python 3.10+ (backend runs on 3.10 and 3.13 in CI)
- [Bun](https://bun.sh/) (runs the web app and orchestration scripts)
- [Agora CLI](https://github.com/AgoraIO/cli) (optional; easiest way to mint App ID + Certificate)
- [ngrok](https://ngrok.com/) (or any public tunnel) — **required**: Agora cloud calls `/llm/chat/completions` directly; it cannot reach `localhost`

## Install

```bash
bun run setup            # installs web deps + creates server/ venv from requirements.txt
```

`setup` runs `setup:env` (copies `server/.env.example` → `server/.env.local` if missing), `setup:server` (recreates `server/venv`, installs `requirements.txt`), and `setup:web` (`bun install`).

## Configure env

Backend env file is `server/.env.local` (template: `server/.env.example`).

| Variable                | Required | Default                    | Notes                                                                          |
| ----------------------- | :------: | -------------------------- | ------------------------------------------------------------------------------ |
| `AGORA_APP_ID`          |    ✅    | —                          | Agora Console → Project → App ID                                               |
| `AGORA_APP_CERTIFICATE` |    ✅    | —                          | Agora Console → Project → App Certificate                                      |
| `CUSTOM_LLM_URL`        |    ✅    | —                          | **Public** URL of the `/llm` endpoint, e.g. `https://<tunnel>/llm/chat/completions`. Agora cloud calls it; cannot be `localhost`. |
| `CUSTOM_LLM_API_KEY`    |    ✅    | `any-key-here`             | Forwarded by Agora cloud as `Authorization: Bearer`. Required by `CustomLLM` vendor. |
| `CUSTOM_LLM_MODEL`      |          | `filter-mock`              | Model name passed to the `/llm` endpoint                                       |
| `AGENT_GREETING`        |          | built-in line              | Optional opening utterance override                                            |
| `FILTER_BANNED_TERMS`   |          | `strawberries`             | Comma-separated banned terms; matched case-insensitively per sentence          |

Fill Agora credentials via the CLI or by hand:

```bash
agora login
agora project use <your-project>
agora project env write server/.env.local   # writes App ID + Certificate
# then add CUSTOM_LLM_URL and CUSTOM_LLM_API_KEY to server/.env.local
```

> Do **not** add `PORT` to `server/.env.example` — see [07_gotchas](07_gotchas.md).

## Expose the backend

Agora cloud calls `/llm/chat/completions` on your backend directly. Expose port 8000 before starting:

```bash
ngrok http 8000
# then set CUSTOM_LLM_URL=https://<your-tunnel>.ngrok-free.dev/llm/chat/completions
```

## Run

```bash
bun run dev              # backend (:8000, serves /llm) + web (:3000) via concurrently
```

Open <http://localhost:3000> → **Start Conversation** → speak. Say `strawberries` (or any term in `FILTER_BANNED_TERMS`) to hear that sentence replaced with "Content filtered." Backend API docs at <http://localhost:8000/docs>.

## Quick commands

```bash
bun run doctor           # shared prereqs (bun + node_modules); no creds needed
bun run doctor:local     # + .env.local + AGORA creds + CUSTOM_LLM_URL present; warns on localhost URL
bun run verify           # web-only gate (doctor + api contracts + web build)
bun run verify:local     # full local gate: backend compile + fastapi smoke + llm smoke + proxy + web build
bun run clean            # remove venvs and build artifacts
```

Backend unit tests run standalone (no cloud, no creds):

```bash
cd server && pytest tests -v
```

## Related Deep Dives

- None. For what each verify command asserts, see [05_workflows](05_workflows.md) and [06_interfaces](06_interfaces.md).
