# API Documentation

OpenAPI schema: `/api/v1/schema/` · Swagger UI: `/api/v1/docs/`

## Surface

| Prefix | Module | Status |
| --- | --- | --- |
| `/api/v1/auth/` | accounts | **live** — register, login, logout, me |
| `/api/v1/users/` | users | planned (stub) |
| `/api/v1/wallets/` | wallets | **live** — `GET summary/` (PKR + USD buckets) |
| `/api/v1/ledger/` | ledger | **live** — `GET transactions/` (type/status filters) |
| `/api/v1/rewards/` | rewards | planned (stub) |
| `/api/v1/deposits/` | deposits | **live** — create/list (manual provider for dev) |
| `/api/v1/withdrawals/` | withdrawals | **live** — request/list + methods |
| `/api/v1/games/` | games | **live** — catalog + sessions (`<slug>/sessions/`, `sessions/<token>/events|end/`) |
| `/api/v1/surveys/` | surveys | **live** — active catalog |
| `/api/v1/offers/` | offers | **live** — eligibility-filtered |
| `/api/v1/notifications/` | notifications | **live** — list, read, read-all, unread count |
| `/api/v1/postbacks/<provider_code>/` | offers | **live** |
| `/api/v1/webhooks/<provider_code>/` | payments | **live** |

Conventions: JSON, session auth initially, DRF throttling (`anon`, `user`,
`login`, `withdrawal`, `offer_click`, `postback`), cursor/page pagination.

When implementing an endpoint: add it to the module `urls.py`, keep the view
thin, call the service layer, and document request/response here.
