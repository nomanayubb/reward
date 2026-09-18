# Expose the local dev server with a public https URL (temporary).
#
# Requires cloudflared:
#   winget install --id Cloudflare.cloudflared
#
# Then:
#   .\scripts\public-tunnel.ps1            # serves http://127.0.0.1:8010
#
# It prints a https://<random-words>.trycloudflare.com URL. That URL changes
# every time you start the tunnel — use it to show a live site quickly; for a
# stable free URL use render.yaml instead (docs/deployment/README.md).

param(
    [string]$Port = "8010"
)

$cloudflared = Get-Command cloudflared -ErrorAction SilentlyContinue
if (-not $cloudflared) {
    Write-Host "cloudflared is not installed."
    Write-Host "Install it with:  winget install --id Cloudflare.cloudflared"
    exit 1
}

Write-Host "Starting a public tunnel to http://127.0.0.1:$Port ..."
Write-Host "Copy the https://*.trycloudflare.com URL printed below."
& cloudflared tunnel --url "http://127.0.0.1:$Port"
