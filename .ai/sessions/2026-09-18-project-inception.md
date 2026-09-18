# Session 2026-09-18 — Project inception, foundation build, AI protocol, auth API

Participants: product owner (noman), coding agent.

---

## 1. Project created

**User request:** "create folder in local d disk named reward project" →
"cd reward project" → "now thats our project folder".

**Agent:** Created `D:\reward project`. This is the project root from now on.

Note: the same chat thread earlier contained unrelated requests (car company
name lists). Those are not part of this project and are not logged here.

## 2. Master PRD + DRD delivered

**User:** Pasted the complete MASTER PRD + DRD for the "Rewards Gaming, Surveys
& CPA Platform" (250 numbered sections): vision, business model, reward
currency, wallets, ledger, games, surveys, CPA/offerwall, compliance, postbacks,
withdrawals, payments, KYC, fraud, admin, automation, SEO, CMS, phases,
deployment, architecture principles.

**Agent:** Saved the substance as `docs/PRD.md` and `docs/DRD.md`; built the
entire Phase 1 foundation:

- Django project + `config` package (base/dev/prod/test settings), Celery,
  Docker, Nginx, requirements, `.env.example`.
- 26 apps with models + migrations + Django admin: accounts, users, wallets,
  ledger, rewards, payments, deposits, withdrawals, games, surveys, offers,
  cpa, advertising, bonuses, referrals, fraud, risk, kyc, notifications,
  automation, analytics, reports, cms, seo, support, adminpanel.
- Immutable double-entry ledger (locking, idempotency, reversals).
- Wallet provisioning + system wallet + liability totals.
- Configurable reward engine (rules, calculation, pending → approved).
- Offers: eligibility engine, campaign quotas, clicks, conversions, postbacks.
- Surveys + games services, deposits/withdrawals state machines.
- Provider adapter interfaces (CPA / surveys / payments).
- Fraud/risk scoring, automation event bus, notifications.
- Celery tasks + beat schedule; postback + webhook endpoints.
- Docs: PRD, DRD, ARCHITECTURE, DATABASE, GAME_INTEGRATION, CPA_INTEGRATION.
- 11 critical business-rule tests (`tests/test_critical_flows.py`).

**Bug found and fixed during testing:** `money_field(null=True)` forced a `0`
default, so `RewardRule.max_user_reward` defaulted to 0 and clamped every
reward to zero. Fixed in `apps/common/fields.py`; nullable money fields now
default to NULL.

## 3. API status question

**User:** "api working?"

**Agent:** Verified with the Django test client: `/api/v1/schema/` 200,
`/api/v1/docs/` 200, `/admin/login/` 200, postback/webhook endpoints wired
(404 for unknown provider), business endpoints still stubs. Reported honestly.

## 4. AI development protocol adopted

**User:** Pasted the full operating protocol spec (repository structure,
`.ai/` memory files, `AGENTS.md`, scripts, Git workflow, commit style, session
completion, context efficiency, etc.) and asked to install it.

**Agent installed:**

- `.ai/`: GOAL, RULES, STATE, HISTORY, MASTER, TASKS, ARCHITECTURE, DECISIONS,
  SESSION (+ earlier CODING_RULES, DATABASE_RULES, SECURITY_RULES,
  REWARD_RULES, PROJECT_RULES).
- `AGENTS.md` at root (37-section protocol).
- `scripts/project-check.{sh,ps1}`, `scripts/session-finish.{sh,ps1}`.
- `docs/` subfolders: api, modules, integrations, deployment, security;
  moved integration docs to `docs/integrations/`.
- GitHub Actions CI (`.github/workflows/ci.yml`), `.gitattributes`,
  `.gitkeep` placeholders.
- Git repository initialized (branch `main`).

## 5. GitHub remote + pushes

**User:** Provided remote: `https://github.com/nomanayubb/reward`.

**Agent:** Added `origin`, committed, pushed after the user authenticated.
Subsequent pushes from the agent's shell kept hanging on the interactive
GitHub credential prompt, so the user ran `git push` manually each time.
SSH key setup was offered; decision pending.

