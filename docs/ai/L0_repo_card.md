# recipe-agent-content-filter — Repo Card

> Next.js web client + Python FastAPI backend for an Agora Conversational AI agent that runs a sentence-level keyword filter on agent output before TTS. The LLM stage is a zero-key mock that echoes the user; the filter is real, pluggable code.

## Identity

| Field          | Value                                                                                   |
| -------------- | --------------------------------------------------------------------------------------- |
| Repo           | `AgoraIO-Conversational-AI/recipe-agent-content-filter`                                 |
| Type           | `distributed-system` (single repo, two co-located processes)                            |
| Language       | Python 3.10+ (FastAPI + uvicorn) backend + Next.js 16 / React 19 web                   |
| Deploy Target  | `web/` as Next.js app, `server/` as a publicly reachable FastAPI service (also serves `/llm`) |
| Owner          | Agora Conversational AI DevEx                                                           |
| Last Reviewed  | 2026-06-25                                                                              |
| Recipe Role    | `base`                                                                                  |
| Recipe Version | `1.0.0`                                                                                 |
| Recipe Status  | `experimental`                                                                          |

## L1 — Summaries

The Audience column helps agents prioritise: **Use** = consuming the recipe's behavior, **Maintain** = modifying internals.

| File                                     | Purpose                                                                                              | Audience       |
| ---------------------------------------- | ---------------------------------------------------------------------------------------------------- | -------------- |
| [01_setup](L1/01_setup.md)               | bun + venv + pip setup, env vars (incl. required `CUSTOM_LLM_URL` + tunnel), commands               | Use & Maintain |
| [02_architecture](L1/02_architecture.md) | Two-concern single-process topology, filter seam, request lifecycle                                  | Maintain       |
| [03_code_map](L1/03_code_map.md)         | `web/` and `server/` trees with key file responsibilities                                            | Maintain       |
| [04_conventions](L1/04_conventions.md)   | Python async + FastAPI patterns, Biome, JSON envelope, filter seam ownership                         | Maintain       |
| [05_workflows](L1/05_workflows.md)       | Add a route, change the filter, replace the mock, adjust session params, verify, deploy              | Use            |
| [06_interfaces](L1/06_interfaces.md)     | FastAPI route contracts, rewrites, env vars, `CustomLLM` config, OpenAI SSE contract                 | Use & Maintain |
| [07_gotchas](L1/07_gotchas.md)           | `CUSTOM_LLM_URL` must be public, no `PORT` in env example, STT/TTS vendor chain, VAD config         | Maintain       |
| [08_security](L1/08_security.md)         | Token007, App Certificate server-only, co-public `/llm` caveat, CORS, `CUSTOM_LLM_API_KEY` bearer  | Maintain       |

## Recipe Profile

This repo declares `Recipe Role: base`. See [RECIPE.md](RECIPE.md) for extension points, invariants, and stable contracts before changing reusable surfaces.
