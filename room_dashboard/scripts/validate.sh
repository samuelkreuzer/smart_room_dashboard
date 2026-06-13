#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${PROJECT_DIR}"

python3 -m py_compile dashboard.py
python3 -m json.tool config.example.json >/dev/null
python3 -m json.tool data/todos.example.json >/dev/null

echo "Validation passed."
