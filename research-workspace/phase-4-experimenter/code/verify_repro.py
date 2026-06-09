"""Reproducibility check: re-run the deterministic headline computations from the
cached parquet and compare to the saved result CSVs. Seed-0, fixed permutation seeds.
"""
import os, sys
import numpy as np
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import main as MAIN

death = MAIN.load_processed()
print(f"[data] parquet rows = {len(death):,}")
print(f"[data] death deliveries (overs 16-20) = {len(death):,}  matches = {death['match_id'].nunique():,}")
print(f"[data] batter-credited wicket rate (legal) = {death.loc[death['legal']==1,'wicket'].mean():.4f}")
print(f"[data] mean runs_off_bat (legal) = {death.loc[death['legal']==1,'runs_off_bat'].mean():.4f}")

train, val, test, T = MAIN.temporal_split(death)
tr, va, te, enc = MAIN.encode_splits(train, val, test, death, T, MAIN.CONFIG["alpha"])

# --- re-run H3 from scratch ---
print("\n[H3] recomputing Miller-Sanjurjo sweep from parquet ...")
h3_new = MAIN.run_h3(te)
h3_old = pd.read_csv(MAIN.RES / "h3_momentum.csv")

prim_new = h3_new[(h3_new.success_def=="score") & (h3_new.direction=="hot") & (h3_new.k==1)].iloc[0]
prim_old = h3_old[(h3_old.success_def=="score") & (h3_old.direction=="hot") & (h3_old.k==1)].iloc[0]
print(f"  PRIMARY (k=1, score, hot):")
print(f"    D_naive   re-run={prim_new.D_naive:+.5f}  saved={prim_old.D_naive:+.5f}")
print(f"    bias      re-run={prim_new.mean_bias:+.5f}  saved={prim_old.mean_bias:+.5f}")
print(f"    D_corr    re-run={prim_new.D_corrected:+.5f}  saved={prim_old.D_corrected:+.5f}")
print(f"    gap       re-run={prim_new.gap:+.5f}  saved={prim_old.gap:+.5f}")
print(f"    n_seq     re-run={int(prim_new.n_seq)}  saved={int(prim_old.n_seq)}")

# compare full sweep on the deterministic columns
m = h3_new.merge(h3_old, on=["unit","success_def","direction","k"], suffixes=("_new","_old"))
for c in ["D_naive","D_corrected","gap","mean_bias","n_seq"]:
    maxdiff = (m[f"{c}_new"] - m[f"{c}_old"]).abs().max()
    print(f"  full-sweep max |Δ {c}| = {maxdiff:.2e}")

print("\n[DONE] reproduction check complete")
