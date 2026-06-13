const state = {
  config: {
    title: "Smart Room Dashboard",
    subtitle: "Home status, schedule, tasks, music and news",
    timezone: "",
    refresh: {}
  },
  todos: []
};

const $ = (selector) => document.querySelector(selector);

const elements = {
  title: $("#dashboard-title"),
  subtitle: $("#dashboard-subtitle"),
  clockTime: $("#clock-time"),
  clockDate: $("#clock-date"),
  quickTemperature: $("#quick-temperature"),
  quickCondition: $("#quick-condition"),
  quickOnline: $("#quick-online"),
  quickNetwork: $("#quick-network"),
  quickMusicStatus: $("#quick-music-status"),
  quickMusicTitle: $("#quick-music-title"),
  quickEventTime: $("#quick-event-time"),
  quickEventTitle: $("#quick-event-title"),
  weatherLocation: $("#weather-location"),
  weatherUpdated: $("#weather-updated"),
  weatherIcon: $("#weather-icon"),
  weatherCondition: $("#weather-condition"),
  weatherTemp: $("#weather-temp"),
  weatherFeels: $("#weather-feels"),
  weatherHumidity: $("#weather-humidity"),
  weatherWind: $("#weather-wind"),
  weatherRain: $("#weather-rain"),
  forecastList: $("#forecast-list"),
  calendarUpdated: $("#calendar-updated"),
  calendarList: $("#calendar-list"),
  todoForm: $("#todo-form"),
  todoInput: $("#todo-input"),
  todoCount: $("#todo-count"),
  todoList: $("#todo-list"),
  musicUpdated: $("#music-updated"),
  musicStatus: $("#music-status"),
  musicTitle: $("#music-title"),
  musicArtist: $("#music-artist"),
  musicProgress: $("#music-progress"),
  networkUpdated: $("#network-updated"),
  networkHostname: $("#network-hostname"),
  networkIp: $("#network-ip"),
  networkSsid: $("#network-ssid"),
  networkOnline: $("#network-online"),
  rssUpdated: $("#rss-updated"),
  rssList: $("#rss-list")
};

async function fetchJson(url, options = {}) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options
  });
  const payload = await response.json();
  if (!response.ok || payload.ok === false) {
    throw new Error(payload.error || `Request failed: ${response.status}`);
  }
  return payload.data;
}

function interval(name, fallbackSeconds) {
  return Math.max(5, Number(state.config.refresh?.[name] || fallbackSeconds)) * 1000;
}

function formatNumber(value, suffix = "") {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return `--${suffix}`;
  }
  return `${Math.round(Number(value))}${suffix}`;
}

function formatTime(value) {
  if (!value) return "--:--";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "--:--";
  return new Intl.DateTimeFormat("en-GB", {
    hour: "2-digit",
    minute: "2-digit",
    timeZone: state.config.timezone || undefined
  }).format(date);
}

function formatDay(value, style = "short") {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Unknown";
  return new Intl.DateTimeFormat("en-GB", {
    weekday: style,
    day: "2-digit",
    month: "short",
    timeZone: state.config.timezone || undefined
  }).format(date);
}

function updateFreshness(element) {
  element.textContent = `Updated ${new Intl.DateTimeFormat("en-GB", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit"
  }).format(new Date())}`;
}

function setError(container, message) {
  container.replaceChildren(createStateNode(message, "error-state"));
}

function setEmpty(container, message) {
  container.replaceChildren(createStateNode(message, "empty-state"));
}

function createStateNode(message, className) {
  const node = document.createElement("div");
  node.className = className;
  node.textContent = message;
  return node;
}

function updateClock() {
  const now = new Date();
  elements.clockTime.textContent = new Intl.DateTimeFormat("en-GB", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    timeZone: state.config.timezone || undefined
  }).format(now);
  elements.clockDate.textContent = new Intl.DateTimeFormat("en-GB", {
    weekday: "long",
    day: "2-digit",
    month: "long",
    year: "numeric",
    timeZone: state.config.timezone || undefined
  }).format(now);
}

async function loadConfig() {
  try {
    const config = await fetchJson("/api/config");
    state.config = { ...state.config, ...config };
    document.title = state.config.title;
    elements.title.textContent = state.config.title;
    elements.subtitle.textContent = state.config.subtitle;
  } catch (error) {
    elements.subtitle.textContent = `Config error: ${error.message}`;
  }
}

