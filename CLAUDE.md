# CLAUDE.md

Persistent project context for Claude Code. Read this file in full before starting any implementation work, and re-check it whenever a task touches architecture, data handling, or the boundary between "boilerplate" and "skill-building" work (see §9).

## 1. Project context and objectives

This project analyzes the rhetoric of UK Prime Ministers (2019–present) using UK Parliament Hansard speech data.

It is the third project in a personal NLP / data science portfolio, following two prior repositories (`hansard-extraction`, `hansard-2025-analysis`) that studied parliamentary framing of the trans-rights debate following the April 2025 *For Women Scotland Ltd v The Scottish Ministers* Supreme Court ruling. This project reuses and generalizes the pipeline architecture, tooling, and conventions developed there rather than starting from scratch.

Two goals guide every decision in this repo:
1. Produce a portfolio-worthy, publicly presentable project (GitHub, LinkedIn).
2. Deepen practical NLP competence — this is an active learning project, not just a delivery.

The author has a strong statistics/actuarial background (MSc in applied mathematics for finance and insurance) but limited prior NLP experience. Implementation choices should favor genuine skill-building over black-box automation in the phases flagged in §9.

## 2. Research question and hypotheses

**Central question:** How does the rhetoric of UK Prime Ministers differ by individual and shift around major exogenous crises, and does that shift depend on the governing party?

Formal hypotheses (same quasi-experimental logic as the prior trans-rights project — an exogenous rupture point plus testable, falsifiable claims):

- **H1 — Stylometric signature.** PMs are distinguishable via lexical/stylistic features; a supervised classifier can attribute an anonymized speech excerpt to the correct PM at a rate significantly above chance.
- **H2 — Crisis affect.** Negative sentiment and uncertainty/hedging markers increase significantly during defined crisis windows (Covid-19, the 2022 mini-budget, the invasion of Ukraine, the 2026 Labour leadership crisis) relative to baseline periods.
- **H3 — Party interaction.** The magnitude of that increase differs by governing party (Conservative vs. Labour), tested via an interaction term in regression — direct analogue of the prior project's H3.
- **H4 — Thematic drift (exploratory).** Dominant topics shift continuously over time with detectable breaks at PM transitions.

## 3. Functional scope

**In scope**
- Speeches by the sitting PM only: Johnson, Truss, Sunak, Starmer, Burnham — 2019 to a fixed corpus cutoff date (§9).
- Hansard debate contributions, tagged where possible by debate type (PMQs / "Engagements" vs. other debates).
- A layered NLP pipeline: lexical baseline → sentiment/affect → topic modeling → embeddings → supervised style classification → event-study statistics.
- An interactive dashboard exposing the above.

**Out of scope for v1**
- Non-PM speakers, opposition leaders, other ministers.
- Non-Hansard sources (social media, press coverage).
- Real-time/continuously updating deployment — v1 is a frozen corpus snapshot, refreshed only deliberately.

## 4. Technical architecture

Two-repository split, consistent with the prior project:

- **`hansard-pm-extraction`** — data acquisition. Async ingestion from the Hansard REST API (`hansard-api.parliament.uk`) and the Members API (PM tenure windows via `governmentPosts`). Produces a versioned parquet corpus.
- **`hansard-pm-nlp`** — analysis. Cleaning, NLP feature layers, topic modeling, embeddings, statistical modeling, and the dashboard app (`/app`).

Parquet is the interchange format between the two repos — typed, compressed, portable. DuckDB may be used internally within extraction for querying but is never the interchange format. Every parquet export ships with `data_README.md` (columns, types, row count, generation date, categorical values) and `schema.json` (for regression checks).

## 5. Technology stack

| Purpose | Tools |
|---|---|
| HTTP / retry | `httpx` (async), `tenacity` |
| Data storage | `pandas`, `pyarrow` (parquet), DuckDB (internal, extraction only) |
| NLP | `spaCy`, `gensim` (LDA), `bertopic`, `sentence-transformers` |
| ML / stats | `scikit-learn`, `statsmodels` |
| Quality | `pytest`, GitHub Actions |
| Dashboard | Streamlit |

## 6. Development conventions

- **Language:** all code, comments, docstrings, commit messages, and documentation in English — the dataset is English-language and the project targets an English-speaking open-source/portfolio audience.
- **Style:** PEP 8, type hints on all public functions, docstrings in a single consistent style (Google style recommended).
- **Structure:** one module per pipeline stage (ingestion, cleaning, features, modeling, viz). No monolithic scripts. Configuration (paths, date ranges, API parameters) is centralized, never hardcoded inline.
- **Notebooks** are for exploration only. Any logic that will be reused moves into a module and is imported — never copy-pasted from a notebook into production code.
- **Commits:** imperative mood, scoped, e.g. `extraction: add PM tenure resolution via Members API`.

## 7. Quality principles

- **Tests:** `pytest` for extraction logic (pagination, retry behavior, atomic writes) and for any function producing a derived feature or statistic used in the final analysis. Not everything needs a test — prioritize logic with silent-failure risk.
- **Modularity:** each NLP layer (sentiment, topics, embeddings, style features) is callable independently and testable in isolation.
- **Reproducibility:** fixed corpus cutoff date, pinned dependency versions, documented random seeds for any stochastic step (LDA, train/test splits, UMAP).
- **Maintainability:** prefer explicit over clever. A reader unfamiliar with the project should be able to follow the pipeline stage by stage from the README alone.

## 8. Portfolio objectives

- The repo should be self-explanatory to a technical recruiter within a few minutes: clear README, architecture diagram, example dashboard screenshots.
- Prioritize one thing done rigorously (e.g. the event-study statistical test, properly validated) over many things done superficially.
- The methodology must be auditable: hypotheses stated up front, decisions justified in `PROJECT_SUMMARY.md` and phase-level docs, not something a reader has to reverse-engineer from the code.

## 9. Constraints and things to always remember

Lessons carried over from the prior Hansard project — do not relearn these the hard way:

- Hansard API `PAGE_SIZE` must stay **≤ 100**; above roughly 100–140 it fails silently rather than raising an error.
- `asyncio.gather(...)` must always be called with `return_exceptions=True` — otherwise one failed chunk orphans the remaining tasks.
- Writes to disk must be atomic: write to a `.part` file, then `os.replace()`.
- PM/ministerial status is time-bound — any join between a speech's date and a PM's identity must be a **temporal join** against tenure windows, never a static lookup.
- CSV and raw DuckDB files are **not** acceptable interchange formats between the two repos (untyped/uncompressed, and engine-version-dependent, respectively). Parquet only.
- Claude Code should accelerate repetitive/boilerplate work — async scaffolding, retry logic, parquet I/O, test boilerplate — but should **not** silently generate the topic modeling, supervised classification, or event-study statistical modeling code end-to-end. These are the phases where the author is deliberately building skill; discuss the design and reasoning first, then implement.
- The corpus cutoff date is fixed and recorded in `data_README.md` at extraction time. Re-running the pipeline later to extend the corpus is a deliberate, documented action — never an automatic background refresh.
