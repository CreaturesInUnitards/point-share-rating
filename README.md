# Point Share Rating (PSR)

An NFL team rating built on each team's share of the points in its games,
adjusted for schedule strength, recency, prior-season carryover, and
quarterback availability (EPA-based). 50 = league average; one rating
point ≈ 1.7 points of margin on a neutral field.

**The whole system is reproducible from this repo.** The weekly GitHub
Action pulls fresh results from [nflverse](https://github.com/nflverse),
recomputes every rating, and redeploys the site — no servers, no manual steps.

## Layout
- `pipeline/psr.py` — the rating engine (smoothing, opponent adjustment, decay, priors)
- `pipeline/qb_value.py` — per-QB value model (recency-weighted, shrunken EPA/play)
- `pipeline/build_site.py` — weekly build: ratings, decompositions, site, post graphics
- `site/` — the published static site (template + generated index.html)
- `post/` — generated graphics for the weekly newsletter
- `.github/workflows/weekly.yml` — Tuesday cron: build + deploy to GitHub Pages

## Run locally
    pip install -r pipeline/requirements.txt
    python pipeline/build_site.py            # downloads data, writes site/index.html
    open site/index.html

## Validation (all out-of-sample, 2004-2025)
- Beats raw point differential at margin prediction by +0.20 pts/game
  (p < 0.0001, season-clustered; won all 22 individual seasons)
- Winner-pick accuracy is statistically indistinguishable from point
  differential — margins are where the information is
- No against-the-spread edge: ~50% ATS over two decades, including on
  QB-change games (an apparent edge in 2022-25 died under pre-registered
  replication on 18 earlier seasons)

Setup note: in the repo settings, set Pages → Source → GitHub Actions.