async function refreshWeather() {
  try {
    const weather = await fetchJson("/api/weather");
    if (weather.setupRequired) {
      elements.quickTemperature.textContent = "-- C";
      elements.quickCondition.textContent = weather.message;
      setEmpty(elements.forecastList, weather.message);
      return;
    }

    const current = weather.current || {};
    const condition = current.condition || {};
    const temp = formatNumber(current.temperature, " C");

    elements.weatherLocation.textContent = weather.locationName || "Configured location";
    elements.weatherTemp.textContent = temp;
    elements.quickTemperature.textContent = temp;
    elements.weatherCondition.textContent = condition.label || "Weather available";
    elements.quickCondition.textContent = condition.label || "Weather available";
    elements.weatherIcon.className = `weather-symbol ${condition.icon || "cloud"}`;
    elements.weatherIcon.textContent = String(condition.icon || "cloud").toUpperCase();
    elements.weatherFeels.textContent = formatNumber(current.feelsLike, " C");
    elements.weatherHumidity.textContent = formatNumber(current.humidity, "%");
    elements.weatherWind.textContent = formatNumber(current.windSpeed, " km/h");
    elements.weatherRain.textContent = formatNumber(current.precipitation, " mm");

    renderForecast(weather.forecast || []);
    updateFreshness(elements.weatherUpdated);
  } catch (error) {
    setError(elements.forecastList, error.message);
  }
}

function renderForecast(forecast) {
  if (!forecast.length) {
    setEmpty(elements.forecastList, "No forecast returned.");
    return;
  }

  const nodes = forecast.map((day) => {
    const row = document.createElement("div");
    row.className = "forecast-item";

    const copy = document.createElement("div");
    const dayName = document.createElement("strong");
    dayName.textContent = formatDay(day.date);
    const condition = document.createElement("span");
    condition.textContent = day.condition?.label || "Forecast";
    copy.append(dayName, condition);

    const temp = document.createElement("span");
    temp.className = "forecast-temp";
    temp.textContent = `${formatNumber(day.temperatureMin, " C")} / ${formatNumber(day.temperatureMax, " C")}`;

    row.append(copy, temp);
    return row;
  });
  elements.forecastList.replaceChildren(...nodes);
}

async function refreshCalendar() {
  try {
    const calendar = await fetchJson("/api/calendar");
    const events = calendar.events || [];
    if (calendar.setupRequired) {
      elements.quickEventTime.textContent = "Setup";
      elements.quickEventTitle.textContent = "Calendar iCal URL missing";
      setEmpty(elements.calendarList, calendar.message);
      return;
    }
    renderCalendar(events, calendar.errors || []);
    updateFreshness(elements.calendarUpdated);
  } catch (error) {
    setError(elements.calendarList, error.message);
  }
}

function renderCalendar(events, errors) {
  if (!events.length) {
    const message = errors.length ? errors.join(" | ") : "No upcoming events.";
    elements.quickEventTime.textContent = "No event";
    elements.quickEventTitle.textContent = message;
    setEmpty(elements.calendarList, message);
    return;
  }

  const first = events[0];
  elements.quickEventTime.textContent = first.allDay ? formatDay(first.start) : formatTime(first.start);
  elements.quickEventTitle.textContent = first.title;

  const nodes = events.map((event) => {
    const row = document.createElement("div");
    row.className = "event-item";

    const color = document.createElement("span");
    color.className = "event-color";
    color.style.background = event.color || "#5eead4";

    const copy = document.createElement("div");
    const title = document.createElement("span");
    title.className = "event-title";
    title.textContent = event.title || "Untitled event";
    const meta = document.createElement("span");
    meta.className = "event-meta";
    const when = event.allDay ? formatDay(event.start, "long") : `${formatDay(event.start)} at ${formatTime(event.start)}`;
    meta.textContent = [when, event.location, event.calendar].filter(Boolean).join(" - ");
    copy.append(title, meta);

    row.append(color, copy);
    return row;
  });
  elements.calendarList.replaceChildren(...nodes);
}

async function refreshTodos() {
  try {
    state.todos = await fetchJson("/api/todos");
    renderTodos();
  } catch (error) {
    setError(elements.todoList, error.message);
  }
}

function renderTodos() {
  const openCount = state.todos.filter((todo) => !todo.done).length;
  elements.todoCount.textContent = `${openCount} open`;

  if (!state.todos.length) {
    setEmpty(elements.todoList, "No tasks yet.");
    return;
  }

  const nodes = state.todos.map((todo) => {
    const row = document.createElement("label");
    row.className = `todo-item ${todo.done ? "done" : ""}`;

    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.checked = todo.done;
    checkbox.addEventListener("change", () => toggleTodo(todo.id, checkbox.checked));

    const title = document.createElement("span");
    title.className = "todo-title";
    title.textContent = todo.title;

    const remove = document.createElement("button");
    remove.className = "icon-button";
    remove.type = "button";
    remove.title = "Delete task";
    remove.setAttribute("aria-label", `Delete task: ${todo.title}`);
    remove.textContent = "x";
    remove.addEventListener("click", (event) => {
      event.preventDefault();
      deleteTodo(todo.id);
    });

    row.append(checkbox, title, remove);
    return row;
  });
  elements.todoList.replaceChildren(...nodes);
}

async function saveTodos() {
  state.todos = await fetchJson("/api/todos", {
    method: "PUT",
    body: JSON.stringify(state.todos)
  });
  renderTodos();
}

async function toggleTodo(id, done) {
  state.todos = state.todos.map((todo) => (todo.id === id ? { ...todo, done } : todo));
  renderTodos();
  await saveTodos();
}

