# Reward Rules — Memory Match

Configured in the admin (`GameRewardRule`), never in game code.

| Rule | Conditions | Reward | Cooldown | Daily | Monthly |
| --- | --- | --- | --- | --- | --- |
| Easy | `{"min_score": 100}` | 5 points | 0h | 5 | 50 |
| Standard | `{"min_score": 500}` | 10 points | 0h | 5 | 50 |
| Perfect-ish | `{"min_score": 700}` | Rs 2 fixed cash | 4h | 2 | 20 |

Notes:
- Max score is 800 (8 pairs × 100, no extra moves).
- `Game.min_session_seconds` invalidates rushed sessions before rules run.
- Cash rewards are paid in the wallet currency (PKR by default).
