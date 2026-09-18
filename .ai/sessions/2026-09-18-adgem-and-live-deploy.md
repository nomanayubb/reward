# Session: AdGem integration, live deployment fix, generic offerwalls

Date: 2026-09-18
Topic: AdGem (offerwall + postbacks + reporting), Render production fix, and
making offerwalls network-agnostic

## User requests (this session)

- Continue the build: frontend, admin UI, then the AdGem integration end to end
  (they supplied App ID 33592 and the Postback Key).
- Deploy to a live URL for AdGem's property review (Render free tier).
- After launch, reported: login on the live site failed with a CSRF error and
  the page still showed `DEBUG = True`.
- Review feedback: *"why you do iframe when you know there's 17 more networks
  we have to add"* — the AdGem offerwall page was network-specific.

## What was done

1. **AdGem integration**
   - Adapter (`apps/cpa/providers/adgem.py`): REST Offer API, Prism (GraphQL)
     mode (`mode: prism`), Reporting API client, Cloudflare-safe User-Agent.
   - Web Offerwall (iframe, App ID only) with stable `u<uuid>` player id.
   - Postbacks: signature verification (v3), player-id → user resolution,
     automatic offer provisioning, compliance gating.
   - Reconciliation: `manage.py reconcile_provider adgem --days N`.
   - Postback chain verified end-to-end with the real key: signed postback →
     224 PKR credited (40% of $2 × 280), replay → duplicate, bad signature →
     rejected.
   - Blocker: Offer API/Prism refresh token is issued by the AdGem Team only;
     tokens tried returned 401 with empty scopes.

2. **Live deployment (Render)** — `https://reward-odgq.onrender.com`
   - Pages verified 200: landing, login, register, CMS pages, robots, sitemap.
   - **Bug found:** the container silently ran development settings. Root
     causes: `docker/start.sh` ran `manage.py` (dev default leaked into
     gunicorn's environment) and the local `.env` was baked into the image
     (`COPY . .` with no `.dockerignore`).
   - **Fix:** `.dockerignore` (never ship `.env`, DB, media, memory), forced
     `DJANGO_SETTINGS_MODULE=config.settings.production` in `docker/start.sh`
     and `Dockerfile`. Verified live: HSTS, Secure cookies, DEBUG off.
   - GitHub credentials are now cached in the agent shell, so the agent can
     push directly.

3. **Generic offerwalls (review feedback)**
   - Removed the AdGem-specific view and template.
   - New hub `/offers/offerwall/` lists every enabled network that exposes a
     pre-built wall; `/offers/offerwall/<code>/` renders it in an iframe.
   - The URL is configuration: `offerwall_url_template` on the adapter
     (`{player_id}`, `{app_id}`), overridable per provider; `{app_id}` resolves
     from provider config or `<CODE>_APP_ID`. `/offers/offerwall/adgem/` still
     works via the generic route.
   - Docs updated (`ADGEM.md`, `NETWORK_CATALOG.md`).

## Decisions

- Adding a network's offerwall must never require new view code — it is an
  adapter class attribute or a provider-config override (extends ADR-003).
- Containers always run production settings; development settings are for the
  developer machine only.

## Blockers / open

1. AdGem property approval (App ID 33592) — wall shows no offers until then.
2. `incentive_allowed` stays `false` until AdGem confirms incentivized traffic
   in writing (T&C §11.3).
3. Offer API/Prism refresh token must come from AdGem support.
4. Next networks to add: pick from `docs/integrations/NETWORK_CATALOG.md`.

## Tests

230 passing (`pytest`), `scripts/project-check` green.

## Commits this session

See `git log` — includes `59909b4` (Prism + docs), `6bb8aae` (container
production fix), and the generic-offerwall commit.
