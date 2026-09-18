# SECURITY_RULES

## Secrets

- All secrets come from environment variables; `.env` is git-ignored.
- New keys go into `.env.example` with empty values and a comment.
- Never log secrets, tokens, API keys, full card/wallet numbers or KYC data.

## Money endpoints

- Server-side validation only; no client-supplied amounts or scores.
- Idempotency keys on every external financial event.
- `select_for_update()` for balance-affecting operations.
- Rate limits: login 5/min, withdrawal 3/hour, offer click 30/min, postbacks
  per provider.

## Webhooks / postbacks

- Verify signature (constant-time compare) before any processing.
- Reject stale timestamps; store raw payload for disputes.
- Idempotent processing enforced by DB constraints.
- IP allow-listing where the provider publishes ranges.
- Never reveal internal errors to providers; log them instead.

## Auth and admin

- Argon2 password hashing; 2FA mandatory for admin accounts in production.
- Granular permissions (`withdrawals.approve`, `wallet.adjust`, ...); audit
  every sensitive action with actor, old/new value, reason, IP.
- Session cookies: HttpOnly, Secure, SameSite=Lax in production.
- CSRF protection on all state-changing endpoints (webhooks are exempt but
  signature-verified).

## Games

- Untrusted code: sandboxed iframe, separate origin, CSP, `postMessage` origin
  checks, no cookies, no platform APIs.
- Rate-limit sessions; invalidate suspicious sessions and record fraud events.

## Data protection

- KYC and payment proofs are private files; serve only through
  permission-checked views, never public media.
- Minimize collected PII; provide consent records where legally required.
- Maintain privacy policy, terms, cookie policy and reward/withdrawal terms
  (versioned in CMS).

## Headers / transport (production)

HTTPS only, HSTS, CSP, `X-Content-Type-Options: nosniff`,
`Referrer-Policy: same-origin`, `X-Frame-Options: DENY` on the platform origin.
