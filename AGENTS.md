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

## Morgenzeitung Neu – current newspaper

The user-requested current paper is `Privat/Morgenzeitung-Neu/`. It preserves the classic newspaper interface and separates the editorial process into `services/morgenzeitung-neu/INTERESSEN.md` (qualitative interest-description learning) then `RECHERCHE.md` (long, high-quality independent journalism). Its only private feedback profile is `morgenzeitung-neu/` in `fabian-stoeckl/morgenzeitung-feedback`. Ratings have distinct issue prefixes, no numerical selection weights. Reuse the GitHub browser permission for issues and obtain separate Contents: Read permission for the private preferences display. `Privat/Pressespiegel/` and `Privat/Persoenliche-Zeitung/` remain readable archives. Never edit the ETF files or workflows for newspaper tasks. Current startup edition is explicitly preview/imported; do not pass it off as newly researched.

## Pressespiegel – historical predecessor

The current user-requested rebuild is `Privat/Pressespiegel/`, with exactly two editorial prompts in `services/pressespiegel/`: update a short natural-language interest description, then research and publish using it. Run them sequentially in one automatic daily task. There is no numerical ranking/learning engine in this product. `scripts/pressespiegel.py` only checks structure and prepares changed feedback for reading. Private description, change notes and feedback state live under `pressespiegel/` in `fabian-stoeckl/morgenzeitung-feedback`.

Keep `Privat/Persoenliche-Zeitung/` as a readable archive with its original IDs, feedback, source dossiers and tests. Do not execute its legacy editorial contract for the new Pressespiegel. The dashboard has three tiles: ETF, Pressespiegel, Website ändern. Preserve the existing skill link and ETF data.

For the new reader, run `python3 scripts/pressespiegel.py verify`, `python3 -m unittest discover -s tests/pressespiegel -v` and the mocked mobile/desktop `tests/pressespiegel-browser.cjs`. Test the old reader only when shared navigation or its files change. No publisher URL probes, quality claims from word count, simulated feedback or private comments in public files. Source accuracy is an editorial responsibility, not guaranteed by schema checks. Historical editions copied for preview must be visibly marked imported.
