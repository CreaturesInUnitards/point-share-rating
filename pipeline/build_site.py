"""Weekly build: compute PSR ratings + decomposition, emit site/index.html and post graphics.

Usage: python build_site.py [--season 2025] [--games PATH] [--qbdir PATH]
Downloads nflverse data when paths aren't supplied (CI mode).
"""
import argparse, json, os, sys, urllib.request, warnings, bisect
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
from psr import compute_ratings, to_long, smoothed_psr
from qb_value import ALIASES, qb_values_before

K, HL, M, CARRY = 14, 12, 8, 0.3
QB_HL, QB_M, REPL, LEAGUE, PPG = 16, 150, -0.048, 0.045, 38
LAM = 0.5 ** (1.0 / HL)
GAMES_URL = "https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv"
QB_URL = "https://github.com/nflverse/nflverse-data/releases/download/stats_player/stats_player_week_{y}.csv.gz"
TEAMS = {"ARI":"Cardinals","ATL":"Falcons","BAL":"Ravens","BUF":"Bills","CAR":"Panthers","CHI":"Bears",
"CIN":"Bengals","CLE":"Browns","DAL":"Cowboys","DEN":"Broncos","DET":"Lions","GB":"Packers","HOU":"Texans",
"IND":"Colts","JAX":"Jaguars","KC":"Chiefs","LA":"Rams","LAC":"Chargers","LV":"Raiders","MIA":"Dolphins",
"MIN":"Vikings","NE":"Patriots","NO":"Saints","NYG":"Giants","NYJ":"Jets","PHI":"Eagles","PIT":"Steelers",
"SEA":"Seahawks","SF":"49ers","TB":"Buccaneers","TEN":"Titans","WAS":"Commanders"}


def fetch(url, path):
    if not os.path.exists(path):
        urllib.request.urlretrieve(url, path)
    return path


