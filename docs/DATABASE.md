# Database

PostgreSQL in every real environment (SQLite only for local dev/tests).

## Conventions

- UUID primary keys on business entities (`UUIDTimeStampedModel`).
- `created_at` / `updated_at` on mutable models; `created_at` is indexed.
- Money/points: `NUMERIC(20,8)` via `apps.common.fields.money_field`.
  Nullable money fields default to `NULL` (never silently `0`).
- Immutable tables: `ledger_ledgerentry`, `adminpanel_auditlog`.
- JSONB (`JSONField`) for provider payloads, configs, conditions and
  eligibility context.
- Partial unique constraint example: one reward per
  (`source`, `source_reference`, `user`) where `source_reference <> ''`.

## Tables by module

### accounts
| Table | Key fields |
| --- | --- |
| `accounts_user` | email (unique), username, phone, country, status, is_active, is_staff, is_email_verified, referral_code (unique), date_joined, last_login_ip |

### users
| Table | Key fields |
| --- | --- |
| `users_userprofile` | user 1:1, display_name, avatar, country, language, tier, xp, level |
| `users_usersecurity` | user 1:1, two_factor_enabled/secret, failed_login_attempts, locked_until |
| `users_userdevice` | user FK, device_id_hash, browser/os, last_ip, risk_flags; unique(user, device_id_hash) |
| `users_usersession` | user FK, session_key, device FK, ip, started/last activity, revoked_at |
| `users_userriskprofile` | user 1:1, risk_score, level, signals, review_required |
| `users_userrestriction` | user FK, type, reason, until, is_active |

### wallets
| Table | Key fields |
| --- | --- |
| `wallets_wallet` | user 1:1, currency, is_locked |
| `wallets_walletaccount` | wallet FK, type (cash/points/bonus/pending/locked/withdrawable/deposit), currency, balance, is_frozen; unique(wallet, type, currency) |
| `wallets_balancesnapshot` | account FK, balance, reason, taken_at |

### ledger
| Table | Key fields |
| --- | --- |
| `ledger_ledgertransaction` | type, status, reference, metadata, idempotency_key (unique), reverses 1:1 |
| `ledger_ledgerentry` | transaction FK, account FK, amount (signed), created_at — immutable |

### rewards
| Table | Key fields |
| --- | --- |
| `rewards_rewardrule` | name, priority, source, provider_code, campaign_type, country, user_tier, conditions, mode, user_percentage, fixed_cash/points, points_percentage, multiplier, max_user_reward, requires_manual_approval |
| `rewards_reward` | user, source, source_reference, rule, gross_revenue, platform_share, user_reward, points_reward, status, ledger_transaction |

### payments / deposits / withdrawals
| Table | Key fields |
| --- | --- |
| `payments_paymentprovider` | code (unique), kind, is_enabled, config, fee, health |
| `payments_paymenttransaction` | provider FK, user FK, direction, external_id, amount, status, raw_payload; unique(provider, external_id) |
| `deposits_deposit` | user, provider, amount, currency, status, instructions, expires_at, ledger_transaction |
| `withdrawals_withdrawalmethod` | user, type, details, is_default, is_verified |
| `withdrawals_withdrawal` | user, method, amount, fee, net_amount, status, risk_level, payout_mode, dual-approval fields, reserve/payout/refund transactions |

### games / surveys / offers
| Table | Key fields |
| --- | --- |
| `games_gamecategory` / `games_game` | slug, title, entry_path, status, min_session_seconds, max_daily_sessions |
| `games_gamerewardrule` | game FK, conditions, mode, points/cash, cooldown_hours, daily_max, monthly_max |
| `games_gamesession` | user, game, session_token (unique), status, duration, score, ip, device hash |
| `games_gameevent` | session FK, event_type, payload, server_validated |
| `surveys_surveyprovider` / `surveys_survey` | code, adapter_path, health / external_id, payout, user_reward, caps, status |
| `surveys_surveysession` / `surveys_surveycompletion` | status, timings / external_completion_id unique per provider |
| `cpa_cpaprovider` | code, adapter_path, capabilities, health |
| `offers_offercategory` / `offers_offer` | compliance flags, payout, user_reward, countries/devices/OS, limits, rank_score |
| `offers_campaignquota` | offer 1:1, global/hourly/user/lifetime/country caps + counters |
| `offers_offerclick` | click_id (unique), user, offer, ip, device |
| `offers_offerconversion` | external_conversion_id, payout, user_reward, status, reward FK; unique(provider, external_conversion_id) |
| `offers_offerpostback` | provider, payload, headers, signature_valid, processing_result |

### advertising / bonuses / referrals
| Table | Key fields |
| --- | --- |
| `advertising_adprovider` / `advertising_adcampaign` | kind / ad_type, placements M2M, weight, frequency caps |
| `advertising_adimpression` / `advertising_adclick` | campaign, user, placement |
| `bonuses_bonusrule` / `bonuses_bonus` / `bonuses_bonusclaim` | kind, reward config, streak_days, max claims / status / claimed_at |
| `referrals_referral` | referrer, referred 1:1, code_used, status, fraud_flags |
| `referrals_referralconversion` | referral FK, source, gross/reward amounts, status |

### fraud / risk / kyc
| Table | Key fields |
| --- | --- |
| `fraud_fraudevent` | user, kind, severity, status, evidence, action_taken |
| `risk_riskrule` | conditions, action, score_delta, priority |
| `risk_riskscore` | user, score, reasons, computed_at |
| `kyc_kycverification` | user 1:1, status, level, identity fields, documents, reviewer |

### notifications / automation / analytics / reports
| Table | Key fields |
| --- | --- |
| `notifications_notification` | user, kind, channel, title, is_read, delivery_status |
| `notifications_emailtemplate` | code (unique), subject, bodies |
| `notifications_smslog` | phone, message, provider, status |
| `automation_automationrule` | trigger, conditions, actions, priority, max_executions_per_user |
| `automation_automationexecution` | rule, user, status, event_payload, result |
| `analytics_dailystatistic` | date + key (unique), value, dimension |
| `analytics_analyticsevent` | name, user, payload |
| `reports_reportjob` | kind, format, params, status, file, expires_at |

### cms / seo / support / adminpanel
| Table | Key fields |
| --- | --- |
| `cms_cmspage` + `cms_pageversion` | slug, status / versioned content |
| `cms_blogcategory` / `cms_blogpost` | slug, author, category, status, published_at, SEO fields |
| `seo_seoconfig` | path (unique), title, meta, canonical, robots, OG, schema |
| `support_ticket` / `support_ticketmessage` | category, status, priority / body, is_staff |
| `support_rewarddispute` | source, reference, status, resolution |
| `adminpanel_permission` / `adminpanel_role` | code (unique) / permissions M2M, users M2M |
| `adminpanel_platformsetting` | key (unique), value JSON, group, is_public |
| `adminpanel_configurationversion` | key, old_value, new_value, changed_by |
| `adminpanel_featureflag` | key (unique), is_enabled, rollout_percent |
| `adminpanel_auditlog` | actor, action, object_type/id, old/new value, reason, ip — immutable |

## Indexing

Key indexes already in place: user+status+created_at on transactions, status
filters, provider external ids, campaign/offer lookups, ledger
account+created_at, daily statistics date+key. Add indexes alongside new
query patterns; verify with `EXPLAIN ANALYZE` before large launches.

## Partitioning (future)

When volume grows, partition by month: `ledger_ledgerentry`,
`games_gameevent`, `advertising_adimpression`, `offers_offerclick`,
`analytics_analyticsevent`. Move analytics reads to a warehouse rather than
adding load to the transactional database.
