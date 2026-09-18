# Deploying to your own server (VPS) — independent of any PaaS

This is the "project finished, own everything" path: your server, your domain,
your database. No Render/Heroku dependency; the same Docker image runs
everywhere.

## 1. Server

Any Ubuntu 22.04/24.04 VPS with 2 GB RAM (Hetzner, Contabo, DigitalOcean,
Hostinger, a Pakistani host — any is fine).

Point your domain's DNS at the server:

```
A     @      <server-ip>
A     www    <server-ip>
```

## 2. Install Docker

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER   # re-login after this
```

## 3. Get the code and configure

```bash
git clone https://github.com/nayubb/reward.git
cd reward
cp .env.example .env
nano .env
```

Set at least:

```
DOMAIN=yourdomain.com
SECRET_KEY=<long random string>
POSTGRES_PASSWORD=<long random password>
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
# plus your provider keys (NOWPayments, CPA networks) as they arrive
```

## 4. Start

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

What happens automatically:
- PostgreSQL + Redis start
- the container entrypoint runs migrations, collects static files and seeds
  starter content (CMS pages, games, ad placements)
- Caddy requests a **Let's Encrypt certificate** for `$DOMAIN` (needs ports
  80/443 open and DNS pointing at the server)
- Celery worker + beat run the background jobs

Open `https://yourdomain.com` — create your admin account:

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

Then in `/admin/` → CMS pages: replace the `[bracketed]` placeholders.

## 5. Moving from a temporary URL (Render/tunnel) to this domain

1. Deploy here first and test the full flow (register → earn → wallet).
2. In **each provider dashboard** update:
   - **Website URL** → `https://yourdomain.com`
   - **Postback URL** → `https://yourdomain.com/api/v1/postbacks/<network_code>/`
3. Email each affiliate manager: "production domain is now yourdomain.com".
4. Only then promote the domain to users. (Free-tier data is disposable —
   start real users on the real domain.)

## 6. Backups (do this on day one)

```bash
# daily database dump at 03:00
crontab -e
0 3 * * * cd /home/<user>/reward && docker compose -f docker-compose.prod.yml exec -T db pg_dump -U reward reward | gzip > /home/<user>/backups/reward-$(date +\%F).sql.gz
```

Also copy `media/` (KYC files, proofs) off-site weekly. Test a restore once
before launch.

## 7. Updates

```bash
git pull
docker compose -f docker-compose.prod.yml up -d --build
```

Migrations run automatically on boot.

## 8. Optional hardening

- `ufw allow 22,80,443/tcp && ufw enable`
- Fail2ban for SSH
- Move KYC/media to S3-compatible storage (private bucket)
- Put the games on a separate subdomain (`games.yourdomain.com`) for isolation
- Monitoring: uptime check on `/accounts/login/` + log alerts
