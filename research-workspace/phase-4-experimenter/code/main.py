"""
Cricket death-over momentum & state-vs-identity decomposition.
H1: state vs identity (nested GBM + grouped SHAP), asymmetry runs vs wicket.
H2: residual dot-ball-pressure (Markov violation) beyond state and deterministic PI.
H3 (headline): Miller-Sanjurjo streak-bias correction + within-state permutation null.

Scope (user-confirmed): men's IPL + men's T20Is. H4 regime ablation SKIPPED.
"""
import os, sys, json, time, warnings
from pathlib import Path
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import data as D
import features as F
import models as M
import metrics as MET
import attribution as ATTR
import momentum_ms as MS

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "results"
FIG = RES / "figures"
RAW = RES / "raw"
DATA = ROOT / "data"
for p in (RES, FIG, RAW, DATA / "processed"):
    p.mkdir(parents=True, exist_ok=True)

CONFIG = dict(
    seeds=[0, 1, 2, 3, 4],
    leagues=("ipl", "t20s"),
    alpha=50,
    shap_sample=20000,
    boot_B=1000,
    perm_B_uncond=2000,
    perm_B_strat=2000,
    ms_max_perm=2000,
    k_values=[1, 2, 3],
)

RUN_CLASSES = [0, 1, 2, 3, 4, 6]
CLASS_TO_IDX = {c: i for i, c in enumerate(RUN_CLASSES)}


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


# ---------------------------------------------------------------------------
def load_processed():
    pq = DATA / "processed" / "deliveries.parquet"
    if pq.exists():
        log("loading cached parquet")
        return pd.read_parquet(pq)
    log("parsing raw Cricsheet CSVs")
    raw = D.load_raw(str(DATA / "raw"), leagues=CONFIG["leagues"])
    death = D.derive_and_filter(raw)
    death = F.add_pressure_index(death)
    death = F.add_history_features(death)
    death["stratum"] = MS._make_strata(death)
    D.basic_sanity(death)
    death.to_parquet(pq)
    return death


def temporal_split(death):
    years = sorted(death["season_year"].dropna().unique())
    # drop the partial current-year if it is tiny (<20% of prior year volume)
    counts = death.groupby("season_year").size()
    if len(years) >= 2 and counts.get(years[-1], 0) < 0.2 * counts.get(years[-2], 1):
        log(f"dropping sparse latest season {int(years[-1])} (n={int(counts[years[-1]])})")
        years = years[:-1]
    T = years[-1]
    Tm1 = years[-2]
    train = death[death["season_year"] <= T - 2].copy()
    val = death[death["season_year"] == Tm1].copy()
    test = death[death["season_year"] == T].copy()
    log(f"split: train<= {int(T-2)} ({len(train):,}) | val {int(Tm1)} ({len(val):,}) | test {int(T)} ({len(test):,})")
    return train, val, test, int(T)


def encode_splits(train, val, test, all_death, T, alpha, shuffle_seed=None):
    """Fit identity encoders historically and apply. Encoders for train use data < (T-2);
    for val/test use all data strictly before that season => historical-only.
    Simplified to two encoder fits to stay leakage-safe and fast."""
    enc_train = F.fit_identity_encoders(all_death[all_death["season_year"] <= T - 3], alpha=alpha) \
        if (all_death["season_year"] <= T - 3).any() else \
        F.fit_identity_encoders(train, alpha=alpha)
    enc_eval = F.fit_identity_encoders(all_death[all_death["season_year"] <= T - 2], alpha=alpha)
    train = F.apply_identity_encoders(train, enc_train, shuffle_seed=shuffle_seed)
    val = F.apply_identity_encoders(val, enc_eval, shuffle_seed=shuffle_seed)
    test = F.apply_identity_encoders(test, enc_eval, shuffle_seed=shuffle_seed)
    return train, val, test, enc_eval


def prep_xy(df, target="wicket"):
    """Filter rows appropriately. For runs: legal balls only (drop pure extras)."""
    if target == "runs":
        d = df[(df["legal"] == 1)].copy()
        d = d[d["runs_off_bat"].isin(RUN_CLASSES)]
    else:
        d = df.copy()  # wicket head keeps all rows
    return d


