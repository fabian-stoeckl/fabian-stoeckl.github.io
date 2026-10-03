#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
exec bundle exec jekyll serve --host 0.0.0.0 --port "${PORT:-4000}" --livereload