## 6. Status review

**User:** Asked where the project is, whether admin/user apps are ready, wallet
test status, which ads to use, and what remains.

**Agent:** Reported verified status: 72 models admin-registered; user app has
models but no endpoints/pages (at that time); 11 wallet/ledger tests passing
with listed gaps; ads = models only; recommended house/direct ads first and
**never AdSense on reward pages** (policy risk).

## 7. Memory alignment + ads policy

**User:** Asked that everything (done vs remaining) be written in the
documents so a new session understands the project.

**Agent:** Updated `.ai/TASKS.md` (added P9 — Advertising, precise gaps),
`.ai/STATE.md` (Known Problems), recorded **ADR-013 — ad monetization
policy**, appended HISTORY entry. Commit `2ac7f29`.

## 8. Ruff task

**User:** "ok do it".

**Agent:** Added `ruff.toml` (E/F/I/UP/B/C4/SIM/DJ; migrations excluded),
fixed 61 auto-fixable + 10 manual findings (unused imports, import order,
`StrEnum`, simplifications). `scripts/project-check` now passes end-to-end.
Commit `2907a87`.

## 9. Push-auth explanation

**User:** "why you not able to do push".

**Agent:** Explained: HTTPS remote + Git Credential Manager needs an
interactive prompt the agent's shell cannot complete; the user must push
manually until SSH is configured. Credential is not persisting
(`credential.credentialStore` unset).

## 10. Auth API (first user-facing feature)

**User:** Implicitly continued the task list.

**Agent:** Implemented `apps/accounts` auth API:
`POST /api/v1/auth/register/`, `login/`, `logout/`, `GET me/`.
Reuses `register_user` service (wallet + referral provisioning), applies Django
password validators, throttles login/register (`login` scope), 8 API tests
added (19 total). Test settings now disable throttling and whitenoise.
Commit `08672f8`.

## 11. Requirements traceability

**User:** Asked whether their requirements are tracked as fulfilled or not, and
which CPA is being used.

**Agent:** Created `.ai/REQUIREMENTS.md`: 50 requirement areas with
✅/🟡/⬜ status, explicit integration status (no CPA/survey/payment network
selected), and four decisions needed from the product owner. Commit `63060f0`.

## 12. Conversation history request (this section)

**User:** "we need full conversation history also to be saved, not to recall
every time but only in new session beginning, and all other things will be
saved in other documents just like our workflow already is."

**Agent:** Created `.ai/sessions/` with this log and a README convention;
updated `AGENTS.md` and `.ai/RULES.md` so every future session writes a log
at session end and reads the latest log at session start.

## 13. Wallet + ledger read endpoints

**User:** "now what to do" → after pushing, the agent continued with the next
task from `.ai/STATE.md`.

**Agent:** Built `GET /api/v1/wallets/summary/` (cash/pending/locked/bonus/
points + accounts) and `GET /api/v1/ledger/transactions/` (paginated,
user-scoped, `type`/`status` filters), with 8 tests (27 total).

While testing, two reward-engine bugs were found and fixed:

- Points were credited twice (once at award, again at approval).
- Two points accounts existed per wallet: currency `USD` (created by account
  provisioning) and currency `POINTS` (created by the rewards flow).

Fix: points now follow the same pending → approved flow as cash via a system
pending-points holding account; reversing an approved reward unwinds both the
pending and approval postings (ADR-014). Stale zero-balance USD points accounts
were removed from the dev database.

Commits: `0d2996e`, `36d6d72`.

## 14. PKR currency decision + slices 1-2

**User:** "payment will be in pkr" → answered the follow-up questions with
"dual wallets USD + PKR" and, on points, "i think if direct pkr not point not
its look more good" (asked what is best).

**Agent:** Recommended and recorded direct-PKR rewards with the points engine
kept but disabled by default (ADR-015), dual wallets (PKR primary, USD for
crypto), USD→PKR conversion with the rate stored per transaction, all limits
in PKR. Planned four migration slices.