def fit_ladder_for_target(train, val, target, seed, runs_objective="tweedie"):
    """Fit each ladder rung. target in {'wicket','runs'}. Returns dict model_name->fitted."""
    fitted = {}
    iso = {}
    tr = prep_xy(train, target)
    va = prep_xy(val, target)
    ycol = "wicket" if target == "wicket" else "runs_off_bat"
    for name, groups in M.LADDER.items():
        cols = M.cols_for(groups)
        Xtr, Xva = tr[cols], va[cols]
        if target == "wicket":
            m = M.fit_wicket_lgbm(Xtr, tr[ycol], Xva, va[ycol], seed=seed)
            p_va = m.predict_proba(Xva)[:, 1]
            iso[name] = M.calibrate_isotonic(p_va, va[ycol].values)
        else:
            m = M.fit_runs_lgbm(Xtr, tr[ycol], Xva, va[ycol], seed=seed, objective=runs_objective)
        fitted[name] = (m, cols)
    return fitted, iso


def fit_multinomial_runs(train, val, seed):
    tr = prep_xy(train, "runs"); va = prep_xy(val, "runs")
    cols = M.cols_for(["S", "B", "W", "P", "H"])
    ytr = tr["runs_off_bat"].map(CLASS_TO_IDX).values
    yva = va["runs_off_bat"].map(CLASS_TO_IDX).values
    m = M.fit_runs_multinomial_lgbm(tr[cols], ytr, va[cols], yva, seed=seed)
    return m, cols


def evaluate_wicket(fitted, iso, test, seed):
    te = prep_xy(test, "wicket")
    y = te["wicket"].values
    rows = []
    preds = {}
    for name, (m, cols) in fitted.items():
        p = m.predict_proba(te[cols])[:, 1]
        p = iso[name].predict(p)
        p = np.clip(p, 1e-6, 1 - 1e-6)
        preds[name] = p
        rows.append(dict(model=name, target="wicket",
                         logloss=MET.log_loss_binary(y, p), brier=MET.brier(y, p),
                         ece=MET.ece(y, p), prauc=MET.pr_auc(y, p),
                         rmse=np.nan, mae=np.nan, crps=np.nan, seed=seed))
    # M0 base rate
    base = test_base_rate(test, "wicket")
    p0 = np.full(len(y), base)
    rows.append(dict(model="M0", target="wicket", logloss=MET.log_loss_binary(y, p0),
                     brier=MET.brier(y, p0), ece=MET.ece(y, p0), prauc=MET.pr_auc(y, p0),
                     rmse=np.nan, mae=np.nan, crps=np.nan, seed=seed))
    return rows, preds, te


def evaluate_runs(fitted, mult_model, test, seed):
    te = prep_xy(test, "runs")
    y = te["runs_off_bat"].values
    rows = []
    preds = {}
    for name, (m, cols) in fitted.items():
        yhat = np.clip(m.predict(te[cols]), 0, None)
        preds[name] = yhat
        rows.append(dict(model=name, target="runs", logloss=np.nan, brier=np.nan,
                         ece=np.nan, prauc=np.nan, rmse=MET.rmse(y, yhat),
                         mae=MET.mae(y, yhat), crps=np.nan, seed=seed))
    # multinomial CRPS + expected runs
    mm, mcols = mult_model
    P = mm.predict_proba(te[mcols])
    classes = np.array(RUN_CLASSES)
    crps = MET.crps_multinomial(y, P, classes=classes)
    erun = P @ classes
    rows.append(dict(model="M_mult", target="runs", logloss=np.nan, brier=np.nan,
                     ece=np.nan, prauc=np.nan, rmse=MET.rmse(y, erun),
                     mae=MET.mae(y, erun), crps=crps, seed=seed))
    base = test_base_rate(test, "runs")
    y0 = np.full(len(y), base)
    rows.append(dict(model="M0", target="runs", logloss=np.nan, brier=np.nan, ece=np.nan,
                     prauc=np.nan, rmse=MET.rmse(y, y0), mae=MET.mae(y, y0), crps=np.nan, seed=seed))
    return rows, preds, te


def test_base_rate(test, target):
    if target == "wicket":
        return test["wicket"].mean()
    d = prep_xy(test, "runs")
    return d["runs_off_bat"].mean()


