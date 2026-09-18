# Reward Rules — Snake

Configured in the admin (`GameRewardRule`), never in game code.

| Rule | Conditions | Reward | Cooldown | Daily | Monthly |
| --- | --- | --- | --- | --- | --- |
| Easy | `{"min_score": 3}` | 5 points | 0h | 5 | 50 |
| Standard | `{"min_score": 10}` | 15 points | 0h | 5 | 50 |
| Skilled | `{"min_score": 20}` | Rs 3 fixed cash | 4h | 2 | 20 |

Notes:
- Score is food eaten; 90 seconds is the cap, so 20+ requires fast play.
- `Game.min_session_seconds` invalidates rushed sessions before rules run.
- Cash rewards are paid in the wallet currency (PKR by default).
