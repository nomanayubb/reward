# CPA / Survey Network Onboarding — what to get and what to send

This is the checklist for adding a real network. You do the signup (business
verification); the platform only needs the values below.

## 1. Sign up (you)

1. Register as a **publisher/affiliate** (not advertiser) on the network.
2. Complete their KYC/business verification.
3. Ask their affiliate manager these exact questions:
   - "Do you allow **incentivized** traffic for app-install offers?"
   - "Do you accept **Pakistan** traffic? Which offers are available for PK?"
   - "Do you support **S2S postback** (server-to-server) with a `subid`?"
   - "What is the **payout** for app installs in Pakistan (incentivized)?"
   - "What is the **payment schedule and minimum**?" (weekly? net-15? $50?)
   - "What are the **per-user caps** (installs per day, per lifetime)?"
   - "Which **app stores/OS** are supported (Android/iOS)?"

## 2. What to send me per network

| Item | Example | Where it goes |
| --- | --- | --- |
| Network code | `adgem` | provider `code` |
| Display name | AdGem | provider `name` |
| **API key / token** | `abc123...` | `.env` (e.g. `CPA_ADGEM_API_KEY`) |
| **Postback secret** (signature key) | `secret...` | `.env` (`CPA_ADGEM_SECRET`) |
| Affiliate/publisher ID | `12345` | `.env` or provider `config` |
| Offer feed API URL (if any) | `https://api.network.com/v1/offers` | provider `config.feed_url` |
| Postback URL format they provide | `https://net.com/postback?subid={subid}&...` | adapter code |
| Sample postback payload | JSON they send you | adapter code + tests |
| Countries/devices they allow for PK | `PK`, `Android` | provider `config` / offer data |

**If the network has no API**, they still usually provide:
- a **postback URL template** (with `subid` placeholder) → we pass our click id as `subid`
- a **report CSV** for reconciliation

That is enough to build the adapter — we do not need their login.

## 3. Our postback endpoint (give this to the network)

```
https://<your-domain>/api/v1/postbacks/<network_code>/
```

We will:
- verify the signature with the secret you provide
- match the conversion to a user via the `subid` we sent on click
- credit the reward exactly once (idempotent)
- store the raw payload for disputes

## 4. Candidate networks to apply to (verify each)

| Network | Type | Notes to verify |
| --- | --- | --- |
| AdGate Media | Offerwall, app installs | incentivized allowed on flagged campaigns; PK coverage varies |
| OfferToro | Offerwall | incentivized allowed; check PK offers |
| AdGem | Offerwall | incentivized allowed; PK coverage |
| Adscend Media | Offerwall | incentivized allowed; check PK |
| Wannads | Offerwall | smaller; low minimums |
| Monlix / Timewall | Offerwall | newer; check PK + payment terms |
| CPAGrip / CPALead | Leads/signups | not installs; weekly payouts |
| CPX Research / BitLabs | Surveys | high PK fill for surveys |

Rules that keep your account alive (non-negotiable):
- never fake installs, never use emulators/VPNs on offers
- one account per device/person
- respect `incentive_allowed`, country, device and caps exactly as stored in the platform
- keep reversal rate low; reversals are what kill accounts

## 5. What I build once you send the values

1. `apps/cpa/providers/<network>.py` adapter (feed parsing, signature, postback parsing)
2. `.env.example` keys + provider row defaults
3. Unit tests with the sample payloads you received
4. Admin: enable the network, sync offers, test postback from their sandbox

Nothing else changes — the reward engine, quotas and compliance engine are
already network-agnostic.
