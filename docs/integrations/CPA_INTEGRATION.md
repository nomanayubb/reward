# CPA / Offerwall Integration

Every CPA network is integrated through an **adapter** that translates provider
data into the platform's normalized format. Core code never branches on
provider names.

## 1. Adapter interface

`apps/cpa/providers/base.py`:

```python
class CPAProviderAdapter(ABC):
    def get_offers(self) -> list[NormalizedOffer]: ...
    def track_click(self, offer, user, click_id, request=None) -> str: ...
    def process_postback(self, payload, headers=None) -> NormalizedConversion: ...
    def validate_signature(self, payload, headers=None) -> bool: ...
    def validate_conversion(self, conversion) -> bool: ...
    def get_campaign_status(self, offer) -> dict: ...
    def get_reporting_data(self, since=None, until=None) -> list[dict]: ...
```

Not every network supports every method; unsupported methods may raise
`NotImplementedError` and the caller degrades gracefully.

## 2. Normalized types

`NormalizedOffer`: external_id, title, payout, description, category,
tracking_url, countries, devices, operating_systems, incentive_allowed,
multiple_completion_allowed, reinstall_allowed, vpn_allowed, daily_user_limit,
lifetime_user_limit, expires_at, raw.

`NormalizedConversion`: external_conversion_id, user_identifier (click id /
subid), payout, status (`approved`/`rejected`), offer_external_id, reason, raw.

## 3. Registering a network

1. Create `apps/cpa/providers/<network>.py` implementing the adapter.
2. Add credentials to `.env` (`CPA_PROVIDER_X_KEY` / `_SECRET`).
3. Create a `CPAProvider` row: code, name, `adapter_path`
   (e.g. `apps.cpa.providers.network_a.NetworkAAdapter`), capabilities,
   priority, `is_enabled=False` until tested.
4. Run `sync_offers` and verify offers import with correct compliance flags.
5. Send test postbacks from the network sandbox and confirm rewards.
6. Enable the provider and monitor health.

## 4. Click tracking

```
User clicks offer
  → platform creates OfferClick (unique click_id)
  → adapter.track_click() builds the provider URL (subid = click_id)
  → user completes the offer on the provider side
  → provider calls our postback with the same subid
```

## 5. Postback contract

Endpoint: `POST /api/v1/postbacks/<provider_code>/`

Processing order (all in `apps/offers/services.process_postback`):

1. Store raw payload + headers (`OfferPostback`).
2. `adapter.validate_signature()` — reject on failure.
3. `adapter.process_postback()` → `NormalizedConversion`.
4. Duplicate check on (`provider`, `external_conversion_id`) — replays return
   the original conversion, `created=False`.
5. Resolve user + offer via `click_id`.
6. Re-run `evaluate_offer()` (eligibility/compliance/limits).
7. `RewardService.award(...)` (idempotent on the conversion id).
8. Bump `CampaignQuota` counters; auto-pause at cap.
9. Emit `OFFER_CONVERTED` for automation.

Response: `{"ok": true, "duplicate": bool, "conversion_id": ..., "status": ...}`.

## 6. Postback security

- Signature/HMAC validation with the provider secret (constant-time compare).
- IP allow-list where the provider publishes ranges.
- Timestamp freshness window (reject stale/replayed callbacks).
- Idempotency: database unique constraint, not just application checks.
- Raw payload retention for provider disputes.
- Rate limiting per provider.
- Rejected conversions are stored with a reason — never silently dropped.

## 7. Quotas and throttling

`CampaignQuota` per offer:

| Field | Effect |
| --- | --- |
| `daily_global_cap` | offer pauses (`PAUSED_BY_QUOTA`) at the cap |
| `hourly_cap` | hourly conversion ceiling |
| `daily_user_cap` | per-user daily completions |
| `lifetime_user_cap` | per-user lifetime completions |
| `country_cap` | JSON map, e.g. `{"PK": 100}` |

Counters reset hourly/daily by
`apps.offers.tasks.recalculate_campaign_quotas`, which also resumes offers
whose caps have freed up.

## 8. Reversals and reconciliation

- Provider reversal → `RewardService.reverse()` on the linked reward; original
  conversion and ledger history stay intact.
- Daily reconciliation compares our conversions against provider reports to
  find missing, duplicate or reversed conversions and payout mismatches.
- Discrepancies open a `RewardDispute` / admin alert rather than silent edits.

## 9. Compliance rules (non-negotiable)

- `incentive_allowed = False` ⇒ offer is never shown in the rewards section.
- Country/device/OS restrictions are enforced by the eligibility engine.
- Reinstall and multiple-completion rules come from the campaign.
- Never assume "the network pays $X so we can reward $Y" — the campaign terms
  decide what is permitted, and the platform stores them as data.
