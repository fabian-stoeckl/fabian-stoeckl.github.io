#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

bundle config set --local path vendor/bundle
bundle install
npm ci
npx playwright install --with-deps chromium

python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/pip install -r requirements-etf.txt

echo "Setup complete. Run: npm test"
