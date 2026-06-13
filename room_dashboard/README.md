# Smart Room Dashboard

A modern always-on room dashboard for Raspberry Pi and a dedicated monitor.

Smart Room Dashboard turns a Raspberry Pi into a fullscreen information display for daily life: time, date, weather, Google Calendar events, local tasks, music playback status, network status, and RSS news. It is built to run locally, boot automatically, and keep working even when optional integrations are not configured yet.

## Highlights

- Fullscreen kiosk interface designed for a wall-mounted or desk monitor.
- Dependency-free Python 3 backend using only the standard library.
- No frontend build step, package manager, or cloud runtime required.
- Weather via Open-Meteo, no API key required.
- Google Calendar support through private iCal feed URLs.
- Local to-do list persisted as JSON.
- Music status via `playerctl` on Linux/MPRIS-compatible players.
- Network status including hostname, local IP, Wi-Fi name, and online check.
- RSS/Atom feed aggregation for news.
- Raspberry Pi systemd service and Chromium kiosk autostart installer.
- Responsive layout for desktop monitors and maintenance from smaller devices.

## Preview

The dashboard is optimized for a 1920x1080 monitor. On Full HD, all primary modules are visible in the first viewport.

```text
Time and date | Weather | Calendar | To-do | Music | Network | RSS
```

## Repository Structure

```text
room_dashboard/
  dashboard.py                  Local HTTP server and integration layer
  config.example.json           Public configuration template
  data/todos.example.json       Public task data example
  web/index.html                Dashboard markup
  web/styles.css                Responsive visual system
  web/app.js                    Client rendering and polling logic
  scripts/install_raspberry_pi.sh
  scripts/room-dashboard.service
  scripts/room-dashboard-kiosk.desktop
  docs/architecture.md
  docs/configuration.md
  docs/api.md
  docs/raspberry-pi-kiosk.md
  docs/github-release-checklist.md
```

Local runtime files are intentionally ignored by Git:

- `config.json`
- `data/todos.json`

This prevents private calendar URLs and personal task data from being committed accidentally.

## Quick Start

Requirements:

- Python 3.9 or newer.
- Raspberry Pi OS, Linux, macOS, or another system with Python 3 for local development.
- Chromium or another modern browser for display.
- `playerctl` only if music status is needed on Linux.

Clone or copy the project, then create a local configuration:

```bash
cd room_dashboard
cp config.example.json config.json
cp data/todos.example.json data/todos.json
python3 dashboard.py --host 127.0.0.1 --port 8080
```

Open:

```text
http://localhost:8080
```

For access from another device on the same LAN:

```bash
python3 dashboard.py --host 0.0.0.0 --port 8080
```

Then open:

```text
http://<raspberry-pi-ip>:8080
```

## Raspberry Pi Kiosk Setup

Recommended packages:

```bash
sudo apt update
sudo apt install -y python3 chromium-browser unclutter playerctl
```

Some Raspberry Pi OS images use `chromium` instead of `chromium-browser`:

```bash
sudo apt install -y chromium
```

Install the local service and Chromium kiosk autostart:

```bash
cd ~/Documents/room_dashboard
chmod +x scripts/install_raspberry_pi.sh
./scripts/install_raspberry_pi.sh
```

After the next graphical login, Chromium opens the dashboard at:

```text
http://127.0.0.1:8080
```

Detailed deployment notes are in [docs/raspberry-pi-kiosk.md](docs/raspberry-pi-kiosk.md).

## Configuration

Edit `config.json` after copying it from `config.example.json`.

```bash
cp config.example.json config.json
cp data/todos.example.json data/todos.json
```

Restart the dashboard after changing configuration:

```bash
systemctl --user restart room-dashboard.service
```

During local development, stop and start the Python server again:

```bash
python3 dashboard.py
```

Core configuration areas:

- `dashboard`: title, subtitle, and timezone.
- `refresh`: polling intervals per module.
- `weather`: Open-Meteo coordinates and forecast settings.
- `calendar`: Google Calendar private iCal feeds.
- `rss`: RSS or Atom feeds.
- `music`: local player integration toggle.
- `network`: online check host and port.

Full configuration reference: [docs/configuration.md](docs/configuration.md).

## Customization and Integrations

All user-specific settings live in `config.json`. The file is ignored by Git because it may contain private Google Calendar URLs and personal preferences.

### Change Title, Subtitle, and Timezone

Edit the `dashboard` block:

```json
"dashboard": {
  "title": "Smart Room Dashboard",
  "subtitle": "Home status, schedule, tasks, music and news",
  "timezone": "Europe/Berlin"
}
```

Use an IANA timezone name, for example:

- `Europe/Berlin`
- `Europe/Vienna`
- `Europe/Zurich`
- `Europe/London`
- `America/New_York`

The timezone controls the clock, date formatting, calendar display, and weather timestamps.

### Change Weather Location

Weather is powered by Open-Meteo and does not require an API key.

Edit the `weather` block:

```json
"weather": {
  "locationName": "Berlin",
  "latitude": 52.52,
  "longitude": 13.405,
  "timezone": "Europe/Berlin",
  "forecastDays": 5
}
```

Change:

- `locationName`: label shown in the dashboard.
- `latitude`: your latitude.
- `longitude`: your longitude.
- `timezone`: your local timezone.
- `forecastDays`: number of forecast days.

You can get latitude and longitude from Google Maps, OpenStreetMap, or any geocoding website.

