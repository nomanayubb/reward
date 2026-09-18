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
| `/api/v1/deposits/` | deposits | planned (stub) |
| `/api/v1/withdrawals/` | withdrawals | planned (stub) |
| `/api/v1/games/` | games | planned (stub) |
| `/api/v1/surveys/` | surveys | planned (stub) |
| `/api/v1/offers/` | offers | planned (stub) |
| `/api/v1/notifications/` | notifications | planned (stub) |
| `/api/v1/postbacks/<provider_code>/` | offers | **live** |
| `/api/v1/webhooks/<provider_code>/` | payments | **live** |

Conventions: JSON, session auth initially, DRF throttling (`anon`, `user`,
`login`, `withdrawal`, `offer_click`, `postback`), cursor/page pagination.

When implementing an endpoint: add it to the module `urls.py`, keep the view
thin, call the service layer, and document request/response here.