def ordinal(n):
    return f"{n}{'th' if 10 <= n % 100 <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--season", type=int, default=None)
    ap.add_argument("--games", default=None)
    ap.add_argument("--qbdir", default=None)
    a = ap.parse_args()

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cache = os.path.join(root, ".cache"); os.makedirs(cache, exist_ok=True)
    gpath = a.games or fetch(GAMES_URL, os.path.join(cache, "games.csv"))
    g = pd.read_csv(gpath, low_memory=False)
    g = g[(g.game_type == "REG") & g.result.notna()]
    season = a.season or int(g.season.max())
    g = g[(g.season >= season - 3) & (g.season <= season)]
    for c in ["home_qb_name", "away_qb_name"]:
        g[c] = g[c].replace(ALIASES)

    qbdir = a.qbdir or cache
    frames = []
    for y in range(season - 3, season + 1):
        p = os.path.join(qbdir, f"ps{y}.csv.gz")
        if not os.path.exists(p):
            fetch(QB_URL.format(y=y), p)
        d = pd.read_csv(p, low_memory=False)
        d = d[(d.position == "QB") & (d.season_type == "REG")].copy()
        d["plays"] = d.attempts.fillna(0) + d.sacks_suffered.fillna(0) + d.carries.fillna(0)
        d["epa"] = d.passing_epa.fillna(0) + d.rushing_epa.fillna(0)
        frames.append(d[["player_display_name", "season", "week", "plays", "epa"]]
                      .rename(columns={"player_display_name": "qb"}))
    qbw = pd.concat(frames)
    qbw = qbw[qbw.plays > 0].sort_values(["season", "week"]).reset_index(drop=True)
    qbw["value"] = qb_values_before(qbw, QB_HL, QB_M, REPL)
    qlook = {}
    for q, gg in qbw.groupby("qb"):
        gg = gg.sort_values(["season", "week"])
        qlook[q] = (list(gg.season * 100 + gg.week), list(gg.value))

    def sval(qb, s, w):
        if qb not in qlook:
            return REPL
        ts, vs = qlook[qb]; t = s * 100 + w
        j = bisect.bisect_left(ts, t)
        if j < len(ts) and ts[j] == t:
            return vs[j]
        return vs[j - 1] if j > 0 else REPL

    # season chain for the prior
    prev = {}
    for s in sorted(g.season.unique()):
        if s == season:
            break
        long = to_long(g[g.season == s])
        prior = {t: 50 + CARRY * (prev.get(t, 50) - 50) for t in set(long.team)}
        prev = compute_ratings(long, prior=prior, k=K, half_life=HL, m=M)

    sg = g[g.season == season].sort_values("week")
    long = to_long(sg)
    prior = {t: 50 + CARRY * (prev.get(t, 50) - 50) for t in set(long.team)}
    weeks = sorted(sg.week.unique())
    week_now = weeks[-1]
    traj = {t: [] for t in set(long.team)}
    for w in weeks:
        r = compute_ratings(long[long.week <= w], prior=prior, k=K, half_life=HL, m=M)
        for t in traj:
            traj[t].append(round(r.get(t, prior[t]), 2))
    final = compute_ratings(long, prior=prior, k=K, half_life=HL, m=M)
    prev_final = compute_ratings(
        long[long.week <= (weeks[-2] if len(weeks) > 1 else weeks[-1])],
        prior=prior, k=K, half_life=HL, m=M)

    # decomposition per team (sums exactly to the final rating)
    long = long.sort_values("order")
    long["psr"] = smoothed_psr(long.pf.astype(float), long.pa.astype(float), K)
    long["gb"] = long.groupby("team").cumcount(ascending=False)
    long["w"] = LAM ** long["gb"]
    rows = []
    starters = {}
    for _, gm in sg.iterrows():
        starters[gm.home_team] = gm.home_qb_name
        starters[gm.away_team] = gm.away_qb_name
    sched_vals = {}
    for t, d in long.groupby("team"):
        raw = d.psr.mean()
        rec = np.average(d.psr, weights=d.w) - raw
        adj = d.psr + (d.opp.map(final) - 50)
        sch = np.average(adj, weights=d.w) - np.average(d.psr, weights=d.w)
        sched_vals[t] = sch
        pri = final[t] - (raw + rec + sch)
        last8 = d.sort_values("order").tail(8)
        w8, l8 = (last8.pf > last8.pa).sum(), (last8.pf < last8.pa).sum()
        rows.append(dict(team=t, raw=raw, rec=rec, sch=sch, pri=pri,
                         last8=f"{w8}\u2013{l8}", n=len(d)))
    sched_rank = {t: r + 1 for r, t in enumerate(
        sorted(sched_vals, key=lambda x: -sched_vals[x]))}

    out = []
    for r in rows:
        t = r["team"]
        qb = starters.get(t, "")
        qv = sval(qb, season, week_now)
        out.append({
            "team": t, "name": TEAMS.get(t, t),
            "rating": round(final[t], 1),
            "delta": round(final[t] - prev_final.get(t, final[t]), 1),
            "raw": round(r["raw"], 1),
            "recency": round(r["rec"], 1), "recencyNote": f"{r['last8']} last eight",
            "schedule": round(r["sch"], 1),
            "scheduleNote": f"{ordinal(sched_rank[t])}-hardest slate",
            "prior": round(r["pri"], 1),
            "priorNote": f"was {round(prev.get(t, 50), 1)} in '{str(season - 1)[2:]}",
            "games": r["n"], "qb": qb,
            "qbPts": round((qv - LEAGUE) * PPG, 1),
            "traj": traj[t],
        })
    out.sort(key=lambda x: -x["rating"])
    data = {"season": season, "week": int(week_now), "teams": out,
            "built": pd.Timestamp.utcnow().strftime("%Y-%m-%d")}

    site = os.path.join(root, "site")
    with open(os.path.join(site, "data", "ratings.json"), "w") as f:
        json.dump(data, f)
    tpl = open(os.path.join(site, "template.html")).read()
    html = tpl.replace("/*__PSR_DATA__*/", "window.PSR_DATA=" + json.dumps(data))
    open(os.path.join(site, "index.html"), "w").write(html)
    print(f"built site for {season} week {week_now}: {len(out)} teams")

    # Substack top-10 graphic
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        top = out[:10]
        fig, ax = plt.subplots(figsize=(7, 5.2), dpi=200)
        ax.axis("off")
        ax.text(0, 1.02, "Point Share Ratings — top 10", fontsize=15, weight="bold")
        ax.text(0, 0.97, f"{season} season, week {week_now} · 50 = league average",
                fontsize=9, color="#666")
        for i, tm in enumerate(top):
            y = 0.88 - i * 0.088
            ax.text(0.00, y, f"{i + 1}", fontsize=10, color="#888")
            ax.text(0.06, y, tm["name"], fontsize=11)
            ax.barh(y + 0.01, (tm["rating"] - 50) / 60, left=0.55, height=0.03,
                    color="#147D64" if tm["rating"] >= 50 else "#C15A2C")
            ax.text(0.53, y, f"{tm['rating']:.1f}", fontsize=11, weight="bold",
                    family="monospace", ha="right")
            ax.text(0.86, y,
                    f"\u2248 {'+' if tm['rating'] >= 50 else '\u2212'}{abs(tm['rating'] - 50) * 1.7:.1f} pts of margin",
                    fontsize=8.5, color="#666")
        ax.plot([0.55, 0.55], [0.05, 0.92], color="#bbb", lw=0.8)
        ax.set_xlim(0, 1); ax.set_ylim(0, 1.05)
        os.makedirs(os.path.join(root, "post"), exist_ok=True)
        fig.savefig(os.path.join(root, "post", f"top10_wk{week_now}.png"),
                    bbox_inches="tight", facecolor="white")
        print("wrote post graphic")
    except ImportError:
        print("matplotlib missing; skipped post graphic")


if __name__ == "__main__":
    main()
