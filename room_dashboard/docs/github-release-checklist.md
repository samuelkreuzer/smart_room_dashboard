# GitHub Release Checklist

Use this checklist before publishing Smart Room Dashboard to GitHub.

## 1. Confirm Sensitive Files Are Ignored

These files should stay local:

```text
config.json
data/todos.json
.env
```

Check:

```bash
git check-ignore config.json data/todos.json
```

Expected output:

```text
config.json
data/todos.json
```

## 2. Validate the Project

```bash
python3 -m py_compile dashboard.py
python3 -m json.tool config.example.json >/dev/null
python3 -m json.tool data/todos.example.json >/dev/null
```

Optional local smoke test:

```bash
python3 dashboard.py
curl http://127.0.0.1:8080/api/health
```

## 3. Review Public Documentation

Confirm these files are accurate:

- `README.md`
- `docs/configuration.md`
- `docs/api.md`
- `docs/architecture.md`
- `docs/raspberry-pi-kiosk.md`
- `SECURITY.md`
- `CONTRIBUTING.md`
- `CHANGELOG.md`

## 4. Initialize Git

If this is not already a Git repository:

```bash
git init
git branch -M main
```

## 5. Inspect What Will Be Committed

```bash
git status --short
git add .
git status --short
```

Make sure `config.json` and `data/todos.json` are not staged.

## 6. Commit

```bash
git commit -m "Initial Smart Room Dashboard release"
```

## 7. Create the GitHub Repository

Create an empty repository on GitHub, then add the remote:

```bash
git remote add origin git@github.com:<user>/<repo>.git
```

or HTTPS:

```bash
git remote add origin https://github.com/<user>/<repo>.git
```

## 8. Push

```bash
git push -u origin main
```

## 9. Recommended Repository Settings

- Add description: `Modern Raspberry Pi smart room dashboard for kiosk displays.`
- Add topics: `raspberry-pi`, `dashboard`, `kiosk`, `smart-home`, `python`, `chromium`, `calendar`, `weather`
- Enable Issues if you want feedback.
- Enable Discussions only if you want community Q&A.
- Consider adding screenshots after the first public push.

## 10. Release Tag

```bash
git tag v1.0.0
git push origin v1.0.0
```

Then create a GitHub Release using the notes from `CHANGELOG.md`.
