"""Standalone runner for H3 (Miller-Sanjurjo) + ablations + figures, reusing cached parquet
and re-fitting only the seed-0 models needed for SHAP/figures. H1/H2/main_results already saved."""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
import main as MA
import momentum_ms as MS


def main():
    t0 = time.time()
    death = MA.load_processed()
    train, val, test, T = MA.temporal_split(death)
    tr, va, te, enc = MA.encode_splits(train, val, test, death, T, MA.CONFIG["alpha"])

    # ---- H3 full ----
    MA.log("H3: Miller-Sanjurjo momentum")
    h3_df = MA.run_h3(te)
    h3_df.to_csv(MA.RES / "h3_momentum.csv", index=False)
    print("\nH3 momentum:\n", h3_df.to_string(), flush=True)

    # ---- seed0 cache for figures (refit needed models) ----
    MA.log("refit seed0 models for figures")
    w_fitted, w_iso = MA.fit_ladder_for_target(tr, va, "wicket", 0)
    _, w_preds, w_te = MA.evaluate_wicket(w_fitted, w_iso, te, 0)
    r_fitted, _ = MA.fit_ladder_for_target(tr, va, "runs", 0)
    mult = MA.fit_multinomial_runs(tr, va, 0)
    _, r_preds, r_te = MA.evaluate_runs(r_fitted, mult, te, 0)
    c = dict(tr=tr, va=va, te=te, enc=enc,
             w_fitted=w_fitted, w_iso=w_iso, w_preds=w_preds, w_te=w_te,
             r_fitted=r_fitted, r_preds=r_preds, r_te=r_te, mult=mult)

    # ---- ablations ----
    MA.log("Ablations")
    MA.run_ablations(death, train, val, test, T, c)

    # ---- figures (need h1/incr/h2 dfs from disk) ----
    MA.log("Figures")
    main_df = pd.read_csv(MA.RES / "main_results.csv")
    h1_df = pd.read_csv(MA.RES / "h1_attribution.csv")
    incr_df = pd.read_csv(MA.RES / "h1_incremental_skill.csv")
    h2_df = pd.read_csv(MA.RES / "h2_incremental.csv")
    MA.make_figures(main_df, h1_df, incr_df, h2_df, h3_df, c)

    MA.log(f"H3+ablations+figures DONE total {round((time.time()-t0)/60,1)} min")


if __name__ == "__main__":
    main()
