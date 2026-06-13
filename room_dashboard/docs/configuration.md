# Configuration Reference

Smart Room Dashboard reads configuration from `config.json`.

For a fresh installation:

```bash
cp config.example.json config.json
```

`config.json` is ignored by Git because it can contain private Google Calendar iCal URLs.

If `config.json` is missing, the server falls back to `config.example.json`. This makes the project easy to preview directly after cloning.

## Top-Level Structure

```json
{
  "dashboard": {},
  "refresh": {},
  "weather": {},
  "calendar": {},
  "rss": {},
  "music": {},
  "network": {}
}
```

## Dashboard

```json
"dashboard": {
  "title": "Smart Room Dashboard",
  "subtitle": "Home status, schedule, tasks, music and news",
  "timezone": "Europe/Berlin"
}
```

| Field | Type | Description |
| --- | --- | --- |
| `title` | string | Main title in the dashboard header. |
| `subtitle` | string | Short description below the title. |
| `timezone` | string | IANA timezone used by the clock and date formatting. |

Examples:

- `Europe/Berlin`
- `Europe/Vienna`
- `Europe/Zurich`
- `America/New_York`

## Refresh

```json
"refresh": {
  "weatherSeconds": 900,
  "calendarSeconds": 300,
  "todoSeconds": 60,
  "statusSeconds": 10,
  "rssSeconds": 900
}
```

| Field | Default | Description |
| --- | ---: | --- |
| `weatherSeconds` | 900 | Weather polling interval. |
| `calendarSeconds` | 300 | Calendar polling interval. |
| `todoSeconds` | 60 | To-do polling interval. |
| `statusSeconds` | 10 | Music and network polling interval. |
| `rssSeconds` | 900 | RSS polling interval. |

The frontend enforces a minimum polling interval of 5 seconds.

## Weather

```json
"weather": {
  "locationName": "Berlin",
  "latitude": 52.52,
  "longitude": 13.405,
  "timezone": "Europe/Berlin",
  "forecastDays": 5
}
```

Weather is provided by Open-Meteo and does not require an API key.

| Field | Type | Description |
| --- | --- | --- |
| `locationName` | string | Display name shown in the weather panel. |
| `latitude` | number | Geographic latitude. |
| `longitude` | number | Geographic longitude. |
| `timezone` | string | Timezone for forecast timestamps. |
| `forecastDays` | number | Number of forecast days requested. |

## Calendar

```json
"calendar": {
  "daysAhead": 21,
  "maxItems": 8,
  "calendars": [
    {
      "name": "Personal",
      "color": "#5eead4",
      "url": ""
    }
  ]
}
```

| Field | Type | Description |
| --- | --- | --- |
| `daysAhead` | number | How far into the future events are shown. |
| `maxItems` | number | Maximum number of events returned by the API. |
| `calendars` | array | List of iCal feeds. |
| `name` | string | Calendar label shown in event metadata. |
| `color` | string | Accent color for events from this calendar. |
| `url` | string | Private iCal feed URL. |

### Google Calendar Setup

1. Open Google Calendar.
2. Open settings.
3. Select the calendar.
4. Open "Integrate calendar".
5. Copy "Secret address in iCal format".
6. Paste the URL into `config.json`.

Private iCal URLs are sensitive. Rotate the URL in Google Calendar if it is exposed.

## RSS

```json
"rss": {
  "maxItems": 8,
  "feeds": [
    {
      "name": "Tagesschau",
      "url": "https://www.tagesschau.de/xml/rss2"
    }
  ]
}
```

| Field | Type | Description |
| --- | --- | --- |
| `maxItems` | number | Maximum total feed items returned by the API. |
| `feeds` | array | RSS or Atom feeds. |
| `name` | string | Source label shown in the UI. |
| `url` | string | Feed URL. |

The server aggregates all feeds, sorts by publish date when possible, and returns the newest items.

## Music

```json
"music": {
  "enabled": true
}
```

Music status is read from `playerctl`.

Install on Raspberry Pi OS:

```bash
sudo apt install -y playerctl
```

Check manually:

```bash
playerctl status
playerctl metadata
```

If `playerctl` is missing or no media player is active, the dashboard shows a graceful idle state.

## Network

```json
"network": {
  "checkHost": "1.1.1.1",
  "checkPort": 53
}
```

| Field | Type | Description |
| --- | --- | --- |
| `checkHost` | string | Host used for online connectivity check. |
| `checkPort` | number | TCP port used for online connectivity check. |

The default checks DNS reachability at `1.1.1.1:53`.

## Local To-do Data

To-dos are stored in:

```text
data/todos.json
```

Create it from the example:

```bash
cp data/todos.example.json data/todos.json
```

If the file is missing, the server creates starter tasks automatically.
