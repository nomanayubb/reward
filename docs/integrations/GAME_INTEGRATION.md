# Game Integration

Games are **self-contained, untrusted** HTML5 packages. The platform wraps them
in a sandboxed iframe and communicates only through the Game SDK. Game code
never touches the wallet, cookies, auth tokens or admin APIs.

## 1. Folder contract

```
games/
  <game-slug>/
    game.html
    assets/
    css/
    js/
    images/
    documentation/
      README.md          # what the game is, controls, how to run
      INSTALL.md         # how to add/replace the game in the platform
      CONFIGURATION.md   # configurable values
      REWARD_RULES.md    # example reward rules for this game
      API.md             # SDK calls this game uses
      TROUBLESHOOTING.md
```

The platform references `Game.entry_path` (e.g. `flappy-example/game.html`).
Each game carries its own docs so a future developer/AI can modify the game
without reading the whole platform.

## 2. Session flow

```
User opens game
  → platform creates GameSession (server token, ip, device hash)
  → iframe loads games/<slug>/game.html with ?session=<token>&origin=<platform>
  → GameSDK.startSession()
  → gameplay; GameSDK.reportEvent()/reportScore() (telemetry only)
  → GameSDK.endSession(score)
  → platform validates duration/score server-side
  → GameRewardRule conditions evaluated
  → RewardService awards (pending → approved)
```

The client can **request** an end-of-session; only the server decides rewards.

## 3. Game SDK contract

Static assets live in `static/game-sdk/`. The SDK communicates via
`postMessage` with strict origin checks:

| Call | Message | Server action |
| --- | --- | --- |
| `GameSDK.startSession()` | `{type: "start"}` | validates token, marks session active |
| `GameSDK.reportEvent(name, data)` | `{type: "event"}` | stores `GameEvent` (telemetry) |
| `GameSDK.reportScore(score)` | `{type: "score"}` | stores score candidate |
| `GameSDK.endSession(score)` | `{type: "end"}` | validates + evaluates reward rules |
| `GameSDK.requestReward()` | `{type: "reward"}` | returns status only; never pays directly |
| `GameSDK.getUser()` | `{type: "user"}` | non-sensitive profile fields only |
| `GameSDK.getConfiguration()` | `{type: "config"}` | per-game public config |

Responses are posted back to the game iframe only at the registered origin.

## 4. Server-side validation (mandatory)

- Session must exist, be `ACTIVE`, and belong to the requesting user.
- `duration_seconds >= game.min_session_seconds`.
- `GameRewardRule.conditions` (`min_score`, `min_duration_seconds`) are checked
  on the server.
- Cooldown (`cooldown_hours`), `daily_max`, `monthly_max` enforced against
  ended sessions.
- Suspicious sessions (impossible scores/durations, replayed tokens) are marked
  `INVALIDATED` and may raise a fraud event.

## 5. Security requirements

- iframe `sandbox="allow-scripts"` (no `allow-same-origin`) and a separate
  origin (`games.example.com`) in production.
- CSP on the game origin; no cookies sent; no access to platform APIs.
- Origin verification on every `postMessage`.
- Rate limiting per session and per user.
- Never expose wallet balances, tokens or admin endpoints to game JS.

## 6. Configuring rewards (admin)

For each game, admins create one or more `GameRewardRule` rows:

| Field | Meaning |
| --- | --- |
| `conditions` | `{"min_score": 1000}` / `{"min_duration_seconds": 600}` |
| `mode` | `points` or `cash` |
| `points` / `cash` | amount |
| `cooldown_hours` | minimum time between rewarded sessions |
| `daily_max` / `monthly_max` | reward frequency caps |

Example: score ≥ 1000 → 10 points, 24h cooldown, 1/day, 20/month.

## 7. Checklist for adding a game

1. Copy the game into `games/<slug>/` with its `documentation/` folder.
2. Integrate the Game SDK in `game.html` (see `static/game-sdk/`).
3. Add a `Game` row (slug, title, category, `entry_path`, min session seconds).
4. Add reward rule(s) in the admin.
5. Play a full session in staging and verify: session created, event recorded,
   duration validated, reward pending → approved, ledger entries balanced.
