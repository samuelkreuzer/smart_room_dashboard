# Contributing

Thank you for considering a contribution to Smart Room Dashboard.

This project is intentionally small, local-first, and Raspberry-Pi-friendly. Contributions should preserve that character unless there is a strong reason to change it.

## Development Principles

- Keep the default install dependency-free.
- Prefer Python standard-library solutions when they are maintainable.
- Keep private data out of the browser.
- Keep the UI useful in kiosk mode without requiring interaction.
- Treat integrations as optional and failure-tolerant.
- Avoid adding build tooling unless it clearly improves the project.

## Local Setup

```bash
git clone <repository-url>
cd room_dashboard
cp config.example.json config.json
cp data/todos.example.json data/todos.json
python3 dashboard.py
```

Open:

```text
http://localhost:8080
```

## Validation

Before opening a pull request, run:

```bash
python3 -m py_compile dashboard.py
python3 -m json.tool config.example.json >/dev/null
python3 -m json.tool data/todos.example.json >/dev/null
```

If you change the UI, verify the dashboard manually in a browser at 1920x1080 and at a smaller responsive width.

## Pull Requests

A good pull request includes:

- A focused description of the change.
- Notes on tested hardware or operating system when relevant.
- Screenshots for visible UI changes.
- Documentation updates for new configuration or behavior.

Avoid mixing unrelated refactors with feature work.

## Style

- Keep Python readable and explicit.
- Use concise comments only where they explain non-obvious behavior.
- Keep CSS class names descriptive.
- Avoid introducing secrets, tokens, private URLs, or personal data into committed files.
