# Provider setup & migration checklist

Use this every time you add a network and every time you change hosting.
The rule: **credentials live in our `.env`; URLs live in their dashboard.**

## A. When adding a network (first time)

In **our admin** (`/admin-panel/providers/?tab=...`):

1. Add the network: code, name, adapter path, JSON config.
2. Add its secrets to the host environment (`.env` on VPS, or Environment
   Variables on Render):
   - `<CODE>_API_KEY`, `<CODE>_SECRET`, affiliate/publisher ID
3. Press **Test** (honest result) → **Sync now** → verify offers/surveys
   appear → **Enable**.

In **their dashboard**:

| Field | Value |
| --- | --- |
| Website / app URL | your public URL (Render now, domain later) |
| Postback / S2S URL | `https://<your-domain>/api/v1/postbacks/<network_code>/` |
| Postback method | GET or POST — whatever their docs say; our endpoint accepts POST JSON |
| Signature / secret | the same secret you put in our `.env` |
| IP allowlist (if they require one) | your server's **static** IP — Render free has none; use a VPS |

Then send one real test conversion and confirm:
- the conversion appears in our `OfferPostback` records,
- the user's reward goes pending → approved,
- nothing is duplicated if they resend the same postback.

## B. When moving hosting (Render → VPS, or VPS → VPS)

**If the domain does not change** (VPS → VPS): nothing to do in their
dashboards. Copy the `.env` and the database (see `docs/deployment/VPS.md` §8).

**If the domain changes** (Render/tunnel → your domain):

| Order | Action | Why |
| --- | --- | --- |
| 1 | Deploy on the new host and test the full flow | never break live traffic |
| 2 | Update **postback URL** in every network dashboard | dead postback = lost conversions |
| 3 | Update **website URL** in every network account | keeps reviews clean |
| 4 | Email each affiliate manager: new domain | they often need to re-approve |
| 5 | Send a test conversion per network | prove it works |
| 6 | Only then promote the domain to users | free-tier data is disposable |

Keep a copy of every network's dashboard login in your password manager —
you will need it for step 2.

## C. What lives where (never mix these up)

| Item | Location | Changes when hosting changes? |
| --- | --- | --- |
| API keys / secrets | our `.env` / host env vars | yes — re-enter on the new host |
| Affiliate ID | our `.env` or provider config | no |
| Postback URL | their dashboard | only if the domain changes |
| Website URL | their dashboard | only if the domain changes |
| Offer/survey data | our database (synced from them) | no |

## D. Per-network quick notes

- **AdGem** — incentivized traffic requires **prior written consent** (T&C
  §11.3); payments within 60 days after month end (§10.2). Ask for the
  consent email and keep it.
- **CPX Research** — no setup fee; min payout $25 (bank/PayPal) / $100 (BTC);
  they provide a script/iFrame/API integration plus S2S.
- **BitLabs (Prodege)** — net-30; large survey supply.
- **Ad networks** (Adsterra/Monetag/...): paste their snippet into
  `/admin-panel/ads/` (HTML snippet field); no postback needed.

## E. Never do this

- Never set a postback URL pointing at a temporary tunnel URL
  (`*.trycloudflare.com`) — it changes and conversions are lost silently.
- Never put user-supplied content in an ad HTML snippet.
- Never enable an offer whose campaign forbids incentivized traffic.