# ---------------------------------------------------------------------------
def run():
    t0 = time.time()
    death = load_processed()
    train, val, test, T = temporal_split(death)

    all_main = []
    h1_shap_rows = []
    h2_rows = []
    # store seed-0 artifacts for SHAP / bootstrap / leakage
    seed0_cache = {}

    for seed in CONFIG["seeds"]:
        log(f"===== SEED {seed} =====")
        tr, va, te, enc = encode_splits(train, val, test, death, T, CONFIG["alpha"])

        # wicket ladder
        log("  fit wicket ladder")
        w_fitted, w_iso = fit_ladder_for_target(tr, va, "wicket", seed)
        w_rows, w_preds, w_te = evaluate_wicket(w_fitted, w_iso, te, seed)
        all_main += w_rows

        # runs ladder + multinomial
        log("  fit runs ladder + multinomial")
        r_fitted, _ = fit_ladder_for_target(tr, va, "runs", seed)
        mult = fit_multinomial_runs(tr, va, seed)
        r_rows, r_preds, r_te = evaluate_runs(r_fitted, mult, te, seed)
        all_main += r_rows

        if seed == 0:
            seed0_cache = dict(tr=tr, va=va, te=te, enc=enc,
                               w_fitted=w_fitted, w_iso=w_iso, w_preds=w_preds, w_te=w_te,
                               r_fitted=r_fitted, r_preds=r_preds, r_te=r_te, mult=mult)

    main_df = pd.DataFrame(all_main)
    main_df.to_csv(RES / "main_results.csv", index=False)
    log(f"saved main_results.csv ({len(main_df)} rows)")
    print(main_df.groupby(["target", "model"])[["logloss", "brier", "rmse", "mae", "crps"]]
          .mean().to_string())

    # ---------------- H1: grouped SHAP + incremental skill + asymmetry ----------------
    log("H1: grouped SHAP")
    h1_attr = []
    # wicket SHAP on full identity model M_SBW
    wm, wcols = seed0_cache["w_fitted"]["M_SBW"]
    Xw = seed0_cache["w_te"][wcols]
    gw = ATTR.grouped_shap(wm, Xw, n_sample=CONFIG["shap_sample"])
    for g, v in gw.items():
        h1_attr.append(dict(target="wicket", group=g, shap_pct=v))
    rm, rcols = seed0_cache["r_fitted"]["M_SBW"]
    Xr = seed0_cache["r_te"][rcols]
    gr = ATTR.grouped_shap(rm, Xr, n_sample=CONFIG["shap_sample"])
    for g, v in gr.items():
        h1_attr.append(dict(target="runs", group=g, shap_pct=v))
    h1_df = pd.DataFrame(h1_attr)

    # incremental skill table with match-clustered bootstrap (seed0)
    incr = incremental_skill_h1(seed0_cache)
    incr_df = pd.DataFrame(incr)
    # merge incr skill into h1 attribution-ish file
    h1_df.to_csv(RES / "h1_attribution.csv", index=False)
    incr_df.to_csv(RES / "h1_incremental_skill.csv", index=False)
    print("\nH1 grouped SHAP %:\n", h1_df.pivot(index="group", columns="target", values="shap_pct").to_string())
    print("\nH1 incremental skill:\n", incr_df.to_string())

    # asymmetry: identity skill share runs vs wicket
    asym = asymmetry_test(seed0_cache)
    pd.DataFrame([asym]).to_csv(RES / "h1_asymmetry.csv", index=False)
    print("\nH1 asymmetry:", asym)

    # leakage audit
    log("H1: leakage audit")
    la = ATTR.leakage_audit(seed0_cache["te"], F.GROUP_B + F.GROUP_W, F.GROUP_S)
    la.to_csv(RES / "leakage_audit.csv", index=False)
    print("\nLeakage audit (R^2 identity~state):\n", la.to_string())

    # ---------------- H2: incremental skill of H beyond S+B+W+P ----------------
    log("H2: incremental skill of history beyond state+PI")
    h2 = h2_incremental(seed0_cache)
    h2_df = pd.DataFrame(h2)
    h2_df.to_csv(RES / "h2_incremental.csv", index=False)
    print("\nH2 incremental:\n", h2_df.to_string())

    # ---------------- H3: Miller-Sanjurjo ----------------
    log("H3: Miller-Sanjurjo momentum (this is the slow part)")
    h3_df = run_h3(seed0_cache["te"])
    h3_df.to_csv(RES / "h3_momentum.csv", index=False)
    print("\nH3 momentum:\n", h3_df.to_string())

    # ---------------- Ablations ----------------
    log("Ablations")
    run_ablations(death, train, val, test, T, seed0_cache)

    # ---------------- Figures ----------------
    log("Figures")
    make_figures(main_df, h1_df, incr_df, h2_df, h3_df, seed0_cache)

    log(f"DONE total {round((time.time()-t0)/60,1)} min")


