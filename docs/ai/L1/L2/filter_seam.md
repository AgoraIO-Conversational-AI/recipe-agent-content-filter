# Deep Dive — Filter Seam

**When to Read This:** You are replacing `moderate()` with a real moderation model, replacing `echo_reply()` with a real LLM, debugging why sentences are or are not redacted, or verifying the OpenAI SSE contract. For the high-level picture, start at [02_architecture](../02_architecture.md).

The filter seam lives entirely in `server/src/llm.py`. It has no `agora_agent` dependency — it is provider-agnostic by design.

## Call graph

```
POST /llm/chat/completions
  └─ run_agent_turn(messages)
       ├─ _extract_last_user_text(messages)  → user_text
       ├─ echo_reply(user_text)              → raw reply text
       └─ filter_reply(raw_reply)            → filtered reply text
            └─ moderate(sentence)            per sentence  → True (allow) / False (redact)
```

## Symbol reference

| Symbol | Signature | Role |
| ------ | --------- | ---- |
| `moderate` | `(sentence: str) -> bool` | **Pluggable seam.** `True` = allow, `False` = redact with `REDACTION`. |
| `filter_reply` | `(text: str) -> str` | Splits `text` on `(?<=[.!?])\s+`; calls `moderate()` per sentence; joins. |
| `echo_reply` | `(user_text: str) -> str` | Mock generator: three-sentence reply where the middle sentence echoes the user. |
| `run_agent_turn` | `(messages: list) -> str` | Top-level: extract last user message → `echo_reply` → `filter_reply`. |
| `_extract_last_user_text` | `(messages: list) -> str` | Walks `messages` in reverse; handles `str` and `list[TextContent]` content. |
| `REDACTION` | `str` | `"Content filtered."` — the replacement for any redacted sentence. |
| `FILTER_BANNED_TERMS` | `list[str]` | Parsed from `os.getenv("FILTER_BANNED_TERMS", "strawberries")`, lowercased, stripped. |

## Sentence splitting

`_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")` — splits on whitespace that follows a sentence-ending punctuation mark. Single-sentence inputs are not split (no trailing punctuation match needed; `filter_reply` treats them as a single sentence).

Example:
- Input: `"Sure, I can help. You said: strawberries. Is there anything else?"`
- Sentences: `["Sure, I can help.", "You said: strawberries.", "Is there anything else?"]`
- After filter (banned=`strawberries`): `"Sure, I can help. Content filtered. Is there anything else?"`

## Replacing `moderate()`

Replace only this body. Signature and return type are the stable contract:

```python
def moderate(sentence: str) -> bool:
    """Return True if allowed, False to redact."""
    # Example: call an LLM classifier
    result = my_moderation_api(sentence)
    return result.is_safe
```

Existing tests (`test_filter.py`) still apply. Add tests for your moderation logic; run `cd server && pytest tests -v`.

## Replacing `echo_reply()`

Replace only this body. The function must return a plain string that `filter_reply` can split into sentences:

```python
def echo_reply(user_text: str) -> str:
    """Real LLM call — still runs through filter_reply."""
    return my_llm_client.complete(user_text)
```

After this change the recipe is no longer zero-key. Add the new API key as an env var and document it in `server/.env.example`.

## OpenAI SSE contract

`/llm/chat/completions` must produce this SSE sequence:

```
data: {"id":"chatcmpl-...","object":"chat.completion.chunk","created":...,"model":"...","choices":[{"index":0,"delta":{"role":"assistant","content":""},"finish_reason":null}]}

data: {"id":"chatcmpl-...","object":"chat.completion.chunk","created":...,"model":"...","choices":[{"index":0,"delta":{"content":"word"},"finish_reason":null}]}

... (one chunk per word, 50ms delay)

data: {"id":"chatcmpl-...","object":"chat.completion.chunk","created":...,"model":"...","choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}

data: [DONE]
```

Agora ConvoAI Engine requires:
- `stream: true` (return 400 otherwise).
- First chunk sets `delta.role = "assistant"`.
- Final chunk sets `finish_reason = "stop"`.
- Stream terminates with `data: [DONE]`.

## Testing

`test_llm_mount.py` verifies:
- `/llm/health` returns `{ "status": "ok" }`.
- `POST /llm/chat/completions` returns 200 + `text/event-stream` + `[DONE]` terminator.
- `llm.py` has no Agora SDK import (AST inspection).

`test_filter.py` verifies:
- `moderate` allows clean sentences and flags banned terms.
- `filter_reply` redacts only the offending sentence.
- `run_agent_turn` redacts the echoed banned term end-to-end.

## Related L1

- [02_architecture](../02_architecture.md) · [04_conventions](../04_conventions.md) · [06_interfaces](../06_interfaces.md) · [07_gotchas](../07_gotchas.md)