async function deleteTodo(id) {
  state.todos = await fetchJson(`/api/todos/${encodeURIComponent(id)}`, { method: "DELETE" });
  renderTodos();
}

async function addTodo(title) {
  state.todos = await fetchJson("/api/todos", {
    method: "POST",
    body: JSON.stringify({ title })
  });
  renderTodos();
}

async function refreshStatus() {
  try {
    const status = await fetchJson("/api/status");
    renderNetwork(status.network || {});
    renderMusic(status.music || {});
  } catch (error) {
    elements.quickOnline.textContent = "Error";
    elements.quickNetwork.textContent = error.message;
  }
}

function renderNetwork(network) {
  elements.networkHostname.textContent = network.hostname || "--";
  elements.networkIp.textContent = network.localIp || "--";
  elements.networkSsid.textContent = cleanSsid(network.ssid) || "--";
  elements.networkOnline.textContent = network.online ? "Online" : "Offline";
  elements.networkOnline.style.color = network.online ? "var(--green)" : "var(--red)";
  elements.quickOnline.textContent = network.online ? "Online" : "Offline";
  elements.quickNetwork.textContent = network.localIp ? `${network.localIp} on ${cleanSsid(network.ssid) || "LAN"}` : "No local IP detected";
  updateFreshness(elements.networkUpdated);
}

function cleanSsid(value) {
  if (!value) return "";
  if (String(value).includes(":")) {
    const active = String(value)
      .split("\n")
      .find((line) => line.startsWith("yes:"));
    return active ? active.replace("yes:", "").trim() : "";
  }
  return String(value).trim();
}

function renderMusic(music) {
  if (music.enabled === false) {
    elements.musicStatus.textContent = "Disabled";
    elements.musicTitle.textContent = "Music integration disabled";
    elements.musicArtist.textContent = "Enable it in config.json.";
    elements.quickMusicStatus.textContent = "Disabled";
    elements.quickMusicTitle.textContent = "Music integration disabled";
    elements.musicProgress.style.width = "0%";
    return;
  }

  if (!music.available) {
    elements.musicStatus.textContent = "Unavailable";
    elements.musicTitle.textContent = "No playerctl data";
    elements.musicArtist.textContent = music.message || "No active player detected.";
    elements.quickMusicStatus.textContent = "Idle";
    elements.quickMusicTitle.textContent = "No media player";
    elements.musicProgress.style.width = "0%";
    updateFreshness(elements.musicUpdated);
    return;
  }

  elements.musicStatus.textContent = music.status || "Unknown";
  elements.musicTitle.textContent = music.title || "Untitled track";
  elements.musicArtist.textContent = [music.artist, music.album].filter(Boolean).join(" - ") || "Unknown artist";
  elements.quickMusicStatus.textContent = music.status || "Playing";
  elements.quickMusicTitle.textContent = music.title || "Untitled track";

  const progress = music.duration ? Math.min(100, Math.round((Number(music.position || 0) / Number(music.duration)) * 100)) : 0;
  elements.musicProgress.style.width = `${progress}%`;
  updateFreshness(elements.musicUpdated);
}

async function refreshRss() {
  try {
    const rss = await fetchJson("/api/rss");
    if (rss.setupRequired) {
      setEmpty(elements.rssList, rss.message);
      return;
    }
    renderRss(rss.items || [], rss.errors || []);
    updateFreshness(elements.rssUpdated);
  } catch (error) {
    setError(elements.rssList, error.message);
  }
}

function renderRss(items, errors) {
  if (!items.length) {
    setEmpty(elements.rssList, errors.length ? errors.join(" | ") : "No RSS items available.");
    return;
  }

  const nodes = items.map((item) => {
    const row = document.createElement("article");
    row.className = "news-item";

    const title = document.createElement(item.link ? "a" : "span");
    title.className = "news-title";
    title.textContent = item.title || "Untitled item";
    if (item.link) {
      title.href = item.link;
      title.target = "_blank";
      title.rel = "noreferrer";
    }

    const meta = document.createElement("span");
    meta.className = "news-meta";
    meta.textContent = [item.source, item.publishedAt ? formatDay(item.publishedAt) : ""].filter(Boolean).join(" - ");

    row.append(title, meta);
    return row;
  });
  elements.rssList.replaceChildren(...nodes);
}

function bindEvents() {
  elements.todoForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const title = elements.todoInput.value.trim();
    if (!title) return;
    elements.todoInput.value = "";
    await addTodo(title);
  });
}

async function start() {
  bindEvents();
  await loadConfig();
  updateClock();
  setInterval(updateClock, 1000);

  refreshWeather();
  refreshCalendar();
  refreshTodos();
  refreshStatus();
  refreshRss();

  setInterval(refreshWeather, interval("weatherSeconds", 900));
  setInterval(refreshCalendar, interval("calendarSeconds", 300));
  setInterval(refreshTodos, interval("todoSeconds", 60));
  setInterval(refreshStatus, interval("statusSeconds", 10));
  setInterval(refreshRss, interval("rssSeconds", 900));
}

start();