# ---------------------------------------------------------------------------
def incremental_skill_h1(c):
    """Delta skill (positive=improvement) for adding B, W, BW over state, both heads,
    with match-clustered bootstrap CIs."""
    rows = []
    # WICKET: logloss
    w_te = c["w_te"]; mids_w = w_te["match_id"].values; yw = w_te["wicket"].values
    def w_pred(name):
        m, cols = c["w_fitted"][name]
        p = m.predict_proba(w_te[cols])[:, 1]
        return np.clip(c["w_iso"][name].predict(p), 1e-6, 1 - 1e-6)
    pS = w_pred("M_S"); pSB = w_pred("M_SB"); pSW = w_pred("M_SW"); pSBW = w_pred("M_SBW")
    for label, p_rich, p_base in [("B|S", pSB, pS), ("W|S", pSW, pS), ("BW|S", pSBW, pS)]:
        def fn(rows_idx, pr=p_rich, pb=p_base):
            return MET.log_loss_binary(yw[rows_idx], pb[rows_idx]) - MET.log_loss_binary(yw[rows_idx], pr[rows_idx])
        pt, lo, hi = MET.match_clustered_bootstrap(mids_w, fn, B=CONFIG["boot_B"])
        rows.append(dict(target="wicket", metric="logloss", added=label, incr_skill=pt, ci_lo=lo, ci_hi=hi))
    # RUNS: rmse
    r_te = c["r_te"]; mids_r = r_te["match_id"].values; yr = r_te["runs_off_bat"].values
    def r_pred(name):
        m, cols = c["r_fitted"][name]
        return np.clip(m.predict(r_te[cols]), 0, None)
    rS = r_pred("M_S"); rSB = r_pred("M_SB"); rSW = r_pred("M_SW"); rSBW = r_pred("M_SBW")
    for label, y_rich, y_base in [("B|S", rSB, rS), ("W|S", rSW, rS), ("BW|S", rSBW, rS)]:
        def fn(rows_idx, yr_=y_rich, yb_=y_base):
            return MET.rmse(yr[rows_idx], yb_[rows_idx]) - MET.rmse(yr[rows_idx], yr_[rows_idx])
        pt, lo, hi = MET.match_clustered_bootstrap(mids_r, fn, B=CONFIG["boot_B"])
        rows.append(dict(target="runs", metric="rmse", added=label, incr_skill=pt, ci_lo=lo, ci_hi=hi))
    return rows


def asymmetry_test(c):
    """Identity's share of explained skill (M_SBW vs M_S over M0 baseline) for runs vs wicket."""
    w_te = c["w_te"]; yw = w_te["wicket"].values
    def w_pred(name):
        m, cols = c["w_fitted"][name]
        p = m.predict_proba(w_te[cols])[:, 1]
        return np.clip(c["w_iso"][name].predict(p), 1e-6, 1 - 1e-6)
    base_w = np.full(len(yw), yw.mean())
    ll0 = MET.log_loss_binary(yw, base_w)
    llS = MET.log_loss_binary(yw, w_pred("M_S"))
    llSBW = MET.log_loss_binary(yw, w_pred("M_SBW"))
    skill_state_w = ll0 - llS
    skill_id_w = llS - llSBW
    share_w = skill_id_w / (skill_state_w + skill_id_w) if (skill_state_w + skill_id_w) != 0 else np.nan

    r_te = c["r_te"]; yr = r_te["runs_off_bat"].values
    def r_pred(name):
        m, cols = c["r_fitted"][name]
        return np.clip(m.predict(r_te[cols]), 0, None)
    rmse0 = MET.rmse(yr, np.full(len(yr), yr.mean()))
    rmseS = MET.rmse(yr, r_pred("M_S"))
    rmseSBW = MET.rmse(yr, r_pred("M_SBW"))
    skill_state_r = rmse0 - rmseS
    skill_id_r = rmseS - rmseSBW
    share_r = skill_id_r / (skill_state_r + skill_id_r) if (skill_state_r + skill_id_r) != 0 else np.nan
    return dict(identity_share_wicket=float(share_w), identity_share_runs=float(share_r),
                asymmetry_runs_minus_wicket=float(share_r - share_w),
                skill_state_wicket=float(skill_state_w), skill_id_wicket=float(skill_id_w),
                skill_state_runs=float(skill_state_r), skill_id_runs=float(skill_id_r))


