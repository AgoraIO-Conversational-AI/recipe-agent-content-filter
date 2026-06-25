# 07 · Gotchas

> Non-obvious pitfalls specific to the content-filter recipe. Read before changing the agent, env, filter, or verify scripts.

## `CUSTOM_LLM_URL` must be a public URL

`CUSTOM_LLM_URL` is the URL Agora cloud calls — **not** the browser or the backend. It cannot be `localhost` or a private IP. For local dev, expose port 8000 with ngrok:

```bash
ngrok http 8000
# then: CUSTOM_LLM_URL=https://<tunnel>/llm/chat/completions
```

`doctor:local` warns if the URL contains `localhost` or `127.0.0.1`. A localhost URL lets the agent "start" while its LLM calls silently fail.

## `CUSTOM_LLM_API_KEY` is required

The `CustomLLM` SDK vendor rejects a missing `api_key`. Even though the mock endpoint does not validate the bearer token, `CUSTOM_LLM_API_KEY` must be set (default `any-key-here`). Omitting it raises a `ValueError` at `Agent.__init__`.

## Do not put `PORT` in `server/.env.example`

`verify:local:fastapi` injects a random `PORT` via environment; `server.py` loads `.env.local` with `load_dotenv(override=True)`. A `PORT` line in `.env.example` (copied to `.env.local`) would clobber the injected port and break the smoke test.

## Turn detection lives on `AgoraAgent`, not on the vendor

Unlike the realtime recipe (where `turn_detection` belongs on the MLLM vendor), this recipe uses the cascading STT→LLM→TTS chain. `turn_detection` is set directly on `AgoraAgent(...)` with `mode: "vad"` for start-of-speech and end-of-speech. Do not move it to a vendor.

## `llm.py` must not import `agora_agent`

`test_llm_mount.py` inspects `llm.py` via AST and asserts no Agora SDK import is present. This is the provider-agnostic seam — it must remain replaceable without touching `agora_agent`.

## Do not reference `get_mock_response`

The legacy `get_mock_response` symbol has been removed. The current pipeline is `run_agent_turn` → `echo_reply` / `filter_reply` / `moderate`. Any reference to the old name will fail at import.

## Do not reference port 8001 for the LLM endpoint

The filter LLM endpoint is mounted **in-process** at `/llm` on port 8000 — not on a separate port 8001. References to port 8001 in scripts or docs are stale.

## Keep `/api/*` ownership in rewrites

Adding `web/app/api/**/route.ts` for agent/token logic breaks the boundary — `verify-api-contracts.ts` explicitly fails if a `route.ts` exists under `app/api`. Token logic belongs in `server/`.

## camelCase request fields

`StartAgentRequest` uses `channelName`, `rtcUid`, `userUid` (camelCase) to match the browser client. Renaming one side without the other breaks the contract tests.

## Token endpoints become co-public

When the backend is deployed publicly so Agora cloud can reach `/llm`, the `/get_config`, `/startAgent`, and `/stopAgent` routes are also public and unauthenticated. Add auth/rate-limiting before a real deployment. See [08_security](08_security.md).

## Local calls under a global proxy

Global proxies (Clash, etc.) can break `localhost`/RFC-1918 traffic. Configure the proxy to send `127.0.0.1`, `localhost`, and private ranges DIRECT, or use `all_proxy` with `socksio` (already in `requirements.txt`).

## Related Deep Dives

- [filter_seam](L2/filter_seam.md) — complete filter seam and SSE contract detail.
