#!/bin/bash
set -euo pipefail

echo "=== Setting up Vivriti systemd services ==="

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run this script with sudo."
  exit 1
fi

install -d -m 755 /home/moslab/vivriti/logs

BACKEND_BIN_DIR="/home/moslab/miniconda3/envs/vivriti/bin"
if ! /home/moslab/miniconda3/envs/vivriti/bin/python -c "import sqlalchemy" >/dev/null 2>&1; then
  BACKEND_BIN_DIR="/home/moslab/vivriti/.venv/bin"
fi
BACKEND_UVICORN="${BACKEND_BIN_DIR}/uvicorn"
if [[ ! -x "${BACKEND_UVICORN}" ]]; then
  echo "Unable to find a working uvicorn runtime for the backend."
  exit 1
fi
echo "Using backend runtime: ${BACKEND_UVICORN}"

BACKEND_ENV_FILE="/home/moslab/vivriti/backend/.env"
if [[ ! -f "${BACKEND_ENV_FILE}" && -f /home/moslab/vivriti/.env ]]; then
  BACKEND_ENV_FILE="/home/moslab/vivriti/.env"
fi
if [[ ! -f "${BACKEND_ENV_FILE}" ]]; then
  echo "Unable to find a backend environment file."
  exit 1
fi
echo "Using backend env file: ${BACKEND_ENV_FILE}"

MARKER_PYTHON="/home/moslab/miniconda3/envs/vivriti/bin/python"
if ! /home/moslab/miniconda3/envs/vivriti/bin/python -c "import marker" >/dev/null 2>&1; then
  if [[ -x /home/moslab/marker-service/.venv/bin/python ]] && /home/moslab/marker-service/.venv/bin/python -c "import marker" >/dev/null 2>&1; then
    MARKER_PYTHON="/home/moslab/marker-service/.venv/bin/python"
  elif [[ -x /home/moslab/miniconda3/bin/python ]] && /home/moslab/miniconda3/bin/python -c "import marker" >/dev/null 2>&1; then
    MARKER_PYTHON="/home/moslab/miniconda3/bin/python"
  else
    echo "Unable to find a Python environment with the marker package installed."
    exit 1
  fi
fi
echo "Using marker runtime: ${MARKER_PYTHON}"

NPM_PATH=""
for candidate in \
  /home/moslab/opt/node20/bin/npm \
  /home/moslab/apps/node/bin/npm \
  /home/moslab/miniconda3/envs/vivriti/bin/npm \
  /usr/local/bin/npm \
  /usr/bin/npm
do
  if [[ -x "${candidate}" ]]; then
    NPM_PATH="${candidate}"
    break
  fi
done
if [[ -z "${NPM_PATH}" ]]; then
  NPM_PATH="$(find /home/moslab -path '*/bin/npm' 2>/dev/null | head -1)"
fi
if [[ -z "${NPM_PATH}" ]]; then
  echo "Unable to find npm on this server."
  exit 1
fi
NODE_BIN_DIR="$(dirname "${NPM_PATH}")"
echo "Found npm at: ${NPM_PATH}"

CF_PATH="$(which cloudflared 2>/dev/null || true)"
if [[ -z "${CF_PATH}" ]]; then
  CF_PATH="/usr/local/bin/cloudflared"
fi
echo "Found cloudflared at: ${CF_PATH}"

HAS_NAMED_TUNNEL=0
if [[ -d /etc/cloudflared && -n "$(find /etc/cloudflared -maxdepth 2 -type f 2>/dev/null)" ]]; then
  HAS_NAMED_TUNNEL=1
elif [[ -d /home/moslab/.cloudflared && -n "$(find /home/moslab/.cloudflared -maxdepth 2 -type f 2>/dev/null)" ]]; then
  HAS_NAMED_TUNNEL=1
elif [[ -d /root/.cloudflared && -n "$(find /root/.cloudflared -maxdepth 2 -type f 2>/dev/null)" ]]; then
  HAS_NAMED_TUNNEL=1
fi
if [[ "${HAS_NAMED_TUNNEL}" -eq 1 ]]; then
  echo "Named Cloudflare tunnel configuration detected."
else
  echo "No named Cloudflare tunnel configuration detected."
  echo "Quick tunnels are not permanent and will change URL on restart."
fi

cat >/etc/systemd/system/vivriti-backend.service <<EOF
[Unit]
Description=Vivriti FastAPI Backend
After=network.target
Wants=network.target