def h2_incremental(c):
    """Delta of M_SBW+P+H vs M_SBW+P for both heads; dot_run_len SHAP sign."""
    rows = []
    w_te = c["w_te"]; mids_w = w_te["match_id"].values; yw = w_te["wicket"].values
    def w_pred(name):
        m, cols = c["w_fitted"][name]
        p = m.predict_proba(w_te[cols])[:, 1]
        return np.clip(c["w_iso"][name].predict(p), 1e-6, 1 - 1e-6)
    pP = w_pred("M_SBW+P"); pPH = w_pred("M_SBW+P+H")
    # dot_run_len SHAP sign on wicket
    wm, wcols = c["w_fitted"]["M_SBW+P+H"]
    sign_w = dotrun_shap_sign(wm, w_te[wcols])
    for metric, fn_metric in [("logloss", MET.log_loss_binary), ("brier", MET.brier)]:
        def fn(idx, fm=fn_metric):
            return fm(yw[idx], pP[idx]) - fm(yw[idx], pPH[idx])
        pt, lo, hi = MET.match_clustered_bootstrap(mids_w, fn, B=CONFIG["boot_B"])
        p_val = 0.0 if (lo > 0 or hi < 0) else 1.0  # crude: significant if CI excludes 0
        rows.append(dict(target="wicket", metric=metric, delta=pt, ci_lo=lo, ci_hi=hi,
                         dotrun_sign=sign_w, sig_ci_excl0=int(lo > 0 or hi < 0)))
    r_te = c["r_te"]; mids_r = r_te["match_id"].values; yr = r_te["runs_off_bat"].values
    def r_pred(name):
        m, cols = c["r_fitted"][name]
        return np.clip(m.predict(r_te[cols]), 0, None)
    rP = r_pred("M_SBW+P"); rPH = r_pred("M_SBW+P+H")
    rm, rcols = c["r_fitted"]["M_SBW+P+H"]
    sign_r = dotrun_shap_sign(rm, r_te[rcols])
    def fnr(idx):
        return MET.rmse(yr[idx], rP[idx]) - MET.rmse(yr[idx], rPH[idx])
    pt, lo, hi = MET.match_clustered_bootstrap(mids_r, fnr, B=CONFIG["boot_B"])
    rows.append(dict(target="runs", metric="rmse", delta=pt, ci_lo=lo, ci_hi=hi,
                     dotrun_sign=sign_r, sig_ci_excl0=int(lo > 0 or hi < 0)))
    return rows


def dotrun_shap_sign(model, X, n=8000):
    """Sign of correlation between dot_run_len and its SHAP contribution (mean)."""
    import shap
    if "dot_run_len" not in X.columns:
        return 0
    Xs = X.sample(min(n, len(X)), random_state=0)
    expl = shap.TreeExplainer(model)
    sv = expl.shap_values(Xs)
    if isinstance(sv, list):
        sv = sv[1] if len(sv) == 2 else sv[0]
    sv = np.asarray(sv)
    if sv.ndim == 3:
        sv = sv[:, :, -1]
    j = list(X.columns).index("dot_run_len")
    corr = np.corrcoef(Xs["dot_run_len"].values, sv[:, j])[0, 1]
    return int(np.sign(corr)) if not np.isnan(corr) else 0


