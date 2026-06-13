#!/usr/bin/env python3
"""Smart Room Dashboard server.

This module serves the static dashboard UI and exposes small JSON endpoints for
weather, calendar, to-do, music, network, and RSS data. It intentionally uses
only the Python standard library so the project is easy to run on Raspberry Pi
OS without a build step or dependency manager.
"""

from __future__ import annotations

import argparse
import datetime as dt
import email.utils
import json
import os
import re
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
from xml.etree import ElementTree

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover - Python < 3.9 fallback
    ZoneInfo = None  # type: ignore


ROOT_DIR = Path(__file__).resolve().parent
WEB_DIR = ROOT_DIR / "web"
DATA_DIR = ROOT_DIR / "data"
DEFAULT_CONFIG = ROOT_DIR / "config.json"
EXAMPLE_CONFIG = ROOT_DIR / "config.example.json"
TODO_FILE = DATA_DIR / "todos.json"
HTTP_TIMEOUT_SECONDS = 8

JSON_HEADERS = {
    "Content-Type": "application/json; charset=utf-8",
    "Cache-Control": "no-store",
}

WEATHER_CODES = {
    0: ("Clear sky", "sun"),
    1: ("Mainly clear", "sun"),
    2: ("Partly cloudy", "cloud-sun"),
    3: ("Overcast", "cloud"),
    45: ("Fog", "fog"),
    48: ("Rime fog", "fog"),
    51: ("Light drizzle", "drizzle"),
    53: ("Drizzle", "drizzle"),
    55: ("Dense drizzle", "drizzle"),
    56: ("Freezing drizzle", "drizzle"),
    57: ("Freezing drizzle", "drizzle"),
    61: ("Light rain", "rain"),
    63: ("Rain", "rain"),
    65: ("Heavy rain", "rain"),
    66: ("Freezing rain", "rain"),
    67: ("Freezing rain", "rain"),
    71: ("Light snow", "snow"),
    73: ("Snow", "snow"),
    75: ("Heavy snow", "snow"),
    77: ("Snow grains", "snow"),
    80: ("Rain showers", "showers"),
    81: ("Rain showers", "showers"),
    82: ("Heavy showers", "showers"),
    85: ("Snow showers", "snow"),
    86: ("Snow showers", "snow"),
    95: ("Thunderstorm", "storm"),
    96: ("Thunderstorm with hail", "storm"),
    99: ("Thunderstorm with hail", "storm"),
}


def now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def read_json_file(path: Path, fallback: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return fallback
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc}") from exc


