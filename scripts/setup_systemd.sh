#!/bin/bash
set -euo pipefail

echo "=== Setting up Vivriti systemd services ==="

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run this script with sudo."
  exit 1
fi

install -d -m 755 /home/moslab/vivriti/logs

NPM_PATH="$(which npm 2>/dev/null || true)"
if [[ -z "${NPM_PATH}" && -x /home/moslab/miniconda3/envs/vivriti/bin/npm ]]; then
  NPM_PATH="/home/moslab/miniconda3/envs/vivriti/bin/npm"
fi
if [[ -z "${NPM_PATH}" && -x /usr/bin/npm ]]; then
  NPM_PATH="/usr/bin/npm"
fi
if [[ -z "${NPM_PATH}" && -x /usr/local/bin/npm ]]; then
  NPM_PATH="/usr/local/bin/npm"
fi
if [[ -z "${NPM_PATH}" ]]; then
  NPM_PATH="$(find /home/moslab/miniconda3 -name npm 2>/dev/null | head -1)"
fi
if [[ -z "${NPM_PATH}" ]]; then
  echo "Unable to find npm on this server."
  exit 1
fi
echo "Found npm at: ${NPM_PATH}"

CF_PATH="$(which cloudflared 2>/dev/null || true)"
if [[ -z "${CF_PATH}" ]]; then
  CF_PATH="/usr/local/bin/cloudflared"
fi
echo "Found cloudflared at: ${CF_PATH}"

cat >/etc/systemd/system/vivriti-backend.service <<'EOF'
[Unit]
Description=Vivriti FastAPI Backend
After=network.target
Wants=network.target

[Service]
Type=simple
User=moslab
WorkingDirectory=/home/moslab/vivriti/backend
Environment="PATH=/home/moslab/miniconda3/envs/vivriti/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin"
Environment="PYTHONPATH=/home/moslab/vivriti/backend"
EnvironmentFile=/home/moslab/vivriti/backend/.env
ExecStart=/home/moslab/miniconda3/envs/vivriti/bin/uvicorn app.main:app --host 127.0.0.1 --port 8100
Restart=always
RestartSec=5
StandardOutput=append:/home/moslab/vivriti/logs/backend.log
StandardError=append:/home/moslab/vivriti/logs/backend.log

[Install]
WantedBy=multi-user.target
EOF

cat >/etc/systemd/system/vivriti-marker.service <<'EOF'
[Unit]
Description=Vivriti Marker PDF Server
After=network.target
Wants=network.target

[Service]
Type=simple
User=moslab
WorkingDirectory=/home/moslab/vivriti
Environment="PATH=/home/moslab/miniconda3/envs/vivriti/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin"
Environment="PYTHONPATH=/home/moslab/vivriti"
ExecStart=/home/moslab/miniconda3/envs/vivriti/bin/python scripts/marker_server.py
Restart=always
RestartSec=10
TimeoutStartSec=120
StandardOutput=append:/home/moslab/vivriti/logs/marker.log
StandardError=append:/home/moslab/vivriti/logs/marker.log

[Install]
WantedBy=multi-user.target
EOF

cat >/etc/systemd/system/vivriti-frontend.service <<'EOF'
[Unit]
Description=Vivriti Next.js Frontend
After=network.target vivriti-backend.service
Wants=network.target

[Service]
Type=simple
User=moslab
WorkingDirectory=/home/moslab/vivriti/frontend
Environment="PATH=/home/moslab/miniconda3/envs/vivriti/bin:/usr/local/bin:/usr/bin"
Environment="NODE_OPTIONS=--max-old-space-size=512"
Environment="NODE_ENV=production"
ExecStart=NPM_PATH run start -- -H 127.0.0.1 -p 3100
Restart=always
RestartSec=5
StandardOutput=append:/home/moslab/vivriti/logs/frontend.log
StandardError=append:/home/moslab/vivriti/logs/frontend.log

[Install]
WantedBy=multi-user.target
EOF

cat >/etc/systemd/system/vivriti-tunnel-frontend.service <<'EOF'
[Unit]
Description=Cloudflare Tunnel for Vivriti Frontend
After=network.target vivriti-frontend.service
Wants=network.target

[Service]
Type=simple
User=moslab
ExecStart=/usr/local/bin/cloudflared tunnel --url http://127.0.0.1:3100
Restart=always
RestartSec=10
StandardOutput=append:/home/moslab/vivriti/logs/tunnel-frontend.log
StandardError=append:/home/moslab/vivriti/logs/tunnel-frontend.log

[Install]
WantedBy=multi-user.target
EOF

cat >/etc/systemd/system/vivriti-tunnel-backend.service <<'EOF'
[Unit]
Description=Cloudflare Tunnel for Vivriti Backend
After=network.target vivriti-backend.service
Wants=network.target

[Service]
Type=simple
User=moslab
ExecStart=/usr/local/bin/cloudflared tunnel --url http://127.0.0.1:8100
Restart=always
RestartSec=10
StandardOutput=append:/home/moslab/vivriti/logs/tunnel-backend.log
StandardError=append:/home/moslab/vivriti/logs/tunnel-backend.log

[Install]
WantedBy=multi-user.target
EOF

sed -i "s|NPM_PATH|${NPM_PATH}|g" /etc/systemd/system/vivriti-frontend.service
sed -i "s|/usr/local/bin/cloudflared|${CF_PATH}|g" /etc/systemd/system/vivriti-tunnel-frontend.service
sed -i "s|/usr/local/bin/cloudflared|${CF_PATH}|g" /etc/systemd/system/vivriti-tunnel-backend.service

systemctl daemon-reload

systemctl enable vivriti-backend
systemctl enable vivriti-marker
systemctl enable vivriti-frontend
systemctl enable vivriti-tunnel-frontend
systemctl enable vivriti-tunnel-backend

fuser -k 8100/tcp || true
fuser -k 3100/tcp || true
fuser -k 8001/tcp || true

systemctl start vivriti-backend
echo "Backend started"
sleep 3

systemctl start vivriti-marker
echo "Marker started (loading GPU models, wait 60s...)"
sleep 10

systemctl start vivriti-frontend
echo "Frontend started"
sleep 5

systemctl start vivriti-tunnel-frontend
systemctl start vivriti-tunnel-backend
echo "Tunnels started"
sleep 10

echo ""
echo "=== Service Status ==="
systemctl status vivriti-backend --no-pager | head -5
systemctl status vivriti-frontend --no-pager | head -5
systemctl status vivriti-marker --no-pager | head -5
systemctl status vivriti-tunnel-frontend --no-pager | head -5
systemctl status vivriti-tunnel-backend --no-pager | head -5

echo ""
echo "=== Health Checks ==="
sleep 5
curl -s http://127.0.0.1:8100/health && echo " Backend OK"
curl -s http://127.0.0.1:8001/health | head -c 50 && echo " Marker OK"
curl -sI http://127.0.0.1:3100 | head -1 && echo " Frontend OK"

echo ""
echo "=== Tunnel URLs ==="
echo "Check these files for public URLs:"
echo "  cat /home/moslab/vivriti/logs/tunnel-frontend.log | grep trycloudflare"
echo "  cat /home/moslab/vivriti/logs/tunnel-backend.log | grep trycloudflare"

echo ""
echo "=== Done ==="
echo "Services will now restart automatically if they crash."
echo "They will also start automatically on server reboot."
echo ""
echo "Useful commands:"
echo "  sudo systemctl status vivriti-backend"
echo "  sudo systemctl status vivriti-frontend"
echo "  sudo systemctl restart vivriti-frontend"
echo "  sudo journalctl -u vivriti-frontend -f"