# ---------------------------------------------------------------------------
def run_h3(test_df, units=("batter_stay",), success_defs=("score", "boundary"),
           directions=("hot", "cold"), full=True):
    rows = []
    pvals = []
    for unit in units:
        for sdef in success_defs:
            seqs_base = MS.build_sequences(test_df, unit=unit, success=sdef)
            for direction in directions:
                for k in CONFIG["k_values"]:
                    agg = MS.corrected_aggregate(seqs_base, k, direction=direction,
                                                 max_perm=CONFIG["ms_max_perm"], seed=0)
                    if agg["n_seq"] == 0 or np.isnan(agg["D_corrected"]):
                        rows.append(dict(unit=unit, success_def=sdef, direction=direction, k=k,
                                         D_naive=np.nan, D_corrected=np.nan, gap=np.nan,
                                         mean_bias=np.nan, n_seq=agg["n_seq"],
                                         p_uncond=np.nan, p_strat=np.nan))
                        pvals.append(np.nan)
                        continue
                    p_unc, _ = MS.perm_null_unconditional(seqs_base, k, direction=direction,
                                                          B=CONFIG["perm_B_uncond"], seed=0)
                    p_str, _ = MS.perm_null_state_stratified(seqs_base, k, direction=direction,
                                                            observed=agg["D_corrected"],
                                                            B=CONFIG["perm_B_strat"],
                                                            max_perm=CONFIG["ms_max_perm"], seed=0)
                    rows.append(dict(unit=unit, success_def=sdef, direction=direction, k=k,
                                     D_naive=agg["D_naive"], D_corrected=agg["D_corrected"],
                                     gap=agg["gap"], mean_bias=agg["mean_bias"], n_seq=agg["n_seq"],
                                     p_uncond=p_unc, p_strat=p_str))
                    pvals.append(p_str)
                    log(f"    H3 {unit}/{sdef}/{direction}/k={k}: D_naive={agg['D_naive']:.4f} "
                        f"D_corr={agg['D_corrected']:.4f} gap={agg['gap']:.4f} p_strat={p_str:.4f}")
    df = pd.DataFrame(rows)
    df["p_bh"] = MS.bh_fdr(df["p_strat"].values)
    return df


