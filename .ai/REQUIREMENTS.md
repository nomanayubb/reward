# REQUIREMENTS TRACEABILITY

Maps the master PRD/DRD (see `docs/PRD.md`, `docs/DRD.md`) to implementation
status. Update this file whenever a requirement area changes state.

Legend: ✅ done · 🟡 partial · ⬜ not started

Updated: 2026-09-18

## Core platform

| # | Requirement | Status | Evidence / gap |
| --- | --- | --- | --- |
| 1 | Modular monolith, configurable admin | 🟡 | 26 apps + service layer + PlatformSetting; admin UI missing |
| 2 | Email auth, Argon2, 2FA-ready | 🟡 | Auth API done; 2FA flow not built |
| 3 | Wallet: multiple ledgers | ✅ | 7 account types, system wallet |
| 4 | Immutable ledger, reversals, locking | ✅ | `apps/ledger` + tests |
| 5 | Configurable reward engine | ✅ | `RewardRule` + `RewardService` |
| 6 | Points + cash + hybrid | ✅ | Points ledger + modes |
| 7 | RBAC + audit log | 🟡 | Models + Django admin; UI/role seeding pending |
| 8 | Runtime settings + versioning | ✅ | `PlatformSetting`, `ConfigurationVersion` |
| 9 | Feature flags | ✅ | `FeatureFlag` model |

## Earning activities

| # | Requirement | Status | Evidence / gap |
| --- | --- | --- | --- |
| 10 | HTML5 games: isolated, SDK, anti-cheat | 🟡 | Models + server validation; SDK, wrapper, first game missing |
| 11 | Game reward rules (score/time/cooldown/caps) | ✅ | `GameRewardRule` + `end_session` |
| 12 | Surveys: provider abstraction | 🟡 | Interface + models + completion flow; real adapter missing |
| 13 | CPA/offers: unified Offer API | 🟡 | Models, postbacks, eligibility, quotas; real adapters missing |
| 14 | Offer compliance flags (incentive/geo/device) | ✅ | Stored + enforced by eligibility engine |
| 15 | Campaign quotas + auto throttling | ✅ | `CampaignQuota` + resume task |
| 16 | Postback idempotency | ✅ | Unique (provider, external_conversion_id) + tests |
| 17 | Ads: providers/placements/rotation | ⬜ | Models only; no serving, no network |
| 18 | Referrals | 🟡 | Models + service; conversion hooks partial |
| 19 | Bonuses + streaks | 🟡 | Models; engine wiring partial |
| 20 | VIP/tiers | 🟡 | Tier field; multipliers not wired |

## Money movement

| # | Requirement | Status | Evidence / gap |
| --- | --- | --- | --- |
| 21 | Deposits with state machine | 🟡 | Service + states; real payment adapter missing |
| 22 | Withdrawals with reserve/review/pay | ✅ | Service + states + tests |
| 23 | NOWPayments adapter | ⬜ | Interface only; needs credentials |
| 24 | EasyPaisa adapter | ⬜ | Interface only; verify merchant/API availability |
| 25 | Reconciliation | ⬜ | Planned (P4) |
| 26 | Payment proof + reference | 🟡 | Fields exist; admin UI pending |
| 27 | Payout modes auto/manual/hybrid | ✅ | Resolved at request time |

## Trust & safety

| # | Requirement | Status | Evidence / gap |
| --- | --- | --- | --- |
| 28 | Fraud events + risk score 0-100 | ✅ | `FraudEvent`, `RiskScore`, scoring service |
| 29 | Automated risk actions/restrictions | ✅ | `RiskRule` + granular restrictions |
| 30 | Device/IP reuse + rapid conversion sweep | ✅ | Celery task |
| 31 | IP reputation (VPN/proxy/TOR) | ⬜ | Hook only (`check_ip_risk`) |
| 32 | Velocity checks (deposits/withdrawals) | ⬜ | Planned |
| 33 | KYC | 🟡 | Model + threshold check; flow/UI pending |
| 34 | AML/transaction monitoring | ⬜ | Requires legal review + rules |

## Experience

| # | Requirement | Status | Evidence / gap |
| --- | --- | --- | --- |
| 35 | User REST API | 🟡 | Auth done; wallet/offers/withdrawals/notifications pending |
| 36 | Frontend pages (home/earn/wallet/withdraw) | ⬜ | Templates not built |
| 37 | Activity history + filters | ⬜ | Data exists; endpoints/UI missing |
| 38 | Notifications (in-app/email/SMS) | 🟡 | In-app + email service; SMS gateway pending |
| 39 | Automation trigger/condition/action | ✅ | Engine + executions |
| 40 | CMS + blog + versioned terms | 🟡 | Models only |
| 41 | SEO config + sitemaps | 🟡 | Model only; views/sitemap missing |
| 42 | Reports/exports | ⬜ | Model only |
| 43 | Urdu/i18n + RTL | ⬜ | Settings ready; no translations/layout |

## Operations

| # | Requirement | Status | Evidence / gap |
| --- | --- | --- | --- |
| 44 | Docker + Nginx + Gunicorn | ✅ | `Dockerfile`, `docker-compose.yml`, `nginx/` |
| 45 | Celery beat jobs | ✅ | 7 scheduled tasks |
| 46 | CI | ✅ | GitHub Actions (check, migrations, tests) |
| 47 | Monitoring/alerting | ⬜ | Planned |
| 48 | Backups + restore drill | ⬜ | Planned |
| 49 | Load testing | ⬜ | Planned |
| 50 | Security audit (OWASP) | ⬜ | Planned |

## Integration status (explicit)

| Integration | Status | Notes |
| --- | --- | --- |
| CPA network | **none selected** | Adapter interface + postback endpoint exist. Choice is a config decision (DB row + `.env` keys), not code. Candidates to evaluate: AdGate Media, OfferToro, AdGem, CPALead, CPAGrip, BitLabs, Timewall, Monlix, AyetStudios. Verify per-campaign: incentivized traffic, PK geo, device rules. |
| Survey provider | **none selected** | Candidates: CPX Research, BitLabs, Pollfish, AyetStudios. Verify PK traffic + incentive policy. |
| NOWPayments | not connected | Needs API key + IPN secret |
| EasyPaisa | not connected | Verify merchant/API availability first |
| Ads | none | House/direct first (ADR-013) |
| SMS gateway | none | `SMSLog` records only |

## Decision needed from product owner

1. Pick first CPA network + survey provider (from the candidate list above).
2. Confirm EasyPaisa merchant/API access (or choose another local method).
3. Confirm KYC threshold policy and provider (manual review vs vendor).
4. Confirm ad strategy timing (house ads first per ADR-013).

## Product owner decisions received

- **Currency: PKR-first** (ADR-015). User rewards paid directly in PKR;
  dual wallets (PKR primary, USD for crypto); points engine kept but disabled
  by default; USD revenue converted at an admin-set rate stored per
  transaction. All limits/fees in PKR.
