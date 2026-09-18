# AdGem Integration

Status: **property created (App ID 33592, pending AdGem approval)**.
Postback chain **verified end-to-end** locally with the real Postback Key:
signed v3 postback accepted → reward 224 PKR (40% of $2 × 280) credited →
replay detected as duplicate → tampered signature rejected.

| Path | Credential needed | Status |
| --- | --- | --- |
| Web Offerwall (pre-built iframe) | **App ID** ✅ have it | live in the generic hub `/offers/offerwall/` → `/offers/offerwall/adgem/`; shows offers after AdGem approves |
| Native offers (Offer API / Prism) | Offer API refresh token / Prism JWT | adapter built + tested; credential pending AdGem support |
| Reporting + reconciliation | dashboard API token | **working live** (`manage.py reconcile_provider adgem`) |

Secrets (App ID, Postback Key) live in `.env` / host environment variables —
never in this repository.

## Compliance switch (do this before launch)

The provider config ships with `incentive_allowed: false`, so offerwall
conversions are stored but **not paid** until AdGem confirms incentivized
traffic in writing (T&C §11.3). Once your affiliate manager confirms:

1. `/admin-panel/providers/?tab=cpa` → AdGem → config
2. set `"incentive_allowed": true`
3. keep the confirmation email on file.

## 1. How AdGem's API works (verified from their docs)

### Web Offerwall (fastest path — needs only the App ID)

```
Direct link: https://api.adgem.com/v1/wall?appid=<APP_ID>&playerid=<PLAYER_ID>
iFrame:      <iframe src="https://api.adgem.com/v1/wall?appid=<APP_ID>&playerid=<PLAYER_ID>">
```

- Create the property in **Properties & Apps** (platform: Desktop/Web) and wait
  for approval; AdGem shows no offers until the app is approved.
- `playerid` must be **lowercase, alphanumeric + hyphens/underscores, ≤255
  characters, constant per user**. We use `u<uuid-hex>` (`player_id_for(user)`)
  and reverse it on postbacks (`user_for_player_id`).
- Rewards arrive through the same signed v3 postback; the platform auto-creates
  the offer record from the postback data and pays via the reward engine.
- Optional parameters we can add later: `limit`, `device`, `ip`, `useragent`,
  `os_version`, `platform`, `placement`, `c1`-`c5`.

### Reporting API (reconciliation)

```
GET https://dashboard.adgem.com/v1/report
Authorization: Bearer <dashboard API token>   (generate in the dashboard)
group_by[]=app_id&group_by[]=date&date_range[start_date]=Y-m-d H:i:s&...
```

Fields available: `app_id`, `app_name`, `date`, `country_name`,
`platform_name`, `campaign_name`, `dau`, `payout`, `offerwall_loads`,
`gross_clicks`, `distinct_clicks`, `conversions`, `ctr`, `cr`, `ecpm`.

Note: Cloudflare fronts `dashboard.adgem.com` and blocks unknown client
signatures — the adapter sends a normal User-Agent header for this reason.

### Offer API (REST) and Prism (GraphQL) — native UI

Both use the same OAuth 2.0 exchange, on different hosts:

```
# REST Offer API
POST https://offer-api.adgem.com/v1/users/token   (form: grant_type=refresh_token&refresh_token=…)
GET  https://offer-api.adgem.com/v1/offers        (Authorization: Bearer <access_token>)

# Prism (GraphQL)
POST https://prism.adgem.com/v1/users/token       (same form)
POST https://prism.adgem.com/v1/offers            (Bearer; JSON body: {query, variables})
```

**Critical:** the `refresh_token` is **"provided by the AdGem Team"** (their
Prism docs) — it is *not* self-generated in the dashboard. Only AdGem support
can issue it, and only after your app is approved. That is why the credentials
tried so far returned 401 (`"scopes":[]`).

Our adapter supports both: set the provider config key
`"mode": "prism"` to use GraphQL (default is `"rest"`). Prism offer mapping is
deliberately minimal until real credentials allow testing the full schema.

- Access tokens live ~1 hour; the adapter caches them and re-exchanges shortly
  before expiry, and clears the cache on any 401.
