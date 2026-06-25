# Progressive Disclosure — Test Results

> Test run for `recipe-agent-content-filter` progressive disclosure docs.
> Date: 2026-06-25 · Standard: AgoraIO-Community/ai-devkit progressive-disclosure.

## Step 1 — Structural checks

| Check                                                  | Result |
| ------------------------------------------------------ | ------ |
| `L0_repo_card.md` ≤ 50 lines                           | Pass (36) |
| All 8 L1 files present                                 | Pass |
| Each L1 has purpose blockquote + Related Deep Dives    | Pass |
| L1 line counts in 80–200 target                        | **Below target** (48–85) — see note |
| L2 `_index.md` present                                 | Pass |
| Each L2 opens with "When to Read This" callout         | Pass (2/2) |
| Relative links resolve (`docs/ai/` + AGENTS.md)        | Pass (44/44, 0 broken) |
| AGENTS.md has How to Load / Git Conventions / Doc Commands | Pass |
| AGENTS.md `Recipe Role` corrected to `base`            | Pass (was `content-filter`, corrected) |

**Note on L1 line counts:** files are table-dense and information-complete but run 48–85 lines, at or below the 80–200 soft target. The standard favors tables over prose; files were kept concise rather than padded. Accepted deviation; revisit if a section needs more depth.

## Step 2 — pytest execution

Backend tests run in throwaway venv `/tmp/v_content_filter` (Python 3.14.4, pytest 9.1.1). Venv removed after run.

```
11 passed, 1 warning in 1.96s
```

| Test file                     | Tests | Result |
| ----------------------------- | :---: | ------ |
| `test_agent_construction.py`  | 1     | Pass   |
| `test_filter.py`              | 4     | Pass   |
| `test_llm.py`                 | 3     | Pass   |
| `test_llm_mount.py`           | 3     | Pass   |
| **Total**                     | **11**| **Pass** |

Warning: `starlette.testclient` deprecation (`httpx` → `httpx2`) — not a test failure; upstream library concern.

## Step 3 — Question runs

Questions span the five standard categories. Each answer was checked against the repo source before being marked Pass. "Level" is the lowest disclosure level that fully answers the question.

### Setup & Build

| # | Question | Expected answer | Source of truth | Level | Status |
|---|----------|-----------------|-----------------|-------|--------|
| 1 | How do I install and run it locally? | `bun run setup`, expose port 8000 via ngrok, set `CUSTOM_LLM_URL`, then `bun run dev`. | `L1/01_setup.md` ↔ `README.md`, `package.json` | L1 | Pass |
| 2 | Which env vars are required? | `AGORA_APP_ID`, `AGORA_APP_CERTIFICATE`, `CUSTOM_LLM_URL`, `CUSTOM_LLM_API_KEY`. | `L1/01_setup.md`, `06_interfaces.md` ↔ `agent.py`, `.env.example` | L1 | Pass |
| 3 | Is this zero-key? | Yes — no LLM API key needed for the mock; `CUSTOM_LLM_API_KEY` defaults to `any-key-here`. | `L1/01_setup.md`, `README.md` ↔ `agent.py`, `llm.py` | L1 | Pass |

### Test & Run

| # | Question | Expected answer | Source of truth | Level | Status |
|---|----------|-----------------|-----------------|-------|--------|
| 4 | How do I run backend tests without cloud creds? | `cd server && pytest tests -v`; `conftest.py` fakes env + SDK session. | `L1/04_conventions.md`, `01_setup.md` ↔ `tests/conftest.py` | L1 | Pass (ran: 11 passed) |
| 5 | What's the narrowest gate for a web-only change? | `bun run verify:web`. | `L1/05_workflows.md` ↔ `package.json` | L1 | Pass |
| 6 | What does `verify:local:llm` do? | Spawns `llm.py` standalone; asserts SSE contract end-to-end (health, streaming, non-streaming 400). | `L1/03_code_map.md` ↔ `web/scripts/verify-local-llm.ts` | L1 | Pass |

