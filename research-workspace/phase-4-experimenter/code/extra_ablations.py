"""Two robustness studies requested in review, run post-hoc on the same parsed data:

  A. IDENTITY PLACEBO  — re-fit with the player->encoding mapping randomly shuffled.
     If real identity carries genuine signal it should own large SHAP mass while the
     placebo does not; if neither transfers, both add ~0 out-of-sample skill. This
     directly tests whether the SHAP-vs-skill dissociation (H1) is real or an artifact
     of merely having high-variance numeric features.

  B. ROLLING-WINDOW EVALUATION — repeat the held-out-season protocol for every feasible
     test season (not just 2026), to test whether "identity does not help out-of-sample"
     is a single-season fluke or a stable pattern.

Reuses the exact model/feature/metric code from main.py. Seed 0, bootstrap B=500.
"""
import os, sys, time
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import main as MAIN
import models as M
import metrics as MET
import attribution as ATTR
import momentum_ms as MS  # noqa
import features as F

RES = MAIN.RES
BOOT_B = 500


def log(m):
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def fit_rungs(tr, va, rungs):
    """Fit only the requested ladder rungs for both heads. Returns dicts."""
    w_fit, w_iso, r_fit = {}, {}, {}
    trw, vaw = MAIN.prep_xy(tr, "wicket"), MAIN.prep_xy(va, "wicket")
    trr, varr = MAIN.prep_xy(tr, "runs"), MAIN.prep_xy(va, "runs")
    for name in rungs:
        cols = M.cols_for(M.LADDER[name])
        wm = M.fit_wicket_lgbm(trw[cols], trw["wicket"], vaw[cols], vaw["wicket"], seed=0)
        pv = wm.predict_proba(vaw[cols])[:, 1]
        w_fit[name] = (wm, cols)
        w_iso[name] = M.calibrate_isotonic(pv, vaw["wicket"].values)
        rm = M.fit_runs_lgbm(trr[cols], trr["runs_off_bat"], varr[cols], varr["runs_off_bat"], seed=0)
        r_fit[name] = (rm, cols)
    return w_fit, w_iso, r_fit


def head_metrics(w_fit, w_iso, r_fit, te):
    tew, ter = MAIN.prep_xy(te, "wicket"), MAIN.prep_xy(te, "runs")
    yw, yr = tew["wicket"].values, ter["runs_off_bat"].values
    out = {}
    out["M0_wicket_logloss"] = MET.log_loss_binary(yw, np.full(len(yw), yw.mean()))
    out["M0_runs_rmse"] = MET.rmse(yr, np.full(len(yr), yr.mean()))
    for name in w_fit:
        wm, wc = w_fit[name]
        p = np.clip(w_iso[name].predict(wm.predict_proba(tew[wc])[:, 1]), 1e-6, 1 - 1e-6)
        out[f"{name}_wicket_logloss"] = MET.log_loss_binary(yw, p)
        rm, rc = r_fit[name]
        out[f"{name}_runs_rmse"] = MET.rmse(yr, np.clip(rm.predict(ter[rc]), 0, None))
    return out, tew, ter


def identity_incr(w_fit, w_iso, r_fit, tew, ter):
    """BW|S incremental skill (>0 = identity helps) with match-clustered bootstrap CI."""
    yw = tew["wicket"].values
    def wp(n):
        m, c = w_fit[n]
        return np.clip(w_iso[n].predict(m.predict_proba(tew[c])[:, 1]), 1e-6, 1 - 1e-6)
    pS, pSBW = wp("M_S"), wp("M_SBW")
    def fw(idx):
        return MET.log_loss_binary(yw[idx], pS[idx]) - MET.log_loss_binary(yw[idx], pSBW[idx])
    w_pt, w_lo, w_hi = MET.match_clustered_bootstrap(tew["match_id"].values, fw, B=BOOT_B)
    yr = ter["runs_off_bat"].values
    def rp(n):
        m, c = r_fit[n]
        return np.clip(m.predict(ter[c]), 0, None)
    rS, rSBW = rp("M_S"), rp("M_SBW")
    def fr(idx):
        return MET.rmse(yr[idx], rS[idx]) - MET.rmse(yr[idx], rSBW[idx])
    r_pt, r_lo, r_hi = MET.match_clustered_bootstrap(ter["match_id"].values, fr, B=BOOT_B)
    return dict(wkt_incr=w_pt, wkt_lo=w_lo, wkt_hi=w_hi,
                runs_incr=r_pt, runs_lo=r_lo, runs_hi=r_hi)


