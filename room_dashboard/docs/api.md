# API Reference

The Python server serves the dashboard UI and exposes JSON endpoints under `/api`.

Base URL in local kiosk mode:

```text
http://127.0.0.1:8080
```

All API responses follow this envelope:

```json
{
  "generatedAt": "2026-06-13T00:00:00+00:00",
  "ok": true,
  "data": {}
}
```

Error responses include:

```json
{
  "generatedAt": "2026-06-13T00:00:00+00:00",
  "ok": false,
  "error": "Description of the problem"
}
```

## GET /api/health

Readiness check.

Example:

```json
{
  "status": "ready"
}
```

## GET /api/config

Returns public configuration needed by the browser.

Private calendar URLs are not returned.

Example:

```json
{
  "title": "Smart Room Dashboard",
  "subtitle": "Home status, schedule, tasks, music and news",
  "timezone": "Europe/Berlin",
  "refresh": {
    "weatherSeconds": 900,
    "calendarSeconds": 300,
    "todoSeconds": 60,
    "statusSeconds": 10,
    "rssSeconds": 900
  }
}
```

## GET /api/weather

Returns current weather and forecast data.

Source: Open-Meteo.

Important fields:

- `locationName`
- `current.temperature`
- `current.condition`
- `current.humidity`
- `current.windSpeed`
- `forecast[]`

If coordinates are missing, the endpoint returns a setup message instead of failing the page.

## GET /api/calendar

Returns upcoming calendar events parsed from configured iCal feeds.

Important fields:

- `events[].title`
- `events[].start`
- `events[].end`
- `events[].allDay`
- `events[].calendar`
- `events[].color`

If no iCal URLs are configured, the endpoint returns:

```json
{
  "setupRequired": true,
  "message": "Add Google Calendar private iCal URLs to calendar.calendars in config.json.",
  "events": []
}
```

## GET /api/todos

Returns local to-do items.

Example item:

```json
{
  "id": "setup-calendar",
  "title": "Add Google Calendar private iCal URL",
  "done": false,
  "createdAt": "2026-06-13T00:00:00+00:00"
}
```

## POST /api/todos

Adds a to-do item.

Request:

```json
{
  "title": "Buy HDMI cable"
}
```

Response:

```json
[
  {
    "id": "generated-id",
    "title": "Buy HDMI cable",
    "done": false,
    "createdAt": "2026-06-13T00:00:00+00:00"
  }
]
```

## PUT /api/todos

Replaces the full to-do list.

The browser uses this endpoint for checkbox updates.

## DELETE /api/todos/{id}

Deletes a to-do item by ID.

## GET /api/status

Returns network and music status.

Network fields:

- `hostname`
- `localIp`
- `ssid`
- `online`

Music fields:

- `enabled`
- `available`
- `status`
- `artist`
- `title`
- `album`
- `position`
- `duration`

Music data depends on `playerctl`.

## GET /api/rss

Returns aggregated RSS or Atom feed items.

Important fields:

- `items[].source`
- `items[].title`
- `items[].link`
- `items[].publishedAt`

If no feeds are configured, the endpoint returns a setup message.

## Error Handling

External integrations may fail independently. A weather or RSS failure does not stop the dashboard from rendering calendar, to-do, music, or network modules.

The UI displays module-local error states instead of replacing the whole dashboard.