- Poll no more than ~once every 5 minutes (the platform syncs every 15).
- Offer fields we map: `total_payout_usd` → payout, `creatives.*` → title /
  description / icon / instructions, `links.click_url` (contains a
  `{playerid}` placeholder we replace with our click id), `geo_targeting`,
  `device_targeting`, `os_targeting`, `is_multi_reward`.

### Postbacks v3 (POST, signed)

```
POST https://<your-domain>/api/v1/postbacks/adgem/
Signature: HMAC-SHA256(raw request body, POSTBACK_KEY)   (hex)
```

Body shape:

```json
{
  "request_id": "…", "timestamp": 1720727170,
  "data": {
    "conversion_id": "c5eb2a9d-…",
    "player_id": "…",            // our click id, sent as {playerid}
    "payout": 1.5,
    "offer_id": "123…",
    "conversion_type": "reward", // "install" is tracking-only
    "country": "PK", "ip": "…", "gaid": "…", "idfa": "…",
    "goal_name": "Reach level 20", "tracking_type": "CPA"
  }
}
```

Our adapter only credits `conversion_type = "reward"`; install postbacks are
stored as rejected (tracking only). Idempotency is enforced on
`(provider, conversion_id)`.

AdGem also recommends **IP whitelisting** — ask their support for their
static postback IP and allow it in your firewall/proxy.

## 2. Environment keys

```
ADGEM_APP_ID=          # Properties & Apps → app id (Web Offerwall)
ADGEM_POSTBACK_KEY=    # Postback Options → generate key (shown once)
ADGEM_REPORT_TOKEN=    # dashboard API token (Reporting API / reconciliation)
ADGEM_API_KEY=         # alias accepted for the report token
ADGEM_REFRESH_TOKEN=   # Offer API refresh token (native offers only)
ADGEM_API_BASE=https://offer-api.adgem.com
```

## 3. Reconciliation

```bash
python manage.py reconcile_provider adgem --days 7
```

Outputs reported vs. local conversions and payout, and flags mismatches. Run it
daily; raise disputes within AdGem's 14-day window (T&C §10.3).

Verified live: the reporting API accepted the dashboard token and the command
ran end-to-end (0 conversions so far — no traffic yet).

## 4. Current blocker (checked live)

| Endpoint | Auth | Result |
| --- | --- | --- |
| `dashboard.adgem.com/v1/report` | dashboard Bearer token | ✅ **works** |
| `offer-api.adgem.com/v1/users/token` | refresh-token exchange | `401 Unauthenticated` (token is not an Offer-API refresh token) |
| `prism.adgem.com/v1/offers` | JWT bearer | `401 Unauthorized` (JWT carries `"scopes":[]`) |

So the dashboard token is valid for reporting. To start earning you need:

1. **App ID** (Properties & Apps) → set `ADGEM_APP_ID` → the Web Offerwall goes
   live immediately at `/offers/offerwall/adgem/` (once AdGem approves the app).
2. **Postback Key** (Postback Options → generate; shown once) → set
   `ADGEM_POSTBACK_KEY` → rewards from the offerwall start crediting.
3. **Offer API refresh token** only if you later want offers listed natively
   inside our own UI.

Ask your Publisher Support Advocate, in one message:

1. "Please confirm my app is approved/active." (dashboard → Properties & Apps)
2. "Please give me the **App ID** for the Web Offerwall property."
3. "Please enable **Server Postback** and give me the **Postback Key** and your
   **static postback IP** for whitelisting."
4. "Please confirm in writing that **incentivized traffic is allowed** for my
   account (T&C §11.3) — required before I can show your offers."

Then set `incentive_allowed: true` in the provider config in
`/admin-panel/providers/?tab=cpa` so imported offerwall offers can pay.

## 5. Compliance notes

- Incentivized traffic requires **prior written consent** (T&C §11.3). The
  adapter imports offers with `incentive_allowed = false` until you set
  `incentive_allowed: true` in the provider config (do that only after the
  written confirmation).
- Payments: within **60 days after the end of each calendar month** (T&C
  §10.2); disputes must be raised within 14 days.
- Never reward a user for an `install` postback — only payable `reward`
  conversions.
