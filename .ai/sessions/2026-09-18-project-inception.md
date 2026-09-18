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

## 19. NOWPayments adapter

**User:** "next" (and interrupted the check run with another "next" — the
adapter work was completed and verified after).

**Agent:** Implemented the NOWPayments adapter (real HTTP client via stdlib
urllib, HMAC-SHA512 IPN signature verification with constant-time compare,
status mapping, PKR→USD invoice conversion using the stored exchange rate,
`check_payment`, and an honest `NotImplementedError` for payouts pending
payout-API verification). Setup + sandbox checklist in
`docs/integrations/NOWPAYMENTS.md`. 8 tests (92 total).

Commit: `feat(payments): add NOWPayments adapter with IPN verification`.

## 20. Frontend (server-rendered pages)

**User:** "next".

**Agent:** Built the frontend: base layout + navigation, auth pages (login,
register, logout via Django forms), dashboard (balances, recent rewards,
quick links), wallet page (per-currency buckets), transaction history,
games/offers/surveys catalogs (offers eligibility-filtered), withdraw page
(payout methods + request form), deposit page (payment instructions) and
alerts. Fixed a name-shadowing bug where the page login view inherited from
the DRF login view (page POSTs returned JSON 400s). 19 tests (111 total).

Commit: `feat(web): add server-rendered pages for earning, wallet and payments`.

## 21. Admin operations UI

**User:** "next".

**Agent:** Built the staff-only admin panel at `/admin-panel/`: metrics
dashboard (users, provider revenue, rewards by currency, pending rewards,
open withdrawals, confirmed deposits today, user liability PKR/USD, open fraud
events) and the withdrawal review queue with approve / mark-paid / reject
actions, each audit-logged. Non-staff users get 403; guests are redirected to
login. 7 tests (118 total).

Commit: `feat(adminpanel): add operations dashboard and withdrawal queue`.

## 22. Admin user management + configuration center

**User:** "nsxt" (next).

**Agent:** Added user management (search, detail page, freeze/unfreeze,
granular restrictions with removal, audited balance adjustments backed by a
ledger `ADJUSTMENT` transaction) and the configuration center (edit
`PlatformSetting` values as JSON, `ConfigurationVersion` history, recent
changes list, feature-flag toggles). Admin sub-navigation added across all
admin pages. 7 tests (125 total).

Commit: `feat(adminpanel): add user management and configuration center`.

## 23. Provider management + emergency kill switches

**User:** "NEXT".

**Agent:** Added the providers admin page: per-provider enable/disable for CPA,
survey, payment and ad providers; manual offer/survey sync actions (graceful
error reporting when an adapter is unavailable); and platform-wide emergency
switches (`GAMES_ENABLED`, `OFFERS_ENABLED`, `SURVEYS_ENABLED`,
`DEPOSITS_ENABLED`, `WITHDRAWALS_ENABLED`) enforced in the services and
catalog views, all audit-logged. 7 tests (132 total).

Commit: `feat(adminpanel): add provider management and emergency kill switches`.

## 24. Ad serving

**User:** "NEXT".

**Agent:** Implemented ad serving per ADR-013 (house/direct first): weighted
rotation across eligible campaigns, frequency caps (per hour, per day, minimum
interval), impression recording, click tracking with redirect at
`/ads/click/<impression>/`, an ad-slot partial rendered on the dashboard and
games pages, and `manage.py seed_ad_placements` (8 standard placements).
Ad clicks are never rewarded. 7 tests (139 total).

Commit: `feat(advertising): add ad serving with rotation and frequency caps`.

## 25. KYC flow

**User:** "NEXT".

**Agent:** Added the KYC flow: user page at `/kyc/` (basic level with name/DOB,
full level with private document/selfie uploads, resubmission rules while
under review) and the staff review queue at `/admin-panel/kyc/` with
approve/reject + audit logging. 7 tests (146 total).

Commit: `feat(kyc): add user KYC submission and admin review`.

## 26. CSV reports

**User:** "NEXT".

