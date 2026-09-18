# API — Tap Target

This game uses the Game SDK (`/static/game-sdk/game-sdk.js`). The SDK talks to
the platform host page via `postMessage`; the host page calls the platform API
with the user's session. The game never sees cookies or tokens.

## Calls used

| Call | When | Payload | Notes |
| --- | --- | --- | --- |
| `GameSDK.startSession()` | Start button pressed | — | Creates a server session; required before any report |
| `GameSDK.reportEvent(name, data)` | Round start | `game_start` + `{round_seconds}` | Telemetry only |
| `GameSDK.reportScore(score)` | Every hit | `{score}` | Telemetry only |
| `GameSDK.endSession(score)` | Timer reaches 0 | `{score}` | Server validates duration/score and pays the reward |
| `GameSDK.isConnected()` | Boot | — | False when opened outside the platform |

## Server endpoints behind the SDK

```
POST /api/v1/games/tap-target/sessions/           -> { session_token, status, ... }
POST /api/v1/games/sessions/<token>/events/       -> { ok: true, event_id }
POST /api/v1/games/sessions/<token>/end/          -> { status, duration_seconds, score }
```

## Guarantees

- `endSession` is the only call that can produce a reward, and only the server
  decides it (duration, score conditions, cooldowns, caps).
- Replaying or faking client scores cannot mint rewards: the server recomputes
  from its own session record.
- Events and scores are stored with the session for anti-cheat review.
