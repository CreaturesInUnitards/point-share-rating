"""Point Share Rating (PSR) — an opponent- and recency-adjusted NFL team rating.

Base stat: a team's share of total points in a game, on a 0-100 scale
(50 = average). Layers, in order:

  1. Smoothing:   PSR = (PF + k) / (PF + PA + 2k) * 100      [k = 14]
                  tames shutouts / low-scoring blowouts
  2. Opponent adjustment (iterative, SRS-style):
                  AdjPSR = GamePSR + (OppRating - 50)
  3. Recency:     weight = 0.5 ** (games_back / half_life)    [half_life = 12]
  4. Shrinkage toward a team-specific prior with m phantom games [m = 8]
     Prior = 50 + carry * (last season's final rating - 50)   [carry = 0.3]

  5. QB availability (prediction-time): if a team starts a QB other than
     its recent primary starter, subtract BACKUP_QB_PENALTY points.

Backtested 2022-2025 (walk-forward, weeks 5-18, coefficients fit on 2015-2021):
  straight-up winners 65.0% | margin MAE 9.89 | corr w/ Vegas spread 0.870
  (Vegas closing line itself: 69.0% / 9.41)
"""

import numpy as np
import pandas as pd

DEFAULTS = dict(k=14.0, half_life=12.0, m=8.0, carry=0.3)


def smoothed_psr(pf, pa, k):
    return (pf + k) / (pf + pa + 2 * k) * 100.0


def compute_ratings(games, prior=None, k=14.0, half_life=12.0, m=8.0,
                    n_iter=25, adjust=True):
    """Rate teams from a long-format game table.

    games: DataFrame with columns team, opp, pf, pa, order
           (two rows per game, one per perspective; order ascending in time)
    prior: dict team -> prior rating (default: flat 50)
    """
    lam = 0.5 ** (1.0 / half_life) if np.isfinite(half_life) else 1.0
    df = games.copy()
    df["psr"] = smoothed_psr(df["pf"].astype(float), df["pa"].astype(float), k)
    df = df.sort_values("order")
    df["gb"] = df.groupby("team").cumcount(ascending=False)
    df["w"] = lam ** df["gb"]

    teams = df["team"].unique()
    prior = prior or {}
    prior = {t: prior.get(t, 50.0) for t in teams}
    ratings = dict(prior)

    for _ in range(n_iter if adjust else 1):
        opp_r = df["opp"].map(ratings).fillna(50.0)
        adj = df["psr"] + (opp_r - 50.0) if adjust else df["psr"]
        tmp = pd.DataFrame({"team": df["team"], "wa": df["w"] * adj, "w": df["w"]})
        agg = tmp.groupby("team").sum()
        new = (agg["wa"] + m * agg.index.map(prior)) / (agg["w"] + m)
        ratings = {t: 0.5 * ratings[t] + 0.5 * new[t] for t in agg.index}
    return ratings


def to_long(season_games):
    """Wide schedule (home_team, away_team, home_score, away_score, week)
    -> long format for compute_ratings."""
    h = season_games.rename(columns={"home_team": "team", "away_team": "opp",
                                     "home_score": "pf", "away_score": "pa"})
    a = season_games.rename(columns={"away_team": "team", "home_team": "opp",
                                     "away_score": "pf", "home_score": "pa"})
    cols = ["team", "opp", "pf", "pa", "week"]
    long = pd.concat([h[cols], a[cols]], ignore_index=True)
    long["order"] = long["week"]
    return long


def season_ratings(sched, first_season=None, **params):
    """Chain seasons: each season's prior = regressed previous final ratings.
    sched: wide schedule with a `season` column. Returns {season: {team: rating}}."""
    p = {**DEFAULTS, **params}
    carry = p.pop("carry")
    out, prev = {}, {}
    for season in sorted(sched["season"].unique()):
        if first_season and season < first_season:
            continue
        prior = {t: 50 + carry * (prev.get(t, 50) - 50)
                 for t in pd.concat([sched["home_team"], sched["away_team"]]).unique()}
        long = to_long(sched[sched["season"] == season])
        out[season] = compute_ratings(long, prior=prior, **p)
        prev = out[season]
    return out




# ---- QB availability layer ------------------------------------------------

PTS_PER_PSR = 1.71
HFA_PTS = 1.70
BACKUP_QB_PENALTY = 4.21   # points; fit on 2015-2021


def backup_flags(starts):
    """starts: DataFrame with columns team, season, week, qb (one row per
    team-game, ascending in time). Returns dict (team, season, week) -> 0/1:
    1 if that game's starter differed from the team's primary QB at the time
    (mode of the season's prior starts, last 8; needs >= 2 prior games)."""
    flags = {}
    for (team, season), g in starts.groupby(["team", "season"]):
        hist = []
        for _, row in g.sort_values("week").iterrows():
            if len(hist) >= 2:
                mode = pd.Series(hist[-8:]).mode().iloc[0]
                flags[(team, season, row["week"])] = int(row["qb"] != mode)
            else:
                flags[(team, season, row["week"])] = 0
            hist.append(row["qb"])
    return flags


def predict_margin_qb(rating_home, rating_away, home_backup=0, away_backup=0):
    """Expected home margin in points, including QB availability."""
    return (PTS_PER_PSR * (rating_home - rating_away) + HFA_PTS
            - BACKUP_QB_PENALTY * (home_backup - away_backup))
