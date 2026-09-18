# AdGem Integration

Status: **adapter implemented and unit-tested**; live access blocked by the
credential type — see "Current blocker" below.

## 1. How AdGem's API works (verified from their docs)

### Offer API (REST)

```
1. Exchange the refresh token for a short-lived access token:
   POST https://offer-api.adgem.com/v1/users/token
   Content-Type: application/x-www-form-urlencoded
   grant_type=refresh_token&refresh_token=<REFRESH_TOKEN>
   -> {"access_token": "...", "expires_in": 3600}

2. Fetch offers:
   GET https://offer-api.adgem.com/v1/offers
   Authorization: Bearer <access_token>
```

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
ADGEM_REFRESH_TOKEN=   # dashboard → Properties & Apps (Offer API refresh token)
ADGEM_API_KEY=         # optional alias for the same value
ADGEM_POSTBACK_KEY=    # Postback Options → generate key (shown once)
ADGEM_API_BASE=https://offer-api.adgem.com
```

## 3. Current blocker (checked live)

Calling the token endpoint with the credential provided so far returns:

```
HTTP 401 {"error":"Unauthenticated."}
```

That means the value is not an Offer-API **refresh token** (or the app is not
active yet). Ask your AdGem Publisher Support Advocate, in one message:

1. "Please confirm my app is approved/active."
2. "Please issue an **Offer API refresh token** for app `<app id>` (dashboard →
   Properties & Apps), or tell me exactly where to copy it."
3. "Please enable **Server Postback** and give me the **Postback Key** and your
   **static postback IP** for whitelisting."
4. "Please confirm in writing that **incentivized traffic is allowed** for my
   account (T&C §11.3) — required before I can show your offers."

When the correct refresh token arrives: put it in `.env`, run
`/admin-panel/providers/?tab=cpa` → **Test** → **Sync now**. The adapter is
already tested against their documented payloads.

## 4. Compliance notes

- Incentivized traffic requires **prior written consent** (T&C §11.3). The
  adapter imports offers with `incentive_allowed = false` until you set
  `incentive_allowed: true` in the provider config (do that only after the
  written confirmation).
- Payments: within **60 days after the end of each calendar month** (T&C
  §10.2); disputes must be raised within 14 days.
- Never reward a user for an `install` postback — only payable `reward`
  conversions.
