# Content-Filter LLM Endpoint

An OpenAI-compatible `POST /chat/completions` server (port 8001) that Agora cloud
calls during a conversation. This endpoint echoes the user's words and then runs a
**sentence-level keyword filter** before streaming the response — so you can
trigger audible redaction just by saying a banned term.

It has no `agora-agents` dependency — it is a plain FastAPI app, which is exactly
the boundary you replace or extend with your own model and moderator.

**Zero-key:** no LLM API key required.

## How it works

1. `echo_reply(user_text)` builds a three-sentence reply: a clean opener, a
   sentence echoing the user (potentially flagged), and a clean closer.
2. `filter_reply(text)` splits the reply at sentence boundaries (`.`, `!`, `?`)
   and passes each sentence to `moderate()`.
3. `moderate(sentence)` checks whether any term from `FILTER_BANNED_TERMS`
   (default: `strawberries`, comma-separated, set via env var) appears in the
   sentence. Returns `False` → sentence becomes `"Content filtered."`.
4. The filtered text is streamed back as OpenAI SSE.

## The pluggable seam

`moderate()` in `src/custom_llm_server.py` is the **seam**. Its current body does
a simple substring check. Replace it with a real moderator model call (e.g. an LLM
classification request) to get the "LLM-powered" variant — `filter_reply()` and
`run_agent_turn()` stay unchanged.

## The contract

Implement `POST /chat/completions` returning OpenAI-style SSE:

- first chunk sets `delta.role = "assistant"`
- content chunks carry `delta.content`
- a final chunk sets `finish_reason = "stop"`
- the stream terminates with `data: [DONE]`

Only streaming (`stream: true`) is supported; non-streaming requests return 400.

## Run

```bash
cd llm
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python src/custom_llm_server.py     # serves on CUSTOM_LLM_PORT (default 8001)
```

## Environment variables

| Variable | Default | Notes |
| --- | --- | --- |
| `CUSTOM_LLM_PORT` | `8001` | Port the server listens on |
| `FILTER_BANNED_TERMS` | `strawberries` | Comma-separated banned terms; case-insensitive |

Put these in `llm/.env.local`.

## Expose it publicly

Agora cloud — not the browser — calls this server, so it must be reachable from
the public internet. For local dev, tunnel it:

```bash
ngrok http 8001
```

Then set `CUSTOM_LLM_URL=https://<tunnel>/chat/completions` in `server/.env.local`.

## Auth

This mock does **not** authenticate. A production endpoint should validate the
`Authorization: Bearer <CUSTOM_LLM_API_KEY>` header that Agora cloud forwards
(the key you set on the agent backend).

## Replacing the mock

The filter + seam live in `run_agent_turn()` / `moderate()` / `filter_reply()` in
`src/custom_llm_server.py`:

- Replace `moderate()`'s body for a real moderator (LLM-powered variant).
- Replace `echo_reply()` with a real LLM call for a production-grade response
  pipeline that still runs through the filter.
