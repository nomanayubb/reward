# NOWPayments Integration

Crypto deposits via [NOWPayments](https://nowpayments.io). The adapter is
implemented (`apps/payments/providers/nowpayments.py`) and its IPN signature
verification is unit-tested; **live/sandbox verification is pending because no
credentials exist in the repository**.

## 1. Configure credentials

Set in `.env` (never commit real values):

```
NOWPAYMENTS_API_KEY=...
NOWPAYMENTS_IPN_SECRET=...
NOWPAYMENTS_SANDBOX=True      # keep True until sandbox tests pass
```

## 2. Create the provider row

In the admin (`Payments → Payment providers`):

| Field | Value |
| --- | --- |
| code | `nowpayments` |
| name | NOWPayments |
| kind | crypto |
| is_enabled | off until verified |
| supports_deposits | on |
| config.adapter_path | `apps.payments.providers.nowpayments.NowPaymentsAdapter` |
| config.pay_currency | e.g. `usdttrc20` |
| config.ipn_callback_url | `https://<your-domain>/api/v1/webhooks/nowpayments/` |

## 3. How the flow works

```
POST /api/v1/deposits/ {provider: "nowpayments", amount: "2800"}
  → adapter converts PKR → USD at the admin-set rate (stored in instructions)
  → NOWPayments invoice created; pay_address returned to the user
  → user pays crypto
  → NOWPayments IPN → POST /api/v1/webhooks/nowpayments/
  → signature verified (HMAC-SHA512, sorted JSON, IPN secret)
  → PaymentTransaction updated; deposit confirmed; wallet credited once
```

## 4. Sandbox verification checklist

- [ ] Sandbox API key set; `NOWPAYMENTS_SANDBOX=True`
- [ ] Create a deposit via the API; verify the returned `pay_address`
- [ ] Send a sandbox payment; confirm the IPN arrives
- [ ] IPN rejected when the signature is wrong (tamper the payload)
- [ ] IPN replayed 3× → only one wallet credit (idempotent)
- [ ] `price_amount`/`price_currency` match the invoice; rate stored
- [ ] Underpaid / expired payments land in `confirming` / `expired` (no credit)
- [ ] Switch to production keys; repeat one live small deposit

## 5. Not enabled yet

**Payouts** (`create_payout`) intentionally raise `NotImplementedError` until
the NOWPayments payout API setup (payout wallet + 2FA verification) is
completed. Withdrawals are paid manually by admins in the meantime.

## 6. Reconciliation

Daily: compare `PaymentTransaction` rows against the NOWPayments dashboard.
Missing/duplicate/reversed payments should be recorded, not silently edited
(see `docs/DRD.md` §124).