# ---------------------------------------------------------------------------
def run_placebo(death, train, val, test, T):
    log("ABLATION A: identity placebo (random player shuffle)")
    rungs = ["M_S", "M_SBW"]
    rows = []
    for tag, shuf in [("real", None), ("placebo", 123)]:
        tr, va, te, _ = MAIN.encode_splits(train, val, test, death, T, MAIN.CONFIG["alpha"], shuffle_seed=shuf)
        w_fit, w_iso, r_fit = fit_rungs(tr, va, rungs)
        mets, tew, ter = head_metrics(w_fit, w_iso, r_fit, te)
        incr = identity_incr(w_fit, w_iso, r_fit, tew, ter)
        # grouped SHAP on M_SBW for both heads
        wm, wc = w_fit["M_SBW"]; rm, rc = r_fit["M_SBW"]
        gw = ATTR.grouped_shap(wm, tew[wc], n_sample=15000)
        gr = ATTR.grouped_shap(rm, ter[rc], n_sample=15000)
        rows.append(dict(encoding=tag,
                         wicket_logloss_M_SBW=mets["M_SBW_wicket_logloss"],
                         wicket_logloss_M_S=mets["M_S_wicket_logloss"],
                         runs_rmse_M_SBW=mets["M_SBW_runs_rmse"],
                         runs_rmse_M_S=mets["M_S_runs_rmse"],
                         shap_B_wicket=gw.get("B"), shap_W_wicket=gw.get("W"), shap_S_wicket=gw.get("S"),
                         shap_B_runs=gr.get("B"), shap_W_runs=gr.get("W"), shap_S_runs=gr.get("S"),
                         **{f"incr_{k}": v for k, v in incr.items()}))
        log(f"  {tag}: wkt SHAP B={gw.get('B'):.3f} runs SHAP B={gr.get('B'):.3f} | "
            f"runs incr(BW|S)={incr['runs_incr']:+.4f}[{incr['runs_lo']:+.4f},{incr['runs_hi']:+.4f}] "
            f"wkt incr={incr['wkt_incr']:+.5f}[{incr['wkt_lo']:+.5f},{incr['wkt_hi']:+.5f}]")
    df = pd.DataFrame(rows)
    df.to_csv(RES / "ablation_identity_placebo.csv", index=False)
    log("  saved ablation_identity_placebo.csv")
    return df


def run_rolling(death):
    log("ABLATION B: rolling-window multi-season evaluation")
    counts = death.groupby("season_year").size()
    years = sorted([int(y) for y in counts.index if not np.isnan(y)])
    # candidate test seasons: need >=2 prior seasons of train and a decent test volume
    cands = [T for T in years if (T - 2) >= years[0] and counts.get(T, 0) >= 3000]
    cands = cands[-6:]  # most recent feasible seasons
    log(f"  rolling test seasons: {cands}")
    rungs = ["M_S", "M_SBW", "M_SBW+P+H"]
    rows = []
    for T in cands:
        train = death[death["season_year"] <= T - 2].copy()
        val = death[death["season_year"] == T - 1].copy()
        test = death[death["season_year"] == T].copy()
        if len(train) < 5000 or len(val) < 500 or len(test) < 1000:
            log(f"  skip {T}: insufficient rows (tr={len(train)} va={len(val)} te={len(test)})")
            continue
        tr, va, te, _ = MAIN.encode_splits(train, val, test, death, T, MAIN.CONFIG["alpha"])
        w_fit, w_iso, r_fit = fit_rungs(tr, va, rungs)
        mets, tew, ter = head_metrics(w_fit, w_iso, r_fit, te)
        incr = identity_incr(w_fit, w_iso, r_fit, tew, ter)
        row = dict(test_season=T, n_test=int(len(test)),
                   wicket_base=mets["M0_wicket_logloss"],
                   wicket_state=mets["M_S_wicket_logloss"],
                   wicket_state_id=mets["M_SBW_wicket_logloss"],
                   runs_base=mets["M0_runs_rmse"],
                   runs_state=mets["M_S_runs_rmse"],
                   runs_state_id=mets["M_SBW_runs_rmse"],
                   identity_helps_wicket=int(incr["wkt_incr"] > 0),
                   identity_helps_runs=int(incr["runs_incr"] > 0),
                   **incr)
        rows.append(row)
        log(f"  T={T} (n={len(test)}): wkt {mets['M_S_wicket_logloss']:.4f}->{mets['M_SBW_wicket_logloss']:.4f} "
            f"runs {mets['M_S_runs_rmse']:.4f}->{mets['M_SBW_runs_rmse']:.4f} | "
            f"id runs incr={incr['runs_incr']:+.4f} wkt incr={incr['wkt_incr']:+.5f}")
    df = pd.DataFrame(rows)
    df.to_csv(RES / "ablation_rolling_window.csv", index=False)
    log("  saved ablation_rolling_window.csv")
    return df


if __name__ == "__main__":
    t0 = time.time()
    death = MAIN.load_processed()
    train, val, test, T = MAIN.temporal_split(death)
    pl = run_placebo(death, train, val, test, T)
    rw = run_rolling(death)
    print("\n=== PLACEBO ===\n", pl.to_string())
    print("\n=== ROLLING ===\n", rw.to_string())
    log(f"DONE total {round((time.time()-t0)/60,1)} min")
