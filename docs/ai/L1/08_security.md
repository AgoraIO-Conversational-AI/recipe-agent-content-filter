# 08 · Security

> Trust boundaries, secret handling, and auth for the content-filter recipe. This recipe's deployment shape is unusual: the filter LLM endpoint must be **publicly reachable**, which co-exposes the token endpoints.

## Trust boundaries

| Hop                                  | Auth                                                                          |
| ------------------------------------ | ----------------------------------------------------------------------------- |
| Browser → agent backend              | None in local dev (same-origin via Next rewrite).                             |
| Agent backend → Agora cloud          | Token007, generated from `AGORA_APP_ID` + `AGORA_APP_CERTIFICATE`.            |
| Agora cloud → content-filter LLM    | `Authorization: Bearer <CUSTOM_LLM_API_KEY>`; the mock does not validate it.  |

## Secret handling

- **`AGORA_APP_CERTIFICATE`** lives only in `server/.env.local` and never reaches the browser. The browser receives a short-lived token, never the certificate.
- **`CUSTOM_LLM_API_KEY`** lives only in `server/.env.local`. Agora cloud forwards it as a bearer token to your LLM endpoint; a production endpoint should validate it.
- `server/.env.local` is gitignored; `server/.env.example` ships placeholders only.
- Tokens (`generate_convo_ai_token`) expire after 3600s and are minted per `get_config` call for a concrete non-zero UID.

## Co-public caveat

The backend serves both the token/agent routes **and** `/llm` on the same port. When deployed publicly so Agora cloud can reach `/llm/chat/completions`, the token-minting routes (`/get_config`, `/startAgent`, `/stopAgent`) are also reachable from the internet. They are **unauthenticated** in this recipe.

**Before any real deployment:**
- Put auth (API key, JWT, mTLS) or rate-limiting on the token endpoints via an ingress or gateway.
- Validate `Authorization: Bearer` in `moderate()` or at the FastAPI route level.

## CORS

The backend sets `CORSMiddleware` with `allow_origins=["*"]` — open by design for a local/dev recipe. **Lock this down to known origins before any production deployment.**

## Validation

- `Agent.__init__` raises `ValueError` if `AGORA_APP_ID`, `AGORA_APP_CERTIFICATE`, `CUSTOM_LLM_URL`, or `CUSTOM_LLM_API_KEY` are absent; the FastAPI app catches this at startup and returns 500 until resolved.
- `Agent.start()` rejects empty `channel_name` and non-positive `agent_uid`/`user_uid` before issuing tokens or starting a session.
- Route errors are sanitized: `_log_route_error` logs only non-`None` context; SDK exceptions map to 400/500 without leaking internals to the client.

## Deployment notes

- Set `AGENT_BACKEND_URL` only to a backend you control; the rewrite forwards browser requests there verbatim.
- The published Docker image is a **single-process image** (`:8000`) serving both token/agent routes and `/llm`; it does not bundle secrets.
- When using a tunnel for local dev, the tunnel URL is only needed in `CUSTOM_LLM_URL`; the browser always connects through Next.js (`localhost:3000`).

## Related Deep Dives

- None.