**Agent:** Added CSV report generation (`apps/reports/services.py` +
Celery-safe `run_report_job` task) for users, financial/rewards, withdrawals
and offer conversions, with the admin page `/admin-panel/reports/` (generate
+ download, 24-hour expiry) and audit logging. 4 tests (150 total).

Commit: `feat(reports): add CSV report generation and admin reports page`.

## 27. Urdu / i18n + RTL

**User:** "NEXTNEXT".

**Agent:** Added internationalization: language switcher in the header,
Urdu (`ur`) catalogue for navigation and dashboard strings, automatic
`dir="rtl"` with RTL font/spacing adjustments, and a pure-Python `.po`→`.mo`
compiler (`scripts/compile_messages.py`) so translations build on machines
without gettext (the first version had wrong offsets — caught and fixed by
comparing against Python's `gettext` module). 3 tests (153 total).

Commit: `feat(i18n): add Urdu translations, language switcher and RTL support`.

## 28. Offer click-through + survey start

**User:** "next".

**Agent:** Completed the user-facing earning actions: the offers page now has
a Start button that runs eligibility, records an `OfferClick`, and redirects
to the provider tracking URL tagged with the click id as `subid` (adapter
tracking with graceful fallback); the surveys page has Start, which creates a
`SurveySession` and redirects to the provider URL (graceful error when no
provider link exists). 5 tests (158 total).

Commit: `feat(offers,surveys): add click-through and survey start actions`.

## 29. Local server + direct-ads management

**User:** asked to run the site locally (admin + user) to try it, then "next".

**Agent:**

- Started the dev server; discovered **port 8000 is occupied by a different
  Django project** on the machine (sports-betting app) — left it untouched and
  ran ours on `127.0.0.1:8010`. Created demo accounts
  (`demo@example.com / Demo1234!` with Rs 5,000, and staff
  `admin@example.com / Admin1234!`).
- Added remaining-limit visibility (offers: today/lifetime/campaign left +
  reset time, unavailable section with reasons; games: plays left + reward).
  6 tests (164 total). Commit `2207fdc`.
- Added direct-ads management at `/admin-panel/ads/`: create direct/house
  campaigns with image upload, placements, schedule, weight, frequency caps;
  impressions/clicks/CTR stats; pause/activate + audit. 4 tests (168 total).

Commit: `feat(adminpanel): add direct ad campaign management`.

## 30. Network ad snippets

**User:** "next".

**Agent:** Added the network ad snippet capability: staff-authored HTML tags
(AdSense/Adsterra/Monetag) can be pasted into a campaign's `html_snippet` and
render verbatim in placements; saves are audit-logged and network tags handle
their own clicks (no internal click redirect). House/direct image campaigns
unchanged. 1 test (169 total).

Commit: `feat(advertising): render network ad snippets in placements`.

## 31. Multi-network console + CPA onboarding

**User:** asked which CPAs to use, how to provide them, and for a multi-network
system with tabs/functions.

**Agent:** Wrote `docs/integrations/CPA_ONBOARDING.md` (exact questions to ask
each network, what credentials to send, our postback URL, candidate list) and
rebuilt the providers admin into a tabbed multi-network console: overview with
emergency switches, CPA / surveys / payments / ads tabs, inventory counts,
health, enable/disable, connection **Test** (honest errors when adapters or
credentials are missing), manual syncs, and an Add-network form with validated
JSON config. 8 tests (176 total).

Commit: `feat(adminpanel): add multi-network console with tabs and connection tests`.

## 32. More games

**User:** "NEXT".

**Agent:** Added two more original HTML5 games with full documentation and
starter reward rules: **Memory Match** (4×4 pairs, score 100/pair minus
10/extra move) and **Snake** (20×20 grid, keyboard + swipe, 90 seconds).
Both integrate the Game SDK with offline fallback. `seed_reference_game` now
seeds all three games (run against the dev DB). Test updated to require docs
for every bundled game.

Commit: `feat(games): add memory-match and snake to the catalog`.

## 33. Earn hub tabs + full offer rules

**User:** "every tab on our site show different web offers with their rules
and regulations".

**Agent:** Built the tabbed Earn hub at `/earn/` (Games / Offers / Surveys).
Each tab shows its own catalog; every offer now displays the complete campaign
rules (incentivized allowed/not, countries, devices/OS, reinstall, completion
rules, remaining daily/lifetime/campaign limits, min age, expiry) via a shared
partial, plus a new offer detail page at `/offers/<id>/`. Catalog row builders
were centralized (`games.services.catalog_rows`,
`offers.services.catalog_rows`) and reused by the hub and the existing pages.
6 tests (182 total).

Commit: `feat(web): add tabbed earn hub with full offer rules`.

Also verified network terms while researching (recorded in the reply): AdGem's
Terms §11.3 require **prior written consent** for incentivized traffic and
§10.2 pays within 60 days after month end; CPX Research pays from $25 (bank/
PayPal) / $100 (BTC) with no setup fee; BitLabs (Prodege) is net-30; AdGate
Media is now part of Prodege.

## 34. Network catalog + scaffolding (flexibility)

**User:** asked for ten more platforms, a total list of what is required, and
to keep the project flexible for adding more later.

**Agent:** Wrote `docs/integrations/NETWORK_CATALOG.md`: 34 catalogued
platforms (13 offerwalls/installs, 6 surveys, 7 CPA/lead-gen, 8 ad networks)
with verified/candidate status, the six credential values needed per network
and the exact "add a network" workflow. Added
`manage.py scaffold_provider <kind> <code> [--name] [--dry-run]` which
generates a full adapter stub (CPA / survey / payment) with TODO markers,
never overwrites an existing file, and prints the adapter path to paste into
the admin. 6 tests (188 total).

Commit: `feat(adminpanel): add network catalog and provider scaffolding command`.

## 35. Public pages (provider review readiness)

**User:** reported that AdGem asks for a website URL and no domain is bought
yet.

**Agent:** Built the public pages reviewers look for: a landing page at `/`
(how it works, ways to earn, clear-rules section; authenticated users redirect
to `/dashboard/`), CMS-driven pages at `/p/<slug>/` (about, terms, privacy,
contact, FAQ) with footer links everywhere, and `manage.py seed_cms_pages`
(starter content with bracketed placeholders flagged for replacement).
Existing tests updated for the new `/dashboard/` route. 6 tests (194 total).

Commit: `feat(cms): add public landing and policy pages`.

## 36. Free deployment path

**User:** "not we can give free from any" — they want a free URL for AdGem,
no paid domain.

**Agent:** Added free deployment options: `render.yaml` (Render blueprint:
Docker service, production settings, generated SECRET_KEY, SQLite, auto-seeded
content, health check), `docker/start.sh` container entrypoint (migrate →
collectstatic → seed → gunicorn), `scripts/public-tunnel.ps1` (instant
temporary public URL via cloudflared) and production settings that run without
Redis and auto-trust Render's hostname. Deployment docs rewritten with the
three free options. 194 tests still green.

Commit: `chore(deploy): add free deployment path (Render blueprint and tunnel script)`.

## 37. Own-server deployment (no PaaS dependency)

**User:** "but we dont have to dependent on render as project finished" — they
want full independence once the project is done.

**Agent:** Added the own-server production stack: `docker-compose.prod.yml`
(PostgreSQL, Redis, web, Celery worker + beat, **Caddy with automatic
Let's Encrypt HTTPS**), `docker/Caddyfile` (static/media + reverse proxy),
`DOMAIN`/`POSTGRES_*` keys in `.env.example`, and `docs/deployment/VPS.md`
with the full walkthrough (VPS, Docker install, DNS, deploy, createsuperuser,
daily pg_dump backup cron, update flow, hardening, and the checklist for
switching providers from a temporary URL to the real domain). 194 tests green.

Commit: `chore(deploy): add own-server production stack (Caddy + VPS guide)`.

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
