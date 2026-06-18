# Agent Development Guide

For coding agents working in `recipe-agent-content-filter`. This repository is the
**content-filter** recipe (`Recipe Role: content-filter`) in the Agora
Conversational AI recipes family, derived from the `agent-quickstart-python`
template and the `custom-llm` reference recipe.

## System shape

- **`server/`** — Python FastAPI agent backend (:8000). Owns Agora token
  generation and agent session lifecycle. Uses the `CustomLLM` vendor to point the
  agent's LLM stage at the content-filter endpoint. SDK: `agora-agents>=2.3.0`
  (`import agora_agent`).
- **`server/src/llm.py`** — provider-agnostic FastAPI content-filter LLM endpoint,
  mounted into the API server at `/llm` (so Agora cloud calls
  `<public>/llm/chat/completions`). OpenAI-compatible `POST /chat/completions`
  mock that echoes the user and applies a sentence-level keyword filter before
  returning. No `agora-agents` dependency. This is the component a developer
  extends or replaces.
- **`web/`** — Next.js 16 / React 19 / TypeScript frontend (:3000).
- Auth: Token007 from `AGORA_APP_ID` + `AGORA_APP_CERTIFICATE`.

## Filter seam (`server/src/llm.py`)

| Symbol | Role |
| --- | --- |
| `run_agent_turn(messages)` | Top-level: generate + filter |
| `echo_reply(user_text)` | Mock generation |
| `filter_reply(text)` | Sentence-level redaction driver |
| `moderate(sentence)` | **The pluggable seam** — swap body for real moderator |
| `FILTER_BANNED_TERMS` | `os.getenv("FILTER_BANNED_TERMS", "strawberries")`, comma-separated |
| `REDACTION` | `"Content filtered."` |

No tools, no storage — output redaction only.

## Routing / ownership

- UI and RTC/RTM lifecycle live in `web/`.
- Browser-facing `/api/*` paths are Next rewrites (`web/next.config.ts`) to the
  agent backend; do not add `web/app/api/**/route.ts` for agent/token logic.
- Token generation and agent lifecycle live in `server/src/`.
- The OpenAI `/chat/completions` contract and the filter live in `server/src/llm.py`.

## Supported modes

- **Local:** `bun run dev` starts `server` (:8000, serving `/llm`) and `web`
  (:3000). The web app calls `/api/*`; Next rewrites to
  `AGENT_BACKEND_URL=http://localhost:8000`. The backend must be exposed publicly
  (`ngrok http 8000`) so Agora cloud can reach `/llm/chat/completions`.
- **Deploy:** deploy `web` (Next) + `server` (a single publicly reachable FastAPI
  process that also serves `/llm`, so Agora cloud can reach
  `/llm/chat/completions`). Set `AGENT_BACKEND_URL` in the web deployment.

## Patterns

- Keep the web client calling `/api/*`; hide backend placement behind Next rewrites.
- Keep token generation and the App Certificate in `server/`.
- Keep `server/src/llm.py` free of `agora-agents` — it is provider-agnostic.
- `CUSTOM_LLM_URL` is required and must be public; there is no localhost default.
- Both `CUSTOM_LLM_URL` and `CUSTOM_LLM_API_KEY` are required by the `CustomLLM`
  vendor (the SDK rejects one without the other).
- `FILTER_BANNED_TERMS` is optional (default `strawberries`), set in
  `server/.env.local`.

## Anti-patterns

- Do not reintroduce Next Route Handlers for agent/token logic.
- Do not add `agora-agents` to `server/src/llm.py`.
- Do not default `CUSTOM_LLM_URL` to localhost.
- Do not put `PORT` in `server/.env.example` (it would clobber the random port
  that `verify:local:fastapi` injects via `load_dotenv(override=True)`).
- Do not reference `get_mock_response` — it has been removed and replaced by
  `run_agent_turn` / `echo_reply` / `filter_reply` / `moderate`.
- Do not reference port 8001 — the mock LLM endpoint is now mounted in-process
  at `/llm` on port 8000.

## Commands

```bash
bun run setup
bun run dev
bun run doctor
bun run doctor:local
bun run verify         # web-only, no creds
bun run verify:local   # full local gate
```

Narrower checks: `bun run verify:backend`, `bun run verify:local:fastapi`,
`bun run verify:local:llm`, `bun run verify:web:proxy`.

## Done criteria

1. Run the narrowest relevant verification command.
2. Web-affecting changes: `bun run verify:web` passes.
3. Backend-affecting changes: `bun run verify:local` (or the narrower
   `verify:local:fastapi` / `verify:local:llm` / `verify:backend`) passes.
4. If you change required env vars or setup steps, update the root README, the
   relevant module README, and `server/.env.example` together.

## Git conventions

- Conventional Commits: `type: description` or `type(scope): description`
  (`feat`, `fix`, `chore`, `test`, `docs`). Lowercase after the prefix, present
  tense.
- No AI tool names in commit messages or PR descriptions. No `Co-Authored-By`
  trailers. No `--no-verify`. No git config changes.
- Branch names: `type/short-description` (e.g. `feat/content-filter-tools`).
