# Development — Tap Target

## Structure

- `game.html` — markup and SDK script tags
- `js/game.js` — game loop, spawning, input, SDK integration
- `css/style.css` — presentation only

## Rules for changing this game

1. Keep the game self-contained: no imports from the platform codebase.
2. Only use the Game SDK for platform communication (`postMessage` protocol).
3. Never attempt to read cookies, tokens or call platform APIs directly.
4. Never award anything client-side — report the score and let the server pay.
5. Keep the game playable when `GameSDK.isConnected()` is false (offline mode).

## Tuning

| Constant (js/game.js) | Effect |
| --- | --- |
| `ROUND_SECONDS` | Round length |
| `SPAWN_INTERVAL_MS` | Target spawn rate |
| `TARGET_LIFETIME_MS` | How long a target stays |

Changing these changes difficulty; reward rules should be reviewed when
difficulty changes.

## Testing locally

1. Run the platform (`python manage.py runserver`).
2. Log in and open `/play/tap-target/`.
3. Play a full round; verify:
   - session created (network tab),
   - events reported,
   - `end` returns `ended` (not `invalidated`),
   - wallet balance increases by the configured rule.

## Packaging checklist

- [ ] `game.html` references `/static/game-sdk/game-sdk.js` (or the games-origin
      copy in production)
- [ ] No absolute URLs to the platform origin other than the SDK
- [ ] Documentation updated (`README`, `API`, `REWARD_RULES`, this file)
