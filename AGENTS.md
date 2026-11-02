# Repository guide

- Begin every task by checking the current GitHub state (`git status`, `git fetch origin`, open PRs and workflows). Work on a separate branch and have changes reviewed through a pull request; never commit directly to `main`.
- The public homepage is the Jekyll site (`index.md`, `_layouts/default.html`, `assets/css/style.scss`, `_config.yml`). The private dashboard is static HTML under `Privat/`; its ETF dashboard and checked-in data are under `Privat/ETFs/`. Lowercase paths contain compatibility redirects.
- Install everything with `./scripts/setup.sh`. Build/check with `npm test`; run ETF checks separately with `npm run check:etf` and `npm run check:charts`.
- Preview with `./scripts/preview.sh`, then open `/`, `/Privat/`, `/Privat/ETFs/`, and `/Privat/Pressespiegel/`. With the preview running, check responsive pages and create screenshots using `npm run check:preview`.
- Never run `scripts/update_etf_data.py` merely to test a change: it downloads and rewrites financial data.

## Repository context and safety

- The workflow is defined by the existing ChatGPT skill “Fabians Website ändern”. The canonical area registry is `docs/website-context/README.md`; protocols reside beside it. Do not keep independent protocol copies in the skill.
- Preserve unrelated work and financial data. Record the tested commit and use a PR; never bypass required checks or branch protection.
- Run `npm run context:update` after adding or renaming a protocol, then `npm run check:context`. Registry generation and validation discover areas dynamically from protocol metadata.
- `docs/` is excluded from Jekyll output. This repository is public: exclusions do not make repository documentation confidential. Do not commit secrets or private chat transcripts.

## Pressespiegel – sole active newspaper

The current (and only public) reader is `Privat/Pressespiegel/`. It shows **Heute wichtig**, **Vertiefungen**, and **Blogs**. There are no public legacy newspaper directories or redirect pages. Unused historical edition copies were removed from the active website; they remain recoverable from git history, not from current public paths. Do not merge them into the active edition index or treat them as new published research.

The current editorial contracts remain `services/morgenzeitung-neu/INTERESSEN.md`, `RECHERCHE.md`, and `README.md`. Their longstanding private GitHub feedback storage is `morgenzeitung-neu/` under `fabian-stoeckl/morgenzeitung-feedback`, using `MORGENZEITUNG_NEU_FEEDBACK_V1`; do not rename or mix historic V3 feedback. Retain stable article IDs, URLs, existing feedback and prior corrections. Never alter ETF resources for a newspaper task. Existing automation publishes only to `Privat/Pressespiegel/data/`, while the independent Noahpinion RSS sync writes to the `blogs-live` branch.

Validate with `python3 scripts/morgenzeitung_neu.py verify`, `python3 tests/morgenzeitung-neu-editorial.py`, `node tests/morgenzeitung-neu.test.cjs`, `node tests/morgenzeitung-neu-feedback.cjs`, and the mocked mobile/desktop browser workflow `tests/morgenzeitung-neu-browser.cjs`. Source truth and editorial quality require independent review; a green CI alone does not establish them.
