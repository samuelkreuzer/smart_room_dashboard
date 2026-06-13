#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PORT="${ROOM_DASHBOARD_PORT:-8080}"
PYTHON_BIN="${PYTHON_BIN:-$(command -v python3)}"
SERVICE_DIR="${HOME}/.config/systemd/user"
AUTOSTART_DIR="${HOME}/.config/autostart"
SERVICE_FILE="${SERVICE_DIR}/room-dashboard.service"
DESKTOP_FILE="${AUTOSTART_DIR}/room-dashboard-kiosk.desktop"

if [[ ! -x "${PYTHON_BIN}" ]]; then
  echo "python3 was not found. Install it with: sudo apt install -y python3" >&2
  exit 1
fi

BROWSER_BIN="$(command -v chromium-browser || command -v chromium || command -v google-chrome || true)"

mkdir -p "${SERVICE_DIR}" "${AUTOSTART_DIR}"

cat > "${SERVICE_FILE}" <<SERVICE
[Unit]
Description=Smart Room Dashboard local web server
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=${PROJECT_DIR}
Environment=ROOM_DASHBOARD_PORT=${PORT}
ExecStart=${PYTHON_BIN} ${PROJECT_DIR}/dashboard.py --host 127.0.0.1 --port ${PORT}
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
SERVICE

systemctl --user daemon-reload
systemctl --user enable --now room-dashboard.service

if [[ -n "${BROWSER_BIN}" ]]; then
  cat > "${DESKTOP_FILE}" <<DESKTOP
[Desktop Entry]
Type=Application
Name=Smart Room Dashboard Kiosk
Comment=Open Smart Room Dashboard in Chromium kiosk mode
Exec=sh -lc 'sleep 8; exec "${BROWSER_BIN}" --kiosk --noerrdialogs --disable-infobars --disable-session-crashed-bubble --check-for-update-interval=31536000 http://127.0.0.1:${PORT}'
X-GNOME-Autostart-enabled=true
DESKTOP
  chmod 0644 "${DESKTOP_FILE}"
else
  echo "Chromium was not found. Install it with: sudo apt install -y chromium-browser" >&2
fi

echo
echo "Smart Room Dashboard service installed."
echo "Service: ${SERVICE_FILE}"
echo "Dashboard URL: http://127.0.0.1:${PORT}"
if [[ -n "${BROWSER_BIN}" ]]; then
  echo "Kiosk autostart: ${DESKTOP_FILE}"
fi
echo
echo "Useful commands:"
echo "  systemctl --user status room-dashboard.service"
echo "  journalctl --user -u room-dashboard.service -f"
