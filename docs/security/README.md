# Security

Summary of the operating rules; the enforceable details live in
`.ai/SECURITY_RULES.md` and `.ai/RULES.md`.

## Baseline

- OWASP protections: CSRF, XSS escaping, ORM parameterization, clickjacking,
  HSTS, secure cookies, CSP (production).
- Argon2 password hashing; login throttling; 2FA for admin accounts.
- Rate limits: login 5/min, withdrawal 3/hour, offer click 30/min, postbacks
  provider-specific.

## Money paths

- Server-side validation only; no client-supplied amounts or scores.
- Idempotency keys on every external financial event.
- Row-level locking for balance changes.
- Immutable ledger; reversals instead of edits.

## Webhooks

- Signature verification (constant-time), timestamp freshness, replay
  protection, idempotent processing, raw payload storage, IP allow-listing
  where published.

## Secrets

- Environment variables only; `.env` is git-ignored; `.env.example` documents
  every key without values.

## Data

- KYC and payment proofs are private files served through permission-checked
  views only.
- PII minimization; consent records where required; versioned terms/privacy.

## Games

- Sandboxed iframe, separate origin, CSP, `postMessage` origin checks, no
  cookies or platform APIs exposed.
