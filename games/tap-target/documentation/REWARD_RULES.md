# Reward Rules — Tap Target

Rewards are configured by admins in the platform (`GameRewardRule`), never in
the game code. The server evaluates rules after `endSession`.

## Rule fields

| Field | Meaning |
| --- | --- |
| `conditions.min_score` | Minimum final score required |
| `conditions.min_duration_seconds` | Minimum play time required |
| `mode` | `points` or `cash` |
| `points` / `cash` | Reward amount |
| `cooldown_hours` | Minimum time between rewarded sessions |
| `daily_max` / `monthly_max` | Reward frequency caps |

## Recommended starting rules

| Rule | Conditions | Reward | Cooldown | Daily | Monthly |
| --- | --- | --- | --- | --- | --- |
| Easy | score ≥ 5 | 5 points | 0h | 5 | 50 |
| Standard | score ≥ 15 | 15 points | 0h | 5 | 50 |
| Skilled | score ≥ 25 | Rs 2 (fixed cash) | 4h | 2 | 20 |

Notes:

- The first matching rule (by priority) wins; the game pays once per session.
- `Game.min_session_seconds` (admin) invalidates very short sessions before
  any rule runs.
- Cash rewards are paid in the user's wallet currency (PKR by default, ADR-015).
- Points rewards are optional; they are disabled by default at the product
  level, so prefer cash unless points are intentionally enabled.

## Anti-cheat notes

- Scores are validated server-side against session duration.
- Impossible score/duration combinations should be reviewed via `GameEvent`
  telemetry and can trigger fraud events.
