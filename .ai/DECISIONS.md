# ARCHITECTURAL DECISIONS

## ADR-001 — PostgreSQL as the production database

Decision: PostgreSQL for all real environments; SQLite only for local dev and
tests.
Reason: financial integrity, transactions, row locking, relational queries.
Status: Accepted.

## ADR-002 — Immutable double-entry ledger

Decision: all financial movement is balanced, immutable ledger transactions;
wallet balances are cached projections.
Reason: auditability, prevention of balance corruption, safe reversals.
Status: Accepted.

## ADR-003 — Provider adapters

Decision: every external network (CPA, surveys, payments) is isolated behind an
adapter interface with normalized internal types.
Reason: prevents vendor-specific logic from contaminating core code.
Status: Accepted.

## ADR-004 — HTML5 games are isolated

Decision: games are self-contained folders executed in a sandboxed iframe; the
client is never trusted for rewards.
Reason: security and maintainability; each game carries its own docs.
Status: Accepted.

## ADR-005 — Money is Decimal / NUMERIC(20,8)

Decision: `apps.common.fields.money_field`; no floats; nullable money fields
have no default.
Reason: exactness for fiat and crypto; distinguishes "unset" from zero.
Status: Accepted.

## ADR-006 — Reward rules are database configuration

Decision: reward splits, points conversion, caps and scopes live in
`RewardRule`/`PlatformSetting`, not code.
Reason: the core product requirement — configurable without deploys.
Status: Accepted.

## ADR-007 — Service layer owns business logic

Decision: views/API/tasks are thin; services own transactions, locking,
idempotency and ledger calls.
Reason: consistency of financial rules across all entry points.
Status: Accepted.

## ADR-008 — Modular monolith

Decision: one Django deployment with per-module service/task/README contracts,
service-oriented boundaries for future extraction.
Reason: speed of development with clear seams; avoids premature microservices.
Status: Accepted.

## ADR-009 — Runtime settings in the database

Decision: `PlatformSetting` (cached) with `ConfigurationVersion` history;
security-critical infrastructure config stays in environment variables.
Reason: admin configurability without exposing secrets to the DB UI.
Status: Accepted.

## ADR-010 — Reward lifecycle: pending → approved

Decision: awards credit a pending bucket first, then move to cash/points on
approval (auto after 30 minutes unless manual approval is required).
Reason: provider reversals and fraud holds without touching user cash.
Status: Accepted.

## ADR-011 — Idempotency via database constraints

Decision: unique constraints on external identifiers (e.g. provider +
external conversion id) rather than application-only checks.
Reason: race-safe duplicate prevention for money paths.
Status: Accepted.

## ADR-012 — AI development protocol

Decision: `.ai/` project memory (GOAL/RULES/STATE/TASKS/HISTORY/MASTER/
DECISIONS/SESSION) + `AGENTS.md` + check scripts; one coherent change per
commit; commit + push after verification.
Reason: persistent project memory, minimal repeated context, safe incremental
development.
Status: Accepted.

## ADR-013 — Ad monetization policy

Decision: monetize with house ads and direct sponsorships first; ad-network
integration (PropellerAds/Adsterra/Monetag) only after per-campaign policy
verification; Google AdSense only on SEO content pages, never on
reward/game/offer pages.
Reason: incentivizing clicks or views violates AdSense policy (account-ban
risk) and most networks restrict incentivized traffic. Rewarding ad clicks is
never allowed unless the program explicitly permits it.
Status: Accepted.

## ADR-014 — Points follow the same pending → approved flow as cash

Decision: awarded points are held in a system pending-points account and move
to the user's points account only on approval. Reversing an approved reward
unwinds both the pending and the approval postings. There is exactly one
points account per wallet (currency `POINTS`).
Reason: the first implementation credited points at award *and* approval
(double-credit bug) and `ensure_accounts` created a second points account in
wallet currency. One flow for every reward currency, one account per purpose.
Status: Accepted.
