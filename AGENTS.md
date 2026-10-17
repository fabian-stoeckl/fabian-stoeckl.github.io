# Repository guide

- Begin every task by checking the current GitHub state (`git status`, `git fetch origin`, open PRs and workflows). Work on a separate branch and have changes reviewed through a pull request; never commit directly to `main`.
- The public homepage is the Jekyll site (`index.md`, `_layouts/default.html`, `assets/css/style.scss`, `_config.yml`). The private dashboard is static HTML under `Privat/`; its ETF dashboard and checked-in data are under `Privat/ETFs/`. Lowercase paths contain compatibility redirects.
- Install everything with `./scripts/setup.sh`. Build/check with `npm test`; run ETF checks separately with `npm run check:etf` and `npm run check:charts`.
- Preview with `./scripts/preview.sh`, then open `/`, `/Privat/`, and `/Privat/ETFs/`. With the preview running, check responsive pages and create screenshots using `npm run check:preview`.
- Never run `scripts/update_etf_data.py` merely to test a change: it downloads and rewrites financial data.

## Website area protocols and release workflow

- **Before any website-edit task:** use `docs/website-context/README.md` to identify the correct area protocol (`Allgemeine-Website.md`, `ETF.md` or `Pressespiegel.md`). Ask which area to edit if it is not specified; read the area protocol and confirm its latest documented state before proposing changes. Do not invent a sample change.
- Compare the protocol with the live `main` branch, open PRs and workflow status. Treat the repo as authoritative if a protocol is outdated; update it.
- Use the agreed sequence: **separate branch/PR → relevant desktop/mobile preview → explicit user approval → full tests → merge/publish → production check**. Record approval and checks in the PR; do not imply that tests or deployment passed before verification.
- **Update the area protocol in the same PR** as every relevant change (decision, files, checks, commit, approval, deployment, remaining work). Add and index a new protocol when a new area is created.
- `docs/` is internal repository documentation and excluded from the published Jekyll site. The ChatGPT skill is managed separately; these files do not themselves alter skill settings.
