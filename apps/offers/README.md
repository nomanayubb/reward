# CPA Offers & Offerwall (`apps/offers`)

## Purpose
Owns the offer catalog, compliance flags, campaign quotas, click tracking,
conversion ingestion and the eligibility engine.

## Module contract
- **Inputs:** provider offer feeds (via `apps.cpa` adapters), user clicks,
  provider postbacks.
- **Outputs:** `Offer`, `CampaignQuota`, `OfferClick`, `OfferConversion`,
  `OfferPostback` rows; reward creation via `RewardService`.
- **Dependencies:** `apps.cpa`, `apps.rewards`, `apps.wallets`, `apps.fraud`,
  `apps.automation`.
- **Events emitted:** `OFFER_CONVERTED`.
- **Events consumed:** none.
- **Database tables:** `OfferCategory`, `Offer`, `CampaignQuota`, `OfferClick`,
  `OfferConversion`, `OfferPostback`.
- **Public APIs:** `/api/v1/offers/`,
  `/api/v1/postbacks/<provider_code>/`.
- **Security requirements:** postbacks signature-verified; raw payload stored;
  conversions idempotent.

## Business rules
- `incentive_allowed = False` ⇒ offer never shown in the rewards section.
- Eligibility engine returns ELIGIBLE / NOT_ELIGIBLE / REQUIRES_REVIEW with
  reasons (country, device, OS, compliance, quotas, user limits, risk).
- Quotas auto-pause offers (`PAUSED_BY_QUOTA`) and auto-resume on reset.
- Duplicate postbacks return the original conversion and never pay twice.
- Reversals compensate via `RewardService.reverse()`; history stays intact.

## Key functions
- `services.record_click(...)`, `services.get_click_url(...)`
- `services.process_postback(provider, payload, headers, ip)`
- `services.bump_quota(offer, country)`
- `eligibility.evaluate_offer(user, offer, context)`

## Tests
`pytest tests/test_critical_flows.py -q` (idempotency); extend with quota and
eligibility tests when adapters are added.
