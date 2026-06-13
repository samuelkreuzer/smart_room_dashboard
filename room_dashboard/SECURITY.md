# Security Policy

## Supported Versions

The current `main` branch is the supported version.

## Sensitive Local Files

The following files may contain private information and are ignored by Git:

- `config.json`
- `data/todos.json`

`config.json` can contain private Google Calendar iCal URLs. Treat those URLs like passwords. Anyone with a private iCal URL can read the corresponding calendar feed.

## Network Exposure

By default, the dashboard server binds to:

```text
127.0.0.1:8080
```

That is the recommended mode for Raspberry Pi kiosk usage.

Only bind to `0.0.0.0` when you intentionally want other devices on the local network to access the dashboard:

```bash
python3 dashboard.py --host 0.0.0.0 --port 8080
```

Do not expose this dashboard directly to the public internet.

## Reporting Vulnerabilities

If you discover a security issue, please avoid opening a public issue with exploit details. Use the repository owner's preferred private contact method, or open a minimal issue asking for a secure contact path.

Please include:

- Affected version or commit.
- Clear reproduction steps.
- Impact assessment.
- Suggested mitigation if known.

## Operational Guidance

- Keep Raspberry Pi OS updated.
- Keep Chromium updated.
- Avoid storing API tokens in frontend files.
- Review `config.json` before sharing logs, screenshots, or backups.
- Rotate private iCal URLs in Google Calendar if they are accidentally committed or shared.
