# Development — Snake

- Self-contained: no imports from the platform codebase; only the Game SDK.
- Never award anything client-side; report the score and let the server pay.
- Keep offline mode working (`GameSDK.isConnected()` false).

## Tuning (js/game.js)

| Constant | Effect |
| --- | --- |
| `CELLS` | Grid size (board is `CELLS × CELLS`) |
| `TICK_MS` | Movement speed (lower = faster) |
| `ROUND_SECONDS` | Round length |

## Testing

1. `python manage.py runserver`
2. Log in → `/play/snake/`
3. Play a full round; verify session start, score events, `end` returns
   `ended` (not `invalidated`), and the wallet credit matches the rule.