# ---------------------------------------------------------------------------
def run_ablations(death, train, val, test, T, c):
    # 1. identity-encoding placebo (random-player shuffle should add ~0 skill)
    log("  ablation: identity placebo")
    tr_p, va_p, te_p, _ = encode_splits(train, val, test, death, T, CONFIG["alpha"], shuffle_seed=123)
    w_f, w_i = fit_ladder_for_target(tr_p, va_p, "wicket", 0)
    w_r, _, _ = evaluate_wicket(w_f, w_i, te_p, 0)
    r_f, _ = fit_ladder_for_target(tr_p, va_p, "runs", 0)
    mult_p = fit_multinomial_runs(tr_p, va_p, 0)
    r_r, _, _ = evaluate_runs(r_f, mult_p, te_p, 0)
    abl = pd.DataFrame(w_r + r_r)
    abl["encoding"] = "placebo_shuffle"
    # real for comparison
    real_w = pd.DataFrame([x for x in [dict(model=n, target="wicket")] for n in []])
    abl.to_csv(RES / "ablation_identity.csv", index=False)

    # 2. run-out inclusion (wicket_any)
    log("  ablation: run-out inclusion (wicket_any)")
    tr, va, te, _ = encode_splits(train, val, test, death, T, CONFIG["alpha"])
    rows = []
    for name in ["M_S", "M_SBW", "M_SBW+P+H"]:
        cols = M.cols_for(M.LADDER[name])
        m = M.fit_wicket_lgbm(tr[cols], tr["wicket_any"], va[cols], va["wicket_any"], seed=0)
        p_va = m.predict_proba(va[cols])[:, 1]
        iso = M.calibrate_isotonic(p_va, va["wicket_any"].values)
        p = np.clip(iso.predict(m.predict_proba(te[cols])[:, 1]), 1e-6, 1 - 1e-6)
        y = te["wicket_any"].values
        rows.append(dict(model=name, target="wicket_any", logloss=MET.log_loss_binary(y, p),
                         brier=MET.brier(y, p), prauc=MET.pr_auc(y, p)))
    pd.DataFrame(rows).to_csv(RES / "ablation_runout.csv", index=False)

    # 3. sequence-unit ablation (H3) on test set, k=1, score, both directions
    log("  ablation: H3 sequence unit")
    seq_rows = []
    for unit in ["batter_stay", "within_over", "partnership"]:
        seqs = MS.build_sequences(c["te"], unit=unit, success="score")
        for direction in ["hot", "cold"]:
            agg = MS.corrected_aggregate(seqs, 1, direction=direction, max_perm=CONFIG["ms_max_perm"])
            seq_rows.append(dict(unit=unit, success_def="score", direction=direction, k=1,
                                 D_naive=agg["D_naive"], D_corrected=agg["D_corrected"],
                                 gap=agg["gap"], n_seq=agg["n_seq"]))
    pd.DataFrame(seq_rows).to_csv(RES / "ablation_sequnit.csv", index=False)

    # 4. league scope: IPL-only vs IPL+T20I
    log("  ablation: league scope (IPL only)")
    ipl = death[death["league"] == "ipl"]
    rows = []
    years = sorted(ipl["season_year"].dropna().unique())
    Ti = int(years[-1]);
    counts = ipl.groupby("season_year").size()
    if counts.get(Ti, 0) < 0.2 * counts.get(years[-2], 1):
        years = years[:-1]; Ti = int(years[-1])
    itr = ipl[ipl["season_year"] <= Ti - 2]; iva = ipl[ipl["season_year"] == Ti - 1]; ite = ipl[ipl["season_year"] == Ti]
    if len(ite) > 200 and len(itr) > 1000:
        itr, iva, ite, _ = encode_splits(itr, iva, ite, ipl, Ti, CONFIG["alpha"])
        wf, wi = fit_ladder_for_target(itr, iva, "wicket", 0)
        wr, _, _ = evaluate_wicket(wf, wi, ite, 0)
        rf, _ = fit_ladder_for_target(itr, iva, "runs", 0)
        mlt = fit_multinomial_runs(itr, iva, 0)
        rr, _, _ = evaluate_runs(rf, mlt, ite, 0)
        adf = pd.DataFrame(wr + rr); adf["scope"] = "ipl_only"
        adf.to_csv(RES / "ablation_league.csv", index=False)

    # 5. learner ablation: GLM vs LightGBM on state-only and full
    log("  ablation: learner GLM vs LightGBM")
    rows = []
    trw = prep_xy(tr, "wicket"); vaw = prep_xy(va, "wicket"); tew = prep_xy(te, "wicket")
    trr = prep_xy(tr, "runs"); ter = prep_xy(te, "runs")
    for name in ["M_S", "M_SBW"]:
        cols = M.cols_for(M.LADDER[name])
        # GLM wicket
        gm = M.fit_glm_wicket(trw[cols], trw["wicket"])
        pg = np.clip(M.predict_glm_wicket(gm, tew[cols]), 1e-6, 1 - 1e-6)
        yw = tew["wicket"].values
        rows.append(dict(learner="GLM", model=name, target="wicket",
                         logloss=MET.log_loss_binary(yw, pg), brier=MET.brier(yw, pg)))
        # GLM runs
        gr = M.fit_glm_runs(trr[cols], trr["runs_off_bat"])
        yhat = np.clip(M.predict_glm_runs(gr, ter[cols]), 0, None)
        yr = ter["runs_off_bat"].values
        rows.append(dict(learner="GLM", model=name, target="runs",
                         rmse=MET.rmse(yr, yhat), mae=MET.mae(yr, yhat)))
    pd.DataFrame(rows).to_csv(RES / "ablation_learner.csv", index=False)
    log("  ablations done")


