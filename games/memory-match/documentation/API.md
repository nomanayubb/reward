# API — Memory Match

Uses the Game SDK (`/static/game-sdk/game-sdk.js`); the host page performs the
API calls with the user's session.

| Call | When | Payload |
| --- | --- | --- |
| `GameSDK.startSession()` | Start pressed | — |
| `GameSDK.reportEvent("game_start", {pairs})` | Start pressed | telemetry |
| `GameSDK.reportScore(score)` | After each match | telemetry |
| `GameSDK.endSession(score)` | All pairs found | server validates and pays |

Server endpoints: `POST /api/v1/games/memory-match/sessions/`,
`…/sessions/<token>/events/`, `…/sessions/<token>/end/`.
The server decides the reward; client scores are never trusted.
