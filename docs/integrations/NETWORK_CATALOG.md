# Network Catalog — all platforms we can plug in

Status legend: **verified** = I read their own site/terms; **candidate** = to
be verified before signing.

## 1. Offerwalls & app installs (incentivized)

| # | Network | Status | Notes (verified where marked) |
| --- | --- | --- | --- |
| 1 | **AdGem** | verified | T&C: incentivized traffic needs **prior written consent**; pays within **60 days** after month end; 1B+ conversions claimed |
| 2 | **AdGate Media** | verified | Now part of **Prodege** (press release); legacy dashboard at prodegeads.com |
| 3 | **OfferToro (Torox)** | verified | Global offerwall, direct traffic, large advertiser partners |
| 4 | **Adscend Media** | candidate | Long-established offerwall/content locker |
| 5 | **Lootably** | candidate | Built for rewards/GPT platforms |
| 6 | **RevU** | candidate | Widely used on GPT sites |
| 7 | **AyetStudios** | candidate | Surveys + offers, popular in reward apps |
| 8 | **Notik** | candidate | Purpose-built for reward platforms |
| 9 | **GemiAds** | candidate | Surveys + offers, smaller publishers accepted |
| 10 | **Wannads** | candidate | Smaller, easier approval, low minimums |
| 11 | **Monlix** | candidate | Newer offerwall |
| 12 | **Timewall** | candidate | Newer offerwall, low minimums |
| 13 | **Tapjoy** | candidate | Giant in mobile rewarded (usually app-to-app) |

## 2. Surveys

| # | Network | Status | Notes |
| --- | --- | --- | --- |
| 14 | **CPX Research** | verified | Make Opinion GmbH (Berlin); no setup fee; min $25 bank/PayPal, $100 BTC; 105+ countries; 100K+ daily surveys |
| 15 | **BitLabs** | verified | Prodege company; **net-30**; clients incl. Freecash, Prime Opinion |
| 16 | **Pollfish** | verified | Prodege company; first-party panel; researcher-side platform |
| 17 | **TheoremReach** | candidate | Survey wall for reward apps |
| 18 | **PureSpectrum** | candidate | Large quality-focused survey marketplace |
| 19 | **Cint (Lucid)** | candidate | One of the largest survey exchanges; usually needs volume |

## 3. CPA / lead-gen

| # | Network | Status | Notes |
| --- | --- | --- | --- |
| 20 | **CPAGrip** | candidate | Weekly payouts, easy approval, leads/signups |
| 21 | **CPALead** | candidate | Weekly payouts, content locking |
| 22 | **MyLead** | candidate | Global CPA, low minimums |
| 23 | **AdWork Media** | candidate | Content locker + offers |
| 24 | **Zeydoo** | candidate | CPA (sweepstakes/leads), accepts small publishers |
| 25 | **TerraLeads** | candidate | Weekly payouts, low minimums |
| 26 | **Gasmobi** | candidate | Incentivized installs |

## 4. Ad networks (banners / popunders / interstitials)

| # | Network | Status | Notes |
| --- | --- | --- | --- |
| 27 | **Adsterra** | candidate | Weekly payouts, accepts new publishers |
| 28 | **Monetag** | candidate | Popunder/interstitial focus |
| 29 | **HilltopAds** | candidate | Popunder/video |
| 30 | **Clickadu** | candidate | Popunder/video |
| 31 | **Evadav** | candidate | Push/popunder |
| 32 | **Galaksion** | candidate | Popunder |
| 33 | **Adcash** | candidate | Popunder + banners |
| 34 | **PropellerAds** | candidate | Large network, accepts small publishers |

**Total catalogued: 34 platforms** (13 offerwalls · 6 survey · 7 CPA · 8 ad
networks). Google AdSense remains content-pages-only (ADR-013).

## What I need from you per network (6 values)

| # | Value | Where it goes |
| --- | --- | --- |
| 1 | Network code (e.g. `adgem`) | provider row |
| 2 | Display name | provider row |
| 3 | API key / token | `.env` |
| 4 | Postback secret / signature key | `.env` |
| 5 | Affiliate / publisher ID | `.env` or provider config |
| 6 | Sample postback payload (+ feed URL if any) | adapter code + tests |

**To start we need 3 networks → 18 values.** Give them to me in one message
per network and I build the adapter the same day.

Our callback URL to give each network:
`https://<your-domain>/api/v1/postbacks/<network_code>/`

## How a new network is added (already flexible)

1. Scaffold the adapter (10 seconds):
   ```bash
   python manage.py scaffold_provider cpa adgem --name "AdGem"
   ```
   → writes `apps/cpa/providers/adgem.py` with the full interface and TODOs.
2. Fill the parsing/signature methods using the network's docs + sample payload.
3. Add credentials to `.env` (+ `.env.example` keys).
4. Admin → **Networks → CPA networks → Add network** (code, name, adapter
   path, JSON config) → **Test** → **Sync now** → enable.
5. Run `pytest` (adapter tests) and `scripts/project-check`.

Nothing in the reward engine, wallets, ledger, quotas or UI changes — that is
the point of the adapter design (ADR-003).
