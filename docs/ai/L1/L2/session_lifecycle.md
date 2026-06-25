# Deep Dive — Session Lifecycle

**When to Read This:** You are touching client-side channel join, token renewal, mid-call agent start/stop, RTM transcript mapping, or the `Agent._sessions` in-memory map. For the high-level picture, start at [02_architecture](../02_architecture.md).

## Browser orchestration

```
LandingPage.tsx
  ├─ getConfig({ channel?, uid? })          → { app_id, token, uid, channel_name, agent_uid }
  ├─ AgoraRTC.join(app_id, channel, token, uid)   [RTC join]
  ├─ RTM login + subscribe                        [transcript/metrics channel]
  ├─ startAgent(channelName, rtcUid, userUid)     → agent_id
  └─ on disconnect → stopAgent(agent_id)
```

Teardown runs in reverse: `stopAgent` → RTM unsubscribe + logout → RTC leave.

## Token issuance

`GET /get_config` mints a Token007 valid for both RTC and RTM, expiring in 3600s. The backend always issues a token for a **concrete non-zero UID**:

- `uid` query param absent, zero, or negative → backend generates a random UID in `[1000, 9_999_999]`.
- `agent_uid` is always randomly generated (`[10_000_000, 99_999_999]`) and returned alongside the user UID.

## `Agent._sessions` map

`start()` stores each live session by `agent_id`:

```python
self._sessions[agent_id] = session
```

`stop()` pops the session and calls `session.stop()`. If the session is not found (e.g. after a backend restart), it falls back to `self.client.stop_agent(agent_id)`. This means stop is best-effort across restarts; reconnecting the browser will issue a new `getConfig` + `startAgent`.

## Vendor chain wiring

```python
agora_agent = AgoraAgent(
    client=self.client,
    instructions=CUSTOM_LLM_PROMPT,
    greeting=self.greeting,
    failure_message="Please wait a moment.",
    max_history=50,
    turn_detection={ ... },          # vad config, see 07_gotchas
    advanced_features={"enable_rtm": True, "enable_tools": True},
    parameters=parameters,
)
agora_agent = agora_agent.with_stt(stt).with_llm(llm).with_tts(tts)
session = agora_agent.create_async_session(
    channel=channel_name,
    agent_uid=str(agent_uid),
    remote_uids=[str(user_uid)],
    enable_string_uid=False,
    idle_timeout=30,
    expires_in=3600,
)
agent_id = await session.start()
```

Key differences from the realtime recipe:
- `.with_llm(llm)` (cascading vendor chain) instead of `.with_mllm(mllm)`.
- `turn_detection` is set on `AgoraAgent(...)` directly (not on the LLM vendor).
- STT and TTS are explicit vendor objects (`DeepgramSTT`, `MiniMaxTTS`).

## Session parameters

| Key                    | Value     | Why                                              |
| ---------------------- | --------- | ------------------------------------------------ |
| `audio_scenario`       | `chorus`  | Ultra-low-latency profile for web clients.       |
| `data_channel`         | `rtm`     | Transcript + metrics delivered over RTM.         |
| `enable_error_message` | `true`    | Surface agent-side errors to the client.         |
| `enable_metrics`       | `true`    | Emit pipeline metrics to the UI.                 |
| `output_audio_codec`   | optional  | Forwarded from `POST /startAgent` `parameters`.  |

## Transcript UID normalization

RTM transcript events use `uid === '0'` for the local participant in some SDK versions. `normalizeTranscript` in `web/src/lib/conversation.ts` maps `uid === '0'` to the local user's UID. Preserve this — speaker identification in the UI depends on concrete UIDs.

## Related L1

- [02_architecture](../02_architecture.md) · [06_interfaces](../06_interfaces.md) · [07_gotchas](../07_gotchas.md)
