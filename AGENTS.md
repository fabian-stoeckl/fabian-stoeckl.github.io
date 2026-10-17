# Repository guide

- Begin every task by checking the current GitHub state (`git status`, `git fetch origin`, open PRs and workflows). Work on a separate branch and have changes reviewed through a pull request; never commit directly to `main`.
- The public homepage is the Jekyll site (`index.md`, `_layouts/default.html`, `assets/css/style.scss`, `_config.yml`). The private dashboard is static HTML under `Privat/`; its ETF dashboard and checked-in data are under `Privat/ETFs/`. Lowercase paths contain compatibility redirects.
- Install everything with `./scripts/setup.sh`. Build/check with `npm test`; run ETF checks separately with `npm run check:etf` and `npm run check:charts`.
- Preview with `./scripts/preview.sh`, then open `/`, `/Privat/`, and `/Privat/ETFs/`. With the preview running, check responsive pages and create screenshots using `npm run check:preview`.
- Never run `scripts/update_etf_data.py` merely to test a change: it downloads and rewrites financial data.

- For website changes, read and follow the “Fabians Website ändern” skill and `docs/website-context/README.md`, then the relevant topic note. Keep confirmed decisions and completed changes in that note. Missing history must be retrieved or marked as unknown.
