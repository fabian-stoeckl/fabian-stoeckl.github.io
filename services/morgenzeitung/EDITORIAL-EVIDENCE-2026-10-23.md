# Morgenzeitung: Editorial learning acceptance check (2026-10-23)

**Status: PARTIAL — retrospective comparison, not proof of editorial learning.** No private ratings or feedback text are published here.

The existing 2026-10-23 edition has 15 headlines and 10 in-depth articles. It covers industry/productivity (Mercedes), infrastructure/productivity (ÖBB), energy infrastructure (offshore wind), and AI/public finances (tax implications). This is thematically compatible with broad reader interests, **but does not prove feedback influenced selection**.

## Required next-edition test

1. **Before** composing a new edition, read the current private profile including `topic_evidence`. Privately record the profile commit and 2–5 prospective editorial choices; do not disclose personal feedback publicly.
2. Research real new articles in the correct time window, checking original source access and timestamps. Keep both editorial breadth and the personalized in-depth section.
3. Create a new dated JSON on a separate PR, run `scripts/check_morgenzeitung.py` and all relevant checks, secure required approval, merge, and verify public HTTPS readback.
4. **After** verified publication, privately create `runs/YYYY-MM-DD.json` with the research window, public commit, checks, applied evidence and concrete selection reasons. Update `last_successful_edition` only when S0–S7 have actually passed; read back both private files.
5. On any partial failure, retain the prior successful state. Never retroactively claim the 2026-10-23 edition used evidence collected later.

The deterministic feedback workflow computes and persists evidence, but does not itself generate an editorial edition or a private S7 audit. The end-to-end learning acceptance test remains open.
