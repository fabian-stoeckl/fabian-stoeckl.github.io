# Repository guide

- Begin every task by checking the current GitHub state (`git status`, `git fetch origin`, open PRs and workflows). Work on a separate branch and have changes reviewed through a pull request; never commit directly to `main`.
- The public homepage is the Jekyll site (`index.md`, `_layouts/default.html`, `assets/css/style.scss`, `_config.yml`). The private dashboard is static HTML under `Privat/`; its ETF dashboard and checked-in data are under `Privat/ETFs/`. Lowercase paths contain compatibility redirects.
- Install everything with `./scripts/setup.sh`. Build/check with `npm test`; run ETF checks separately with `npm run check:etf` and `npm run check:charts`.
- Preview with `./scripts/preview.sh`, then open `/`, `/Privat/`, `/Privat/ETFs/`, and `/Privat/Persoenliche-Zeitung/`. With the preview running, check responsive pages and create screenshots using `npm run check:preview`.
- Never run `scripts/update_etf_data.py` merely to test a change: it downloads and rewrites financial data.

## Repository context and safety

- The workflow is defined by the existing ChatGPT skill “Fabians Website ändern”. The canonical area registry is `docs/website-context/README.md`; protocols reside beside it. Do not keep independent protocol copies in the skill.
- Preserve unrelated work and financial data. Record the tested commit and use a PR; never bypass required checks or branch protection.
- Run `npm run context:update` after adding or renaming a protocol, then `npm run check:context`. Registry generation and validation discover areas dynamically from protocol metadata.
- `docs/` is excluded from Jekyll output. This repository is public: exclusions do not make repository documentation confidential. Do not commit secrets or private chat transcripts.

## Persönliche Zeitung editorial protocol

Only Persönliche Zeitung remains active (technical path: Persoenliche-Zeitung). Its authoritative, short contract is `services/morgenzeitung-v3/REDAKTION.md`, its private learning profile is `morgenzeitung-v3/profile.json` in the private feedback repository. Reader scripts and CSS are local to `Privat/Persoenliche-Zeitung/`; never import removed Pressespiegel or Morgenzeitung-neu directories. Preserve the existing V3 privacy rules, original factual evidence and feedback. Run only V3 tests, not old legacy process tests.

- The old `/Privat/Morgenzeitung-3/` path contains only three HTML bookmark redirects. Do not restore publication data there; keep the new `/Privat/Persoenliche-Zeitung/` as the sole production location. Feedback issue IDs and private repository remain unchanged.
