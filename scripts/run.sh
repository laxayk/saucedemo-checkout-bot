#!/usr/bin/env bash
# One-command run: ./scripts/run.sh [standard_user|performance_glitch_user] [extra saucebot flags]
set -euo pipefail
cd "$(dirname "$0")/.."
export SAUCE_USERNAME="${1:-${SAUCE_USERNAME:-standard_user}}"
export SAUCE_PASSWORD="${SAUCE_PASSWORD:-secret_sauce}"  # public demo password printed on saucedemo.com
shift || true
python3 -m saucebot --input input.json --out outputs "$@"