def write_json_file(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_config() -> Dict[str, Any]:
    configured_path = os.environ.get("ROOM_DASHBOARD_CONFIG")
    config_path = Path(configured_path) if configured_path else DEFAULT_CONFIG
    if not configured_path and not config_path.exists():
        config_path = EXAMPLE_CONFIG
    config = read_json_file(config_path, {})
    return config if isinstance(config, dict) else {}


def timezone_from_config(config: Dict[str, Any]) -> dt.tzinfo:
    tz_name = config.get("dashboard", {}).get("timezone") or config.get("weather", {}).get("timezone")
    if ZoneInfo and tz_name:
        try:
            return ZoneInfo(str(tz_name))
        except Exception:
            pass
    return dt.datetime.now().astimezone().tzinfo or dt.timezone.utc


def json_bytes(payload: Any) -> bytes:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def fetch_url(url: str, timeout: int = HTTP_TIMEOUT_SECONDS) -> bytes:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "SmartRoomDashboard/1.0 (+local Raspberry Pi dashboard)",
            "Accept": "*/*",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def fetch_json(url: str, timeout: int = HTTP_TIMEOUT_SECONDS) -> Any:
    return json.loads(fetch_url(url, timeout).decode("utf-8"))


def api_envelope(data: Any = None, error: Optional[str] = None, **extra: Any) -> Dict[str, Any]:
    payload = {"generatedAt": now_utc(), "ok": error is None}
    if data is not None:
        payload["data"] = data
    if error:
        payload["error"] = error
    payload.update(extra)
    return payload


def weather_condition(code: Optional[int]) -> Dict[str, Any]:
    label, icon = WEATHER_CODES.get(int(code or 0), ("Unknown", "cloud"))
    return {"code": code, "label": label, "icon": icon}


def get_weather(config: Dict[str, Any]) -> Dict[str, Any]:
    weather = config.get("weather", {})
    latitude = weather.get("latitude")
    longitude = weather.get("longitude")
    if latitude is None or longitude is None:
        return {
            "setupRequired": True,
            "message": "Set weather.latitude and weather.longitude in config.json.",
        }

    timezone = weather.get("timezone") or config.get("dashboard", {}).get("timezone") or "auto"
    query = urllib.parse.urlencode(
        {
            "latitude": latitude,
            "longitude": longitude,
            "timezone": timezone,
            "forecast_days": int(weather.get("forecastDays", 5)),
            "current": ",".join(
                [
                    "temperature_2m",
                    "relative_humidity_2m",
                    "apparent_temperature",
                    "is_day",
                    "precipitation",
                    "weather_code",
                    "cloud_cover",
                    "wind_speed_10m",
                    "wind_direction_10m",
                ]
            ),
            "daily": ",".join(
                [
                    "weather_code",
                    "temperature_2m_max",
                    "temperature_2m_min",
                    "precipitation_sum",
                    "sunrise",
                    "sunset",
                ]
            ),
        }
    )
    api_url = f"https://api.open-meteo.com/v1/forecast?{query}"
    raw = fetch_json(api_url)
    current = raw.get("current", {})
    daily = raw.get("daily", {})

    forecast = []
    for index, date_value in enumerate(daily.get("time", []) or []):
        code = value_at(daily, "weather_code", index)
        forecast.append(
            {
                "date": date_value,
                "condition": weather_condition(code),
                "temperatureMax": value_at(daily, "temperature_2m_max", index),
                "temperatureMin": value_at(daily, "temperature_2m_min", index),
                "precipitation": value_at(daily, "precipitation_sum", index),
                "sunrise": value_at(daily, "sunrise", index),
                "sunset": value_at(daily, "sunset", index),
            }
        )

    return {
        "locationName": weather.get("locationName", "Configured location"),
        "units": raw.get("current_units", {}),
        "dailyUnits": raw.get("daily_units", {}),
        "current": {
            "time": current.get("time"),
            "temperature": current.get("temperature_2m"),
            "feelsLike": current.get("apparent_temperature"),
            "humidity": current.get("relative_humidity_2m"),
            "precipitation": current.get("precipitation"),
            "cloudCover": current.get("cloud_cover"),
            "windSpeed": current.get("wind_speed_10m"),
            "windDirection": current.get("wind_direction_10m"),
            "isDay": current.get("is_day") == 1,
            "condition": weather_condition(current.get("weather_code")),
        },
        "forecast": forecast,
    }


def value_at(container: Dict[str, Any], key: str, index: int) -> Any:
    values = container.get(key, [])
    if not isinstance(values, list) or index >= len(values):
        return None
    return values[index]


def unescape_ical_text(value: str) -> str:
    return (
        value.replace("\\n", "\n")
        .replace("\\N", "\n")
        .replace("\\,", ",")
        .replace("\\;", ";")
        .replace("\\\\", "\\")
        .strip()
    )


def unfold_ical_lines(text: str) -> Iterable[str]:
    current = ""
    for raw_line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        if raw_line.startswith((" ", "\t")):
            current += raw_line[1:]
            continue
        if current:
            yield current
        current = raw_line
    if current:
        yield current


def parse_ical_datetime(raw: str, params: str, fallback_tz: dt.tzinfo) -> Tuple[Optional[dt.datetime], bool]:
    value = raw.strip()
    is_all_day = "VALUE=DATE" in params or re.fullmatch(r"\d{8}", value) is not None
    try:
        if is_all_day:
            parsed = dt.datetime.strptime(value[:8], "%Y%m%d")
            return parsed.replace(tzinfo=fallback_tz), True
        if value.endswith("Z"):
            parsed = dt.datetime.strptime(value, "%Y%m%dT%H%M%SZ")
            return parsed.replace(tzinfo=dt.timezone.utc).astimezone(fallback_tz), False
        parsed = dt.datetime.strptime(value[:15], "%Y%m%dT%H%M%S")
        return parsed.replace(tzinfo=fallback_tz), False
    except Exception:
        return None, is_all_day


def parse_ical_events(text: str, calendar_name: str, color: str, fallback_tz: dt.tzinfo) -> List[Dict[str, Any]]:
    events: List[Dict[str, Any]] = []
    inside_event = False
    properties: Dict[str, Tuple[str, str]] = {}

    for line in unfold_ical_lines(text):
        if line == "BEGIN:VEVENT":
            inside_event = True
            properties = {}
            continue
        if line == "END:VEVENT" and inside_event:
            event = event_from_ical_properties(properties, calendar_name, color, fallback_tz)
            if event:
                events.append(event)
            inside_event = False
            continue
        if not inside_event or ":" not in line:
            continue
        name_and_params, value = line.split(":", 1)
        key = name_and_params.split(";", 1)[0].upper()
        params = name_and_params[len(key) :]
        properties[key] = (params, value)

    return events


def event_from_ical_properties(
    properties: Dict[str, Tuple[str, str]],
    calendar_name: str,
    color: str,
    fallback_tz: dt.tzinfo,
) -> Optional[Dict[str, Any]]:
    start_raw = properties.get("DTSTART")
    if not start_raw:
        return None
    end_raw = properties.get("DTEND")
    start, all_day = parse_ical_datetime(start_raw[1], start_raw[0], fallback_tz)
    if start is None:
        return None
    end = None
    if end_raw:
        end, _ = parse_ical_datetime(end_raw[1], end_raw[0], fallback_tz)
    uid = properties.get("UID", ("", str(uuid.uuid4())))[1]
    summary = unescape_ical_text(properties.get("SUMMARY", ("", "Untitled event"))[1])
    location = unescape_ical_text(properties.get("LOCATION", ("", ""))[1])

    return {
        "id": uid,
        "calendar": calendar_name,
        "color": color,
        "title": summary,
        "location": location,
        "start": start.isoformat(),
        "end": end.isoformat() if end else None,
        "allDay": all_day,
    }


def get_calendar(config: Dict[str, Any]) -> Dict[str, Any]:
    calendar_config = config.get("calendar", {})
    calendars = [calendar for calendar in calendar_config.get("calendars", []) if calendar.get("url")]
    if not calendars:
        return {
            "setupRequired": True,
            "message": "Add Google Calendar private iCal URLs to calendar.calendars in config.json.",
            "events": [],
        }

    fallback_tz = timezone_from_config(config)
    now = dt.datetime.now(fallback_tz)
    until = now + dt.timedelta(days=int(calendar_config.get("daysAhead", 21)))
    max_items = int(calendar_config.get("maxItems", 8))
    events: List[Dict[str, Any]] = []
    errors: List[str] = []

    for index, calendar in enumerate(calendars):
        url = calendar.get("url")
        if not url:
            continue
        name = calendar.get("name") or f"Calendar {index + 1}"
        color = calendar.get("color") or "#5eead4"
        try:
            text = fetch_url(url).decode("utf-8", errors="replace")
            events.extend(parse_ical_events(text, str(name), str(color), fallback_tz))
        except Exception as exc:
            errors.append(f"{name}: {exc}")

    def event_start(event: Dict[str, Any]) -> dt.datetime:
        return dt.datetime.fromisoformat(event["start"])

    upcoming = [
        event
        for event in events
        if event_start(event) >= now - dt.timedelta(hours=12) and event_start(event) <= until
    ]
    upcoming.sort(key=event_start)
    return {"events": upcoming[:max_items], "errors": errors}


def normalize_todos(raw: Any) -> List[Dict[str, Any]]:
    if not isinstance(raw, list):
        return []
    todos = []
    for item in raw:
        if not isinstance(item, dict) or not str(item.get("title", "")).strip():
            continue
        todos.append(
            {
                "id": str(item.get("id") or uuid.uuid4()),
                "title": str(item.get("title", "")).strip(),
                "done": bool(item.get("done", False)),
                "createdAt": item.get("createdAt") or now_utc(),
            }
        )
    return todos


def get_todos() -> List[Dict[str, Any]]:
    return normalize_todos(read_json_file(TODO_FILE, []))


def save_todos(todos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    normalized = normalize_todos(todos)
    write_json_file(TODO_FILE, normalized)
    return normalized


def run_command(command: List[str], timeout: int = 2) -> Optional[str]:
    try:
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        output = result.stdout.strip()
        return output if result.returncode == 0 and output else None
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None


def get_music_status(config: Dict[str, Any]) -> Dict[str, Any]:
    music_config = config.get("music", {})
    if music_config.get("enabled", True) is False:
        return {"enabled": False}

    status = run_command(["playerctl", "status"])
    if status is None:
        return {
            "enabled": True,
            "available": False,
            "message": "Install playerctl on the Raspberry Pi to expose media status.",
        }

    artist = run_command(["playerctl", "metadata", "artist"])
    title = run_command(["playerctl", "metadata", "title"])
    album = run_command(["playerctl", "metadata", "album"])
    length_raw = run_command(["playerctl", "metadata", "mpris:length"])
    position_raw = run_command(["playerctl", "position"])

    def seconds_from_microseconds(value: Optional[str]) -> Optional[int]:
        try:
            return int(int(value or "0") / 1_000_000)
        except ValueError:
            return None

    def seconds_from_float(value: Optional[str]) -> Optional[int]:
        try:
            return int(float(value or "0"))
        except ValueError:
            return None

    return {
        "enabled": True,
        "available": True,
        "status": status,
        "artist": artist,
        "title": title,
        "album": album,
        "duration": seconds_from_microseconds(length_raw),
        "position": seconds_from_float(position_raw),
    }


def get_local_ip() -> Optional[str]:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.settimeout(1)
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
    except OSError:
        return None


def get_ssid() -> Optional[str]:
    return (
        run_command(["iwgetid", "-r"])
        or parse_airport_ssid(run_command(["networksetup", "-getairportnetwork", "en0"]))
        or run_command(["nmcli", "-t", "-f", "active,ssid", "dev", "wifi"])
    )


def parse_airport_ssid(output: Optional[str]) -> Optional[str]:
    if not output or ":" not in output:
        return None
    return output.split(":", 1)[1].strip()


def is_online(config: Dict[str, Any]) -> bool:
    network_config = config.get("network", {})
    host = str(network_config.get("checkHost", "1.1.1.1"))
    port = int(network_config.get("checkPort", 53))
    try:
        with socket.create_connection((host, port), timeout=2):
            return True
    except OSError:
        return False


def get_network_status(config: Dict[str, Any]) -> Dict[str, Any]:
    hostname = socket.gethostname()
    return {
        "hostname": hostname,
        "localIp": get_local_ip(),
        "ssid": get_ssid(),
        "online": is_online(config),
    }


def xml_text(node: Optional[ElementTree.Element], tag: str) -> str:
    if node is None:
        return ""
    child = node.find(tag)
    if child is None or child.text is None:
        return ""
    return child.text.strip()


def atom_text(node: Optional[ElementTree.Element], tag: str) -> str:
    return xml_text(node, f"{{http://www.w3.org/2005/Atom}}{tag}")


def parse_date(value: str) -> Optional[str]:
    if not value:
        return None
    try:
        parsed = email.utils.parsedate_to_datetime(value)
        return parsed.isoformat()
    except Exception:
        return value


def parse_rss_feed(xml_bytes: bytes, source_name: str, max_items: int) -> List[Dict[str, Any]]:
    root = ElementTree.fromstring(xml_bytes)
    items: List[Dict[str, Any]] = []

    channel = root.find("channel")
    for item in (channel.findall("item") if channel is not None else root.findall(".//item")):
        title = xml_text(item, "title")
        if not title:
            continue
        items.append(
            {
                "source": source_name,
                "title": title,
                "link": xml_text(item, "link"),
                "publishedAt": parse_date(xml_text(item, "pubDate") or xml_text(item, "date")),
            }
        )
        if len(items) >= max_items:
            return items

    atom_ns = {"atom": "http://www.w3.org/2005/Atom"}
    for entry in root.findall("atom:entry", atom_ns):
        title = atom_text(entry, "title")
        link_node = entry.find("atom:link", atom_ns)
        link = link_node.attrib.get("href", "") if link_node is not None else ""
        items.append(
            {
                "source": source_name,
                "title": title,
                "link": link,
                "publishedAt": parse_date(atom_text(entry, "updated") or atom_text(entry, "published")),
            }
        )
        if len(items) >= max_items:
            break

    return items


def get_rss(config: Dict[str, Any]) -> Dict[str, Any]:
    rss_config = config.get("rss", {})
    feeds = rss_config.get("feeds", [])
    if not feeds:
        return {"setupRequired": True, "message": "Add RSS feed URLs to rss.feeds in config.json.", "items": []}

    max_total = int(rss_config.get("maxItems", 8))
    items: List[Dict[str, Any]] = []
    errors: List[str] = []

    for index, feed in enumerate(feeds):
        url = feed.get("url")
        if not url:
            continue
        name = feed.get("name") or f"Feed {index + 1}"
        try:
            items.extend(parse_rss_feed(fetch_url(url), str(name), max_total))
        except Exception as exc:
            errors.append(f"{name}: {exc}")

    def sort_key(item: Dict[str, Any]) -> str:
        return item.get("publishedAt") or ""

    items.sort(key=sort_key, reverse=True)
    return {"items": items[:max_total], "errors": errors}


class DashboardHandler(SimpleHTTPRequestHandler):
    server_version = "SmartRoomDashboard/1.0"

    def log_message(self, fmt: str, *args: Any) -> None:
        sys.stdout.write(
            f"{dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {self.address_string()} - {fmt % args}\n"
        )

    def end_headers(self) -> None:
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        super().end_headers()

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path.startswith("/api/"):
            self.handle_api_get(parsed.path)
            return
        self.serve_static(parsed.path)

    def do_POST(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/todos":
            body = self.read_json_body()
            todos = get_todos()
            title = str(body.get("title", "")).strip() if isinstance(body, dict) else ""
            if not title:
                self.send_json(api_envelope(error="Todo title is required."), HTTPStatus.BAD_REQUEST)
                return
            todos.insert(0, {"id": str(uuid.uuid4()), "title": title, "done": False, "createdAt": now_utc()})
            self.send_json(api_envelope(save_todos(todos)))
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def do_PUT(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/todos":
            body = self.read_json_body()
            if not isinstance(body, list):
                self.send_json(api_envelope(error="Expected a JSON array."), HTTPStatus.BAD_REQUEST)
                return
            self.send_json(api_envelope(save_todos(body)))
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def do_DELETE(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        match = re.fullmatch(r"/api/todos/([^/]+)", parsed.path)
        if match:
            todo_id = urllib.parse.unquote(match.group(1))
            todos = [todo for todo in get_todos() if todo["id"] != todo_id]
            self.send_json(api_envelope(save_todos(todos)))
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def handle_api_get(self, path: str) -> None:
        config = load_config()
        try:
            if path == "/api/health":
                self.send_json(api_envelope({"status": "ready"}))
            elif path == "/api/config":
                dashboard = config.get("dashboard", {})
                self.send_json(
                    api_envelope(
                        {
                            "title": dashboard.get("title", "Smart Room Dashboard"),
                            "subtitle": dashboard.get("subtitle", "Live room control surface"),
                            "timezone": dashboard.get("timezone", ""),
                            "refresh": config.get("refresh", {}),
                        }
                    )
                )
            elif path == "/api/weather":
                self.send_json(api_envelope(get_weather(config)))
            elif path == "/api/calendar":
                self.send_json(api_envelope(get_calendar(config)))
            elif path == "/api/todos":
                self.send_json(api_envelope(get_todos()))
            elif path == "/api/status":
                self.send_json(
                    api_envelope(
                        {
                            "network": get_network_status(config),
                            "music": get_music_status(config),
                        }
                    )
                )
            elif path == "/api/rss":
                self.send_json(api_envelope(get_rss(config)))
            else:
                self.send_json(api_envelope(error="Unknown endpoint."), HTTPStatus.NOT_FOUND)
        except urllib.error.URLError as exc:
            self.send_json(api_envelope(error=f"External request failed: {exc}"), HTTPStatus.BAD_GATEWAY)
        except ValueError as exc:
            self.send_json(api_envelope(error=str(exc)), HTTPStatus.INTERNAL_SERVER_ERROR)
        except Exception as exc:
            self.send_json(api_envelope(error=f"Unexpected server error: {exc}"), HTTPStatus.INTERNAL_SERVER_ERROR)

    def serve_static(self, path: str) -> None:
        if path in ("", "/"):
            path = "/index.html"
        safe_path = Path(urllib.parse.unquote(path).lstrip("/"))
        target = (WEB_DIR / safe_path).resolve()
        if not str(target).startswith(str(WEB_DIR.resolve())) or not target.exists() or not target.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        content_type = self.guess_type(str(target))
        data = target.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(data)

    def read_json_body(self) -> Any:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return None
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def send_json(self, payload: Any, status: HTTPStatus = HTTPStatus.OK) -> None:
        data = json_bytes(payload)
        self.send_response(status)
        for key, value in JSON_HEADERS.items():
            self.send_header(key, value)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


class ReusableThreadingHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = True


def ensure_files() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not TODO_FILE.exists():
        write_json_file(
            TODO_FILE,
            [
                {
                    "id": str(uuid.uuid4()),
                    "title": "Configure Google Calendar iCal link",
                    "done": False,
                    "createdAt": now_utc(),
                },
                {
                    "id": str(uuid.uuid4()),
                    "title": "Install kiosk autostart on Raspberry Pi",
                    "done": False,
                    "createdAt": now_utc(),
                },
            ],
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Smart Room Dashboard server.")
    parser.add_argument("--host", default=os.environ.get("ROOM_DASHBOARD_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("ROOM_DASHBOARD_PORT", "8080")))
    return parser.parse_args()


def main() -> None:
    ensure_files()
    args = parse_args()
    server = ReusableThreadingHTTPServer((args.host, args.port), DashboardHandler)
    url_host = "localhost" if args.host in ("0.0.0.0", "127.0.0.1") else args.host
    print(f"Smart Room Dashboard running at http://{url_host}:{args.port}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Smart Room Dashboard...")
    finally:
        threading.Thread(target=server.shutdown, daemon=True).start()
        time.sleep(0.1)


if __name__ == "__main__":
    main()
