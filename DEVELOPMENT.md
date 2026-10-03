# Local development

## One-time setup

Requirements are Ruby with Bundler, Node.js/npm, Python 3 and a Chromium-compatible Linux environment. From the repository root run:

```sh
./scripts/setup.sh
```

This installs the GitHub Pages/Jekyll bundle in `vendor/bundle`, locked npm browser tooling in `node_modules`, Playwright Chromium, and the ETF Python packages in `.venv`. Re-running the script is safe. The Python environment exists for deliberate maintenance of the ETF updater; setup does **not** fetch or change financial data.

## Build and checks

```sh
npm test                 # ETF unit/browser regressions, then production Jekyll build
npm run check:etf        # ETF currency mathematics only
npm run check:charts     # ETF charts across six responsive widths
```

The build output is `_site/`. Development files, instructions, tests, dependencies, and generated preview artifacts are excluded from that output in `_config.yml`.

## Preview and responsive check

Start Jekyll in terminal 1:

```sh
./scripts/preview.sh
```

The main site is at <http://127.0.0.1:4000/>, the dashboard at <http://127.0.0.1:4000/Privat/>, and the ETF dashboard at <http://127.0.0.1:4000/Privat/ETFs/>. In terminal 2 run:

```sh
npm run check:preview
```

This checks all three pages at desktop (1440 px) and phone (390 px) widths for successful responses, browser errors, and horizontal overflow. It writes full-page PNGs to `artifacts/screenshots/`. Set `PREVIEW_URL` or `SCREENSHOT_DIR` to override either location.
