# Raspberry Pi Kiosk Setup

This guide describes the intended production setup for a Raspberry Pi connected to a permanent monitor.

## Recommended Hardware

- Raspberry Pi 4 or newer.
- Official Raspberry Pi power supply.
- MicroSD card with Raspberry Pi OS.
- HDMI monitor.
- Stable Wi-Fi or Ethernet connection.

The application is lightweight and should also run on older boards, but Chromium kiosk performance is noticeably better on Pi 4 or newer.

## System Packages

Install the runtime packages:

```bash
sudo apt update
sudo apt install -y python3 chromium-browser unclutter playerctl
```

If your OS image names Chromium differently:

```bash
sudo apt install -y chromium
```

Package purpose:

| Package | Purpose |
| --- | --- |
| `python3` | Runs `dashboard.py`. |
| `chromium-browser` or `chromium` | Fullscreen kiosk browser. |
| `unclutter` | Hides the mouse pointer after inactivity. |
| `playerctl` | Reads music metadata from MPRIS players. |

## Install the Dashboard Service

Create local runtime files first:

```bash
cd ~/Documents/room_dashboard
cp config.example.json config.json
cp data/todos.example.json data/todos.json
```

Edit `config.json` before installing if you already know your weather location, RSS feeds, or Google Calendar iCal URL.

From the project directory:

```bash
cd ~/Documents/room_dashboard
chmod +x scripts/install_raspberry_pi.sh
./scripts/install_raspberry_pi.sh
```

The script creates a systemd user service:

```text
~/.config/systemd/user/room-dashboard.service
```

It also creates a desktop autostart file:

```text
~/.config/autostart/room-dashboard-kiosk.desktop
```

On the next graphical login, Chromium opens automatically in kiosk mode.

## Manual Service Commands

Start:

```bash
systemctl --user start room-dashboard.service
```

Stop:

```bash
systemctl --user stop room-dashboard.service
```

Restart:

```bash
systemctl --user restart room-dashboard.service
```

Enable at login:

```bash
systemctl --user enable room-dashboard.service
```

Logs:

```bash
journalctl --user -u room-dashboard.service -f
```

## Kiosk Behavior

The kiosk autostart entry launches Chromium with:

- Kiosk mode.
- Local dashboard URL.
- Reduced first-run dialogs.
- Disabled infobars.
- A short startup delay so the Python server is ready first.

The dashboard URL is:

```text
http://127.0.0.1:8080
```

This is intentionally local-only. Use `0.0.0.0` only if you want LAN access.

## Screen Reliability

For a permanent display, consider disabling screen blanking in Raspberry Pi OS:

```bash
sudo raspi-config
```

Then use:

```text
Display Options -> Screen Blanking -> No
```

You can also add these commands to the desktop session if needed:

```bash
xset s off
xset -dpms
xset s noblank
```

## Troubleshooting

### The browser opens but the page is unavailable

Check whether the service is running:

```bash
systemctl --user status room-dashboard.service
```

Check logs:

```bash
journalctl --user -u room-dashboard.service -n 100
```

### Weather does not load

Confirm `latitude`, `longitude`, and `timezone` in `config.json`.

### Calendar is empty

Confirm the Google Calendar private iCal URL is present and reachable. The calendar must have future events within `calendar.daysAhead`.

Also confirm you edited `config.json`, not `config.example.json`.

### Music is always idle

Install `playerctl` and confirm your media player exposes MPRIS metadata:

```bash
playerctl status
playerctl metadata
```

### Network SSID is empty

Ethernet-only systems may not expose Wi-Fi SSID. The dashboard will still show local IP and online status.
