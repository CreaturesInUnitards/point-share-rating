"""Per-QB value model: walk-forward, recency-weighted, shrunken EPA/play."""
import pandas as pd, numpy as np

ALIASES = {"Gardner Minshew II":"Gardner Minshew","Justin Herbery":"Justin Herbert",
 "Mitch Trubisky":"Mitchell Trubisky","Robert Griffin":"Robert Griffin III",
 "Phillip Walker":"P.J. Walker","Michael Penix":"Michael Penix Jr.",
 "Michael Vick":"Mike Vick","A.J. McCarron":"AJ McCarron"}
# Taysom Hill / Kendall Hinton: gadget/emergency starts, left unmatched -> prior

def load_qb_weeks():
    qb = pd.read_csv("qb_weeks.csv")
    qb["gi"] = qb.groupby("qb").cumcount()          # career game index
    return qb

def qb_values_before(qb, half_life, m_plays, prior):
    """For each QB-week row, the QB's value entering that game
    (recency-weighted shrunken EPA/play over prior games). Vectorized recursion:
    S_epa <- lam*S_epa + epa; value_before = (lam*S_epa + m*prior)/(lam*S_plays + m)."""
    lam = 0.5 ** (1.0 / half_life)
    out = np.empty(len(qb)); Se = {}; Sp = {}
    for i, (q, e, p) in enumerate(zip(qb.qb.values, qb.epa.values, qb.plays.values)):
        se, sp = Se.get(q, 0.0), Sp.get(q, 0.0)
        out[i] = (se + m_plays * prior) / (sp + m_plays)
        Se[q] = lam * (se + e); Sp[q] = lam * (sp + p)
    return out

if __name__ == "__main__":
    qb = load_qb_weeks()
    # empirical replacement level: EPA/play of low-experience fill-ins (<16 career games), train era
    tr = qb[(qb.season <= 2021) & (qb.season >= 2015)]
    repl = tr[tr.gi < 16]
    REPL = repl.epa.sum() / repl.plays.sum()
    LEAGUE = tr.epa.sum() / tr.plays.sum()
    print(f"league avg EPA/play {LEAGUE:+.3f} | replacement (low-exp fill-ins) {REPL:+.3f}")

    # tune on train: predict each QB-week's realized EPA/play, plays-weighted corr
    mask = (qb.season >= 2015) & (qb.season <= 2021) & (qb.plays >= 10)
    best = None
    for hl in [8, 16, 32, 64]:
        for m in [50, 150, 300, 600]:
            v = qb_values_before(qb, hl, m, REPL)
            y = (qb.epa / qb.plays)[mask]; x = pd.Series(v, index=qb.index)[mask]
            w = qb.plays[mask]
            cx = ((x-np.average(x,weights=w))*(y-np.average(y,weights=w))*w).sum()
            corr = cx/np.sqrt((((x-np.average(x,weights=w))**2*w).sum())*(((y-np.average(y,weights=w))**2*w).sum()))
            if best is None or corr > best[0]: best = (corr, hl, m)
    corr, HL, M = best
    print(f"tuned: half_life={HL} games, shrinkage={M} pseudo-plays (train weighted corr {corr:.3f})")

    qb["value"] = qb_values_before(qb, HL, M, REPL)
    qb.to_csv("qb_values.csv", index=False)

    # holdout predictive check (2022-2025) vs naive career-mean baseline
    hm = (qb.season >= 2022) & (qb.plays >= 10)
    y = (qb.epa/qb.plays)[hm]; w = qb.plays[hm]
    def wcorr(x):
        x = x[hm]
        return (((x-np.average(x,weights=w))*(y-np.average(y,weights=w))*w).sum()
                / np.sqrt((((x-np.average(x,weights=w))**2*w).sum())*(((y-np.average(y,weights=w))**2*w).sum())))
    # naive: unweighted career mean to date, no shrinkage
    naive = qb_values_before(qb, 10**6, 1e-9, REPL)
    print(f"holdout corr w/ next-game EPA: model {wcorr(pd.Series(qb['value'])):.3f} vs naive career mean {wcorr(pd.Series(naive)):.3f}")

    # current top/bottom (entering end of 2025), active in 2025, min 200 plays that season
    latest = qb.sort_values(["season","week"]).groupby("qb").tail(1)
    act = qb[qb.season==2025].groupby("qb").plays.sum()
    cur = latest[latest.qb.isin(act[act>=200].index)][["qb","value"]].sort_values("value",ascending=False)
    cur["pts_per_game_vs_avg"] = ((cur.value - LEAGUE) * 38).round(1)
    print("\ntop 8 entering 2026:"); print(cur.head(8).round(3).to_string(index=False))
    print("\nbottom 5:"); print(cur.tail(5).round(3).to_string(index=False))