[Service]
Type=simple
User=moslab
WorkingDirectory=/home/moslab/vivriti
Environment="PATH=${BACKEND_BIN_DIR}:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin"
Environment="PYTHONPATH=/home/moslab/vivriti/backend"
EnvironmentFile=${BACKEND_ENV_FILE}
ExecStart=${BACKEND_UVICORN} app.main:app --host 127.0.0.1 --port 8100
Restart=always
RestartSec=5
StandardOutput=append:/home/moslab/vivriti/logs/backend.log
StandardError=append:/home/moslab/vivriti/logs/backend.log

[Install]
WantedBy=multi-user.target
EOF

cat >/etc/systemd/system/vivriti-marker.service <<EOF
[Unit]
Description=Vivriti Marker PDF Server
After=network.target
Wants=network.target

[Service]
Type=simple
User=moslab
WorkingDirectory=/home/moslab/vivriti
Environment="PATH=$(dirname "${MARKER_PYTHON}"):/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin"
Environment="PYTHONPATH=/home/moslab/vivriti"
ExecStart=${MARKER_PYTHON} scripts/marker_server.py
Restart=always
RestartSec=10
TimeoutStartSec=120
StandardOutput=append:/home/moslab/vivriti/logs/marker.log
StandardError=append:/home/moslab/vivriti/logs/marker.log

[Install]
WantedBy=multi-user.target
EOF

cat >/etc/systemd/system/vivriti-frontend.service <<EOF
[Unit]
Description=Vivriti Next.js Frontend
After=network.target vivriti-backend.service
Wants=network.target

[Service]
Type=simple
User=moslab
WorkingDirectory=/home/moslab/vivriti/frontend
Environment="PATH=${NODE_BIN_DIR}:/home/moslab/miniconda3/envs/vivriti/bin:/usr/local/bin:/usr/bin"
Environment="NODE_OPTIONS=--max-old-space-size=512"
Environment="NODE_ENV=production"
ExecStart=${NPM_PATH} run start -- -H 127.0.0.1 -p 3100
Restart=always
RestartSec=5
StandardOutput=append:/home/moslab/vivriti/logs/frontend.log
StandardError=append:/home/moslab/vivriti/logs/frontend.log

[Install]
WantedBy=multi-user.target
EOF

cat >/etc/systemd/system/vivriti-tunnel-frontend.service <<EOF
[Unit]
Description=Cloudflare Tunnel for Vivriti Frontend
After=network.target vivriti-frontend.service
Wants=network.target

[Service]
Type=simple
User=moslab
ExecStart=${CF_PATH} tunnel --url http://127.0.0.1:3100
Restart=always
RestartSec=10
StandardOutput=append:/home/moslab/vivriti/logs/tunnel-frontend.log
StandardError=append:/home/moslab/vivriti/logs/tunnel-frontend.log

[Install]
WantedBy=multi-user.target
EOF

cat >/etc/systemd/system/vivriti-tunnel-backend.service <<EOF
[Unit]
Description=Cloudflare Tunnel for Vivriti Backend
After=network.target vivriti-backend.service
Wants=network.target

[Service]
Type=simple
User=moslab
ExecStart=${CF_PATH} tunnel --url http://127.0.0.1:8100
Restart=always
RestartSec=10
StandardOutput=append:/home/moslab/vivriti/logs/tunnel-backend.log
StandardError=append:/home/moslab/vivriti/logs/tunnel-backend.log

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload

systemctl enable vivriti-backend
systemctl enable vivriti-marker
systemctl enable vivriti-frontend
if [[ "${HAS_NAMED_TUNNEL}" -eq 1 ]]; then
  systemctl enable vivriti-tunnel-frontend
  systemctl enable vivriti-tunnel-backend
fi

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

if [[ "${HAS_NAMED_TUNNEL}" -eq 1 ]]; then
  systemctl start vivriti-tunnel-frontend
  systemctl start vivriti-tunnel-backend
  echo "Tunnels started"
  sleep 10
else
  echo "Skipping tunnel service start because no named tunnel config was found."
fi

echo ""
echo "=== Service Status ==="
systemctl status vivriti-backend --no-pager | head -5
systemctl status vivriti-frontend --no-pager | head -5
systemctl status vivriti-marker --no-pager | head -5
if [[ "${HAS_NAMED_TUNNEL}" -eq 1 ]]; then
  systemctl status vivriti-tunnel-frontend --no-pager | head -5
  systemctl status vivriti-tunnel-backend --no-pager | head -5
fi

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