### Conventions

| # | Question | Expected answer | Source of truth | Level | Status |
|---|----------|-----------------|-----------------|-------|--------|
| 7 | What response shape do backend routes use? | `{ code, msg, data }`; `data` only when there's a payload. `/llm/*` routes use OpenAI SSE. | `L1/04_conventions.md`, `06_interfaces.md` ↔ `server.py` | L1 | Pass |
| 8 | How are errors mapped to HTTP codes? | `ValueError→400`, `RuntimeError→500`, else 500 via `_to_http_error`. | `L1/04_conventions.md` ↔ `server.py` | L1 | Pass |
| 9 | What are the commit/branch conventions? | Conventional commits `type: description`; branches `type/short-description`; no AI tool names; no Co-Authored-By. | `AGENTS.md` Git Conventions | L1 | Pass |

### Development

| # | Question | Expected answer | Source of truth | Level | Status |
|---|----------|-----------------|-----------------|-------|--------|
| 10 | How do I add a new browser-facing route? | Add FastAPI handler → add rewrite in `next.config.ts` → add client helper → extend `verify-api-contracts.ts`. | `L1/05_workflows.md` ↔ source | L1 | Pass |
| 11 | Where is the `/api/*` boundary and what must I not add? | Rewrites in `web/next.config.ts`; never add `app/api/**/route.ts` for agent/token logic. | `L1/04_conventions.md`, `07_gotchas.md` ↔ `next.config.ts`, `verify-api-contracts.ts` | L1 | Pass |
| 12 | Why can't `CUSTOM_LLM_URL` be localhost? | Agora cloud calls it directly; localhost is unreachable from the cloud. No localhost default is intentional. | `L1/07_gotchas.md` ↔ `agent.py`, `README.md` | L1 | Pass |

### Deep Dive

| # | Question | Expected answer | Source of truth | Level | Status |
|---|----------|-----------------|-----------------|-------|--------|
| 13 | How do I replace the keyword filter with a real LLM moderator? | Replace only `moderate(sentence: str) -> bool` in `llm.py`; keep `filter_reply` and `run_agent_turn` intact. | `L2/filter_seam.md` ↔ `llm.py`, `test_filter.py` | L2 | Pass |
| 14 | What is the exact OpenAI SSE chunk structure the endpoint must return? | Role chunk → content chunks → finish_reason="stop" chunk → `data: [DONE]`. | `L2/filter_seam.md` ↔ `llm.py`, `test_llm.py` | L2 | Pass |
| 15 | How does stop survive a backend restart? | `_sessions` is in-memory; missing session falls back to `client.stop_agent(agent_id)`. | `L2/session_lifecycle.md` ↔ `agent.py` | L2 | Pass |

## Step 4 — Analysis

- All 15 questions answered at the expected disclosure level (12 at L1, 3 at L2).
- No missing-coverage findings; no broken references.
- AGENTS.md `Recipe Role` was `content-filter`; corrected to `base` per standard.
- One soft deviation: L1 line counts at/below the 80–200 soft target (accepted; concise/table-dense).

## Step 5 — Summary

| Category       | Questions | Pass | Notes |
| -------------- | :-------: | :--: | ----- |
| Setup & Build  | 3 | 3 | — |
| Test & Run     | 3 | 3 | pytest: 11 passed |
| Conventions    | 3 | 3 | — |
| Development    | 3 | 3 | — |
| Deep Dive      | 3 | 3 | resolved at L2 as designed |
| **Total**      | **15** | **15** | — |

## Step 6 — Fixes / Retest

- Fixed: `AGENTS.md` `Recipe Role` corrected from `content-filter` to `base`.
- No failing questions; no further fixes required.

Evidence executed during this run:
- `pytest tests -v` (throwaway venv `/tmp/v_content_filter`, Python 3.14.4) → `11 passed`.
- Relative link check → `44 checked, 0 broken`.