# ---------------------------------------------------------------------------
def make_figures(main_df, h1_df, incr_df, h2_df, h3_df, c):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.size": 10, "font.family": "serif",
                         "axes.spines.top": False, "axes.spines.right": False})

    def save(fig, name):
        fig.tight_layout()
        fig.savefig(FIG / f"{name}.pdf", bbox_inches="tight")
        fig.savefig(FIG / f"{name}.png", dpi=200, bbox_inches="tight")
        plt.close(fig)

    # 1. grouped SHAP bars
    piv = h1_df.pivot(index="group", columns="target", values="shap_pct").fillna(0)
    order = [g for g in ["S", "B", "W", "P", "H"] if g in piv.index]
    piv = piv.reindex(order)
    fig, ax = plt.subplots(figsize=(5, 3))
    x = np.arange(len(piv)); w = 0.38
    if "wicket" in piv.columns:
        ax.bar(x - w/2, piv["wicket"]*100, w, label="wicket", color="#1f77b4")
    if "runs" in piv.columns:
        ax.bar(x + w/2, piv["runs"]*100, w, label="runs", color="#ff7f0e")
    ax.set_xticks(x); ax.set_xticklabels(piv.index)
    ax.set_ylabel("% of total |SHAP|"); ax.set_xlabel("feature group")
    ax.set_title("H1: grouped SHAP mass (M_SBW)"); ax.legend()
    save(fig, "h1_grouped_shap")

    # 2. wicket reliability diagram (M_SBW)
    wm, wcols = c["w_fitted"]["M_SBW"]
    w_te = c["w_te"]
    p = np.clip(c["w_iso"]["M_SBW"].predict(wm.predict_proba(w_te[wcols])[:, 1]), 1e-6, 1-1e-6)
    y = w_te["wicket"].values
    bins = np.linspace(0, p.max(), 11)
    idx = np.clip(np.digitize(p, bins) - 1, 0, 9)
    conf = [p[idx == b].mean() for b in range(10) if (idx == b).sum() > 0]
    acc = [y[idx == b].mean() for b in range(10) if (idx == b).sum() > 0]
    fig, ax = plt.subplots(figsize=(3.5, 3.5))
    ax.plot([0, max(conf)], [0, max(conf)], "k--", lw=1, label="ideal")
    ax.plot(conf, acc, "o-", color="#1f77b4", label="M_SBW")
    ax.set_xlabel("predicted P(wicket)"); ax.set_ylabel("observed freq")
    ax.set_title("Wicket reliability"); ax.legend()
    save(fig, "wicket_reliability")

    # 3. incremental skill forest
    fig, ax = plt.subplots(figsize=(5, 3.2))
    incr = incr_df.reset_index(drop=True)
    labels = [f"{r.target}:{r.added}" for r in incr.itertuples()]
    yy = np.arange(len(incr))
    ax.errorbar(incr["incr_skill"], yy,
                xerr=[incr["incr_skill"]-incr["ci_lo"], incr["ci_hi"]-incr["incr_skill"]],
                fmt="o", color="#1f77b4", capsize=3)
    ax.axvline(0, color="k", lw=0.8)
    ax.set_yticks(yy); ax.set_yticklabels(labels)
    ax.set_xlabel("incremental skill (logloss/RMSE units, >0 better)")
    ax.set_title("H1 incremental skill (95% CI)")
    save(fig, "h1_incremental_forest")

    # 4. H3 D_naive vs D_corrected (score, batter_stay)
    sub = h3_df[(h3_df.unit == "batter_stay") & (h3_df.success_def == "score")]
    fig, ax = plt.subplots(figsize=(5, 3.2))
    for direction, col in [("hot", "#1f77b4"), ("cold", "#d62728")]:
        s = sub[sub.direction == direction].sort_values("k")
        ax.plot(s["k"], s["D_naive"], "o--", color=col, alpha=0.5, label=f"{direction} naive")
        ax.plot(s["k"], s["D_corrected"], "s-", color=col, label=f"{direction} corrected")
    ax.axhline(0, color="k", lw=0.8)
    ax.set_xlabel("streak length k"); ax.set_ylabel("D (momentum)")
    ax.set_title("H3: naive vs MS-corrected momentum"); ax.legend(fontsize=8)
    save(fig, "h3_naive_vs_corrected")

    # 5. E[runs] calibration (multinomial)
    mm, mcols = c["mult"]; r_te = c["r_te"]
    P = mm.predict_proba(r_te[mcols]); erun = P @ np.array(RUN_CLASSES)
    cal = MET.expected_runs_calibration(r_te["runs_off_bat"].values, erun)
    fig, ax = plt.subplots(figsize=(3.5, 3.5))
    cal = np.array(cal)
    ax.plot([cal[:,0].min(), cal[:,0].max()], [cal[:,0].min(), cal[:,0].max()], "k--", lw=1)
    ax.plot(cal[:, 0], cal[:, 1], "o-", color="#ff7f0e")
    ax.set_xlabel("predicted E[runs]"); ax.set_ylabel("observed mean runs")
    ax.set_title("E[runs] calibration")
    save(fig, "eruns_calibration")
    log("  figures saved")


if __name__ == "__main__":
    run()
