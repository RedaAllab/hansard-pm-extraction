# Phase 0 Scoping

Decisions locked before extraction begins. See `CLAUDE.md` for hypotheses (§2) and standing constraints (§9), and `PROJECT_SUMMARY.md` for the overall roadmap.

## Corpus cutoff

The cutoff date is not pre-fixed. It will be set to the most recent date available in the Hansard dataset at extraction time (Phase 1), and recorded in `data_README.md` as required by `CLAUDE.md` §9.

If Andy Burnham's contribution volume is too thin at extraction time for the stylometric analysis (H1), he will be excluded from the corpus initially, with the exclusion documented explicitly in `data_README.md`.

## PM tenure list

| PM | Party | Start | End |
|---|---|---|---|
| Boris Johnson | Conservative | 2019-07-24 | 2022-09-06 |
| Liz Truss | Conservative | 2022-09-06 | 2022-10-25 |
| Rishi Sunak | Conservative | 2022-10-25 | 2024-07-05 |
| Keir Starmer | Labour | 2024-07-05 | 2026-07-20 |
| Andy Burnham | Labour | 2026-07-20 | cutoff |

Andy Burnham was Mayor of Greater Manchester from 2017-05-08 until winning the 2026-06-18 Makerfield by-election, was elected Labour leader unopposed on 2026-07-17, and was appointed PM on 2026-07-20. Starmer remained PM in title until Burnham's appointment despite announcing his resignation on 2026-06-22.

These dates are a scoping-stage draft, sourced from the [French Wikipedia article on Andy Burnham](https://fr.wikipedia.org/wiki/Andy_Burnham). They will be re-resolved authoritatively via the Members API `governmentPosts` endpoint in Phase 1, per the temporal-join requirement in `CLAUDE.md` §9.

## Crisis windows

| Crisis | Start | End | Justification |
|---|---|---|---|
| Covid-19 | 2020-03-23 | 2021-07-19 | First national lockdown to legal end of restrictions in England ("Freedom Day") |
| Mini-budget | 2022-09-23 | 2022-10-17 | Kwarteng's mini-budget to its near-total reversal by Hunt |
| Invasion of Ukraine | 2022-02-24 | 2022-05-24 | Narrowed to the first three months to capture the initial rhetorical shock, rather than the full ongoing conflict |
| Labour leadership crisis | 2026-05-07 | 2026-07-20 | From the local election losses that triggered pressure on Starmer to Burnham's formal appointment as PM |

## H3 note

H3 (party interaction effect) is kept as originally stated in `CLAUDE.md` §2, despite a time imbalance between the two governing parties in the corpus (Conservative: ~5 years across 3 PMs; Labour: from mid-2024 across 2 PMs, one of them just started at cutoff). The resulting limit on statistical power for the interaction term will be noted explicitly in the Phase 7 write-up rather than addressed by reformulating the hypothesis now.

## Status

Phase 0 complete as of 2026-08-05. Proceeding to Phase 1 (extraction).
