# Integrations

| Document | Covers |
| --- | --- |
| `GAME_INTEGRATION.md` | Game folder contract, Game SDK, session flow, anti-cheat, per-game docs |
| `CPA_INTEGRATION.md` | CPA adapter interface, postback contract, quotas, compliance, reconciliation |

Provider adapters live in `apps/*/providers/`. Adding an integration must not
require changes to core services — only a new adapter, credentials,
configuration and tests.
