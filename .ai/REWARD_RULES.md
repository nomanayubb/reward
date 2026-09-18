# REWARD_RULES

## The flow (never bypass it)

```
gross_revenue → RewardRule → calculate_reward() → RewardService._issue()
  → pending ledger credit → RewardService.approve() → cash/points credit
```

All credits go through `apps/rewards/services.py`. Games, surveys, offers,
bonuses, referrals and admin adjustments included.

## Rule resolution

First active `RewardRule` by `priority` where:
- `source` matches (or `any`),
- `provider_code` / `campaign_type` / `country` / `user_tier` match when set,
- `conditions.min_payout` / `max_payout` pass.

## Calculation

| Field | Effect |
| --- | --- |
| `user_percentage` | % of validated revenue paid as cash |
| `fixed_cash` | flat cash added |
| `points_percentage` | % of revenue converted to points |
| `fixed_points` | flat points added |
| `multiplier` | multiplies computed cash/points |
| `max_user_reward` | hard cap on cash (NULL = no cap) |

`mode` is informational (cash/points/hybrid) for the admin UI; calculation uses
whichever fields are set.

## Invariants

- `cash <= 0 and points <= 0` → raise `RewardError` (never silently zero).
- One reward per (`source`, `source_reference`, `user`) — replays return the
  existing reward with `created=False`.
- If `user_reward > gross_revenue`: log a warning; the admin UI must warn and
  require confirmation before saving such a rule.
- Pending rewards auto-approve after 30 minutes unless
  `requires_manual_approval` or the reward is held.
- Reversal compensates ledger entries; never edit or delete reward/ledger rows.

## Ledger mapping

- Award: platform cash `-amount`, user pending `+amount` (key
  `reward:{id}:pending`); points equivalent on the points ledger.
- Approve: pending `-amount`, cash `+amount` (key `reward:{id}:approve`).
- Reject: reversal of the pending transaction(s).
- Reverse: reversal of the approve transaction(s).

## Configuration, not code

New reward behaviors (tiers, campaigns, hybrid splits, caps) must be expressible
as `RewardRule` fields or `PlatformSetting` values — not new `if` branches in
services.
