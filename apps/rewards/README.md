# Reward Engine (`apps/rewards`)

## Purpose
Decides what a user earns from validated revenue and moves it through the
pending → approved → wallet flow. The single entry point for all user credits.

## Module contract
- **Inputs:** validated revenue events (offer/survey/game/bonus/referral) and
  admin-configured `RewardRule`s.
- **Outputs:** `Reward` records and ledger transactions (pending, approval,
  reversal).
- **Dependencies:** `apps.ledger`, `apps.wallets`, `apps.adminpanel`.
- **Events emitted:** none directly (callers emit business events).
- **Events consumed:** none.
- **Database tables:** `RewardRule`, `Reward`.
- **Public APIs:** internal service; reward history exposed via
  `/api/v1/rewards/` (planned).
- **Security requirements:** services-only; never called with client-supplied
  amounts.

## Business rules
- Rule resolution: first active rule by priority matching source/provider/
  campaign/country/tier and payout conditions.
- Calculation supports percentage, fixed cash/points, points percentage,
  multiplier and `max_user_reward` cap.
- Zero reward → `RewardError` (configuration must be visible).
- One reward per (`source`, `source_reference`, `user`); replays are no-ops.
- Reward exceeding gross revenue logs a profitability warning.
- Pending rewards auto-approve after 30 minutes unless the rule requires manual
  approval or the reward is held.

## Key functions
- `RewardService.award(...)` — rule-based award
- `RewardService.award_fixed(...)` — explicit cash/points (games, bonuses,
  admin grants)
- `RewardService.approve/hold/reject/reverse(...)`
- `calculate_reward(rule, payout)`, `resolve_rule(...)`

## Tests
`pytest tests/test_critical_flows.py -q` (§144 percentage, §142 idempotency,
reversal, zero-rule error).
