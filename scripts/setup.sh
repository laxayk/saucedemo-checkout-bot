#!/usr/bin/env bash
# Create a virtualenv, install dependencies and the Chromium browser.
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install --only-binary=:all: -r requirements.txt
.venv/bin/playwright install chromium
echo "Done. Activate with: source .venv/bin/activate"