- Slice 1 (`d03b973`): multi-currency wallet accounts provisioned per currency;
  ledger enforces per-currency zero-sum so cross-currency leakage is rejected.
  4 tests.
- Slice 2: `apps/payments/services.py` exchange-rate service
  (`EXCHANGE_RATE_USD_PKR`, admin-configurable), `RewardRule.reward_currency`
  (default PKR) and `Reward.currency` default PKR; percentage rewards convert
  USD→PKR with the rate stored in reward metadata; fixed amounts are already
  in the reward currency; platform share computed in the revenue currency;
  wallet default currency is PKR; deposits/withdrawals default to the wallet
  currency. Global test cache clearing added (settings cache leaked between
  tests). 42 tests total.

Commits: `d03b973` (slice 1), slice 2 commit.

## 15. PKR migration slices 3-4 (complete)

**User:** "next" — continue the planned slices.

**Agent:**

- Slice 3: withdrawal limits are configured in PKR
  (`MIN/MAX_WITHDRAWAL_PKR`, `KYC_THRESHOLD_PKR`, `AUTO_PAYOUT_MAX_PKR`,
  `DUAL_APPROVAL_THRESHOLD_PKR`) and converted for other wallet currencies;
  5 new limit tests; DRD W5/W6 updated.
- Slice 4: wallet summary now returns per-currency buckets
  (`balances`: PKR primary + USD) plus the existing primary-currency fields;
  API docs updated to mark auth/wallets/ledger live. The PKR migration
  (ADR-015) is complete.

Commits: `377a14f` (slice 3), slice 4 commit. 48 tests total.

## 16. Earning catalog + money movement APIs

**User:** "next" (twice) — continue the task list.

**Agent:**

- Catalog endpoints: `GET /api/v1/games/` (active games),
  `GET /api/v1/offers/` (eligibility-filtered via the shared engine, tracking
  URLs never exposed) and `GET /api/v1/surveys/`. 7 tests (55 total).
  Commit `30eff71`.
- Money endpoints: `GET/POST /api/v1/withdrawals/` (reservation handled by the
  service), `GET/POST /api/v1/withdrawals/methods/` (ownership enforced) and
  `GET/POST /api/v1/deposits/`; added a `manual` payment provider adapter for
  development/testing so deposits can be exercised without a real PSP. 10 tests
  (65 total). Commit `4069e64`.

## 17. Notifications + game session APIs

**User:** "next".

**Agent:** Added the notifications API (list/unread filter, mark read,
read-all, unread count) and the game session API (`<slug>/sessions/`,
`sessions/<token>/events/`, `sessions/<token>/end/`) with server-side
validation and reward payment on end. 12 tests (77 total). Commit `903ee7b`.

## 18. Game SDK + first playable game

**User:** "next".

**Agent:** Built the Game SDK (iframe side `game-sdk.js` + platform side
`game-host.js` with `event.source`/origin validation), the player page
(`/play/<slug>/`), dev asset serving (`/games/<slug>/<asset>` with
path-traversal protection) and the reference game `games/tap-target/`
(game.html + js/css + its own `documentation/`). Added
`manage.py seed_reference_game` (creates the game + starter points rule).
7 tests (84 total). Commit `f5b93f3`.

---

## Decisions made this session

- ADR-013: house ads / direct sponsorships first; AdSense only on content
  pages; never reward ad clicks.
- Adopt the `.ai` project-memory workflow + `AGENTS.md` operating protocol.
- Auth API uses session authentication (DRF) with login/register throttling.

## Open questions / blockers

1. Which CPA network first? (candidates listed in `REQUIREMENTS.md`)
2. Which survey provider first?
3. EasyPaisa merchant/API availability — confirmed or alternative method?
4. KYC policy (threshold, manual vs vendor)?
5. SSH key setup for automatic agent pushes — pending user decision.
6. Ads: when to start (house ads recommended first).

## Commits this session

`0e69b96`, `5e29c59`, `91fc708`, `2ac7f29`, `2907a87`, `08672f8`, `63060f0`,
`095bce0`, `0d2996e`, `36d6d72`, plus the session-log commit.
