# Development — Memory Match

- Self-contained: no imports from the platform codebase; only the Game SDK.
- Never award anything client-side; report the score and let the server pay.
- Keep offline mode working (`GameSDK.isConnected()` false).

## Tuning (js/game.js)

| Constant | Effect |
| --- | --- |
| `PAIR_COUNT` | Number of pairs (board size = `PAIR_COUNT * 2`) |
| `SYMBOLS` | Card symbols (must have ≥ `PAIR_COUNT` entries) |
| `REVEAL_MS` | How long a wrong pair stays visible |

## Testing

1. `python manage.py runserver`
2. Log in → `/play/memory-match/`
3. Play a full board; verify session start, score events, `end` returns
   `ended` (not `invalidated`), and the wallet credit matches the rule.
