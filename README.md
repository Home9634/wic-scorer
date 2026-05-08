# Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

# Run locally

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

# Run with PM2

Start both the API and Cloudflare Tunnel:

```bash
pm2 start ecosystem.config.cjs
pm2 save
```

To keep PM2 enabled after a reboot, run:

```bash
pm2 startup
```

# Cloudflare Tunnel

The system-wide `cloudflared service` handles all tunnels. Just ensure it's running:

```bash
sudo systemctl status cloudflared
```

Then, in [Cloudflare Zero Trust](https://one.dash.cloudflare.com/):

1. Create a named tunnel (e.g., `wic-scorer`).
2. Configure it to route to `http://localhost:8000`.
3. Save.

The tunnel will automatically connect when the service is active. Start the API with:

```bash
pm2 start ecosystem.config.cjs
pm2 save
```