### Connect Google Calendar

The dashboard reads Google Calendar through private iCal URLs. This avoids OAuth login flows on a Raspberry Pi kiosk.

In Google Calendar:

1. Open calendar settings.
2. Select the calendar.
3. Open "Integrate calendar".
4. Copy "Secret address in iCal format".
5. Paste it into the `calendar.calendars` list in `config.json`.

Example:

```json
"calendar": {
  "daysAhead": 21,
  "maxItems": 8,
  "calendars": [
    {
      "name": "Personal",
      "color": "#5eead4",
      "url": "https://calendar.google.com/calendar/ical/..."
    },
    {
      "name": "Work",
      "color": "#f6c177",
      "url": "https://calendar.google.com/calendar/ical/..."
    }
  ]
}
```

Options:

- `daysAhead`: how far into the future events are shown.
- `maxItems`: maximum number of events displayed.
- `name`: label for this calendar.
- `color`: accent color for events from this calendar.
- `url`: private iCal feed URL.

Keep private iCal URLs secret. Anyone with that URL can read the calendar feed.

### Change News and RSS Feeds

News are loaded from RSS or Atom feeds.

Edit the `rss` block:

```json
"rss": {
  "maxItems": 8,
  "feeds": [
    {
      "name": "Tagesschau",
      "url": "https://www.tagesschau.de/xml/rss2"
    },
    {
      "name": "BBC World",
      "url": "https://feeds.bbci.co.uk/news/world/rss.xml"
    }
  ]
}
```

To customize news:

- Remove feeds you do not want.
- Add any RSS or Atom feed URL.
- Change `name` to control the source label in the dashboard.
- Change `maxItems` to control how many total items are loaded.

Examples of feed types that work well:

- News websites.
- Blogs.
- GitHub release feeds.
- Weather alerts.
- Local city or public transport feeds, if available.

### Connect Music Status

Music status is read from `playerctl`, which talks to MPRIS-compatible Linux media players.

Install it on Raspberry Pi OS:

```bash
sudo apt install -y playerctl
```

Test it manually:

```bash
playerctl status
playerctl metadata
```

Supported players often include:

- Chromium media tabs.
- Spotify clients.
- VLC.
- Many Linux desktop audio players.

Enable or disable the module in `config.json`:

```json
"music": {
  "enabled": true
}
```

If `playerctl` is not installed or no player is active, the dashboard still works and shows an idle music state.

### Change Network Status Check

The network module shows hostname, local IP, Wi-Fi name, and online status.

Edit:

```json
"network": {
  "checkHost": "1.1.1.1",
  "checkPort": 53
}
```

The default checks whether the Pi can connect to Cloudflare DNS at `1.1.1.1:53`.

Alternative examples:

```json
"network": {
  "checkHost": "8.8.8.8",
  "checkPort": 53
}
```

or a local router:

```json
"network": {
  "checkHost": "192.168.1.1",
  "checkPort": 80
}
```

### Change To-do Items

To-dos are stored locally:

```text
data/todos.json
```

You can edit tasks directly in the dashboard UI, or reset the file from the example:

```bash
cp data/todos.example.json data/todos.json
```

This file is ignored by Git so personal tasks are not published accidentally.

### Change Refresh Intervals

Edit the `refresh` block:

```json
"refresh": {
  "weatherSeconds": 900,
  "calendarSeconds": 300,
  "todoSeconds": 60,
  "statusSeconds": 10,
  "rssSeconds": 900
}
```

Shorter intervals feel more live but create more network requests. The defaults are conservative for an always-on Raspberry Pi.

### Change Kiosk Port or URL

By default, the dashboard runs at:

```text
http://127.0.0.1:8080
```

Run on a different port:

```bash
python3 dashboard.py --host 127.0.0.1 --port 8090
```

For the Raspberry Pi installer, set `ROOM_DASHBOARD_PORT` before running it:

```bash
ROOM_DASHBOARD_PORT=8090 ./scripts/install_raspberry_pi.sh
```

Only use LAN access when needed:

```bash
python3 dashboard.py --host 0.0.0.0 --port 8080
```

Do not expose this dashboard directly to the public internet.

## Operations

Check service status:

```bash
systemctl --user status room-dashboard.service
```

View logs:

```bash
journalctl --user -u room-dashboard.service -f
```

Restart after configuration changes:

```bash
systemctl --user restart room-dashboard.service
```

## Development

This project intentionally stays simple:

- Python standard library only.
- Static HTML/CSS/JavaScript.
- No npm, webpack, Vite, Flask, Django, or database required.

Run local validation:

```bash
./scripts/validate.sh
```

Start the app:

```bash
python3 dashboard.py
```

API reference: [docs/api.md](docs/api.md).

## Security

- Do not commit `config.json` if it contains private iCal URLs.
- Do not commit `data/todos.json` if it contains personal tasks.
- The default server binds to `127.0.0.1`.
- Use `0.0.0.0` only when LAN access is intentional.
- No browser-side secrets are required.

See [SECURITY.md](SECURITY.md) for responsible disclosure and operational security notes.

## Roadmap

Potential future additions:

- Home Assistant integration.
- MQTT room sensors.
- Spotify Web API album art.
- Google Tasks or Todoist sync.
- Admin settings screen.
- Display brightness schedule.
- PIR sensor wake/sleep behavior.

## Contributing

Contributions are welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request.

## License

This project is released under the MIT License. See [LICENSE](LICENSE).
