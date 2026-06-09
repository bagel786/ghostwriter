"""Figures for the two review-requested robustness studies."""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

R = os.path.join(os.path.dirname(__file__), "..", "results")
FIG = os.path.join(R, "figures")
plt.rcParams.update({"font.size": 10, "axes.titlesize": 11, "figure.dpi": 150,
                     "savefig.bbox": "tight", "axes.spines.top": False,
                     "axes.spines.right": False, "font.family": "DejaVu Sans"})
C = {"state": "#2c6fbb", "batter": "#d9722b", "bowler": "#3a9b6e", "neg": "#c44e52"}


def save(fig, name):
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(FIG, f"{name}.{ext}"))
    plt.close(fig)
    print("wrote", name)


# ---- Fig 6: identity placebo ----
pl = pd.read_csv(os.path.join(R, "ablation_identity_placebo.csv")).set_index("encoding")
fig, axes = plt.subplots(1, 2, figsize=(8.4, 3.3))
# left: SHAP mass of batter group, real vs placebo, both targets
x = np.arange(2)
w = 0.36
real = [pl.loc["real", "shap_B_runs"] * 100, pl.loc["real", "shap_B_wicket"] * 100]
plac = [pl.loc["placebo", "shap_B_runs"] * 100, pl.loc["placebo", "shap_B_wicket"] * 100]
axes[0].bar(x - w / 2, real, w, label="real identity", color=C["batter"])
axes[0].bar(x + w / 2, plac, w, label="shuffled placebo", color="#bbbbbb")
axes[0].set_xticks(x); axes[0].set_xticklabels(["E[runs]", "P(wicket)"])
axes[0].set_ylabel("batter-group share of |SHAP| (%)")
axes[0].set_title("Placebo collapses batter SHAP mass")
for xi, (rv, pv) in enumerate(zip(real, plac)):
    axes[0].text(xi - w / 2, rv + 1, f"{rv:.0f}", ha="center", fontsize=8)
    axes[0].text(xi + w / 2, pv + 1, f"{pv:.0f}", ha="center", fontsize=8)
axes[0].legend(frameon=False, fontsize=8)
# right: incremental skill (runs RMSE) real vs placebo with CI
labels = ["real", "placebo"]
vals = [pl.loc["real", "incr_runs_incr"], pl.loc["placebo", "incr_runs_incr"]]
los = [pl.loc["real", "incr_runs_lo"], pl.loc["placebo", "incr_runs_lo"]]
his = [pl.loc["real", "incr_runs_hi"], pl.loc["placebo", "incr_runs_hi"]]
yy = np.arange(2)[::-1]
for yi, (v, lo, hi, lab) in zip(yy, zip(vals, los, his, labels)):
    col = C["neg"] if hi < 0 else "#888888"
    axes[1].plot([lo, hi], [yi, yi], color=col, lw=2)
    axes[1].plot(v, yi, "o", color=col, ms=6)
axes[1].axvline(0, color="k", lw=0.8, ls="--")
axes[1].set_yticks(yy); axes[1].set_yticklabels(labels)
axes[1].set_xlabel("identity incremental skill on E[runs] (>0 helps)")
axes[1].set_title("Real identity hurts; placebo is harmless")
fig.suptitle("Identity placebo: genuine player signal that does not generalise", y=1.04)
save(fig, "fig6_identity_placebo")


# ---- Fig 7: rolling-window ----
rw = pd.read_csv(os.path.join(R, "ablation_rolling_window.csv")).sort_values("test_season")
fig, axes = plt.subplots(1, 2, figsize=(8.6, 3.3))
s = rw["test_season"].astype(int).astype(str)
# left: runs incremental skill of identity, per season, with CI
xpos = np.arange(len(rw))
axes[0].errorbar(xpos, rw["runs_incr"],
                 yerr=[rw["runs_incr"] - rw["runs_lo"], rw["runs_hi"] - rw["runs_incr"]],
                 fmt="o", color=C["neg"], capsize=3)
axes[0].axhline(0, color="k", lw=0.8, ls="--")
axes[0].set_xticks(xpos); axes[0].set_xticklabels(s, rotation=0)
axes[0].set_ylabel("identity incr. skill on E[runs] (RMSE units)")
axes[0].set_xlabel("held-out test season")
axes[0].set_title("Identity hurts runs RMSE in all 6 seasons")
# right: log-loss / rmse base vs state vs state+id (wicket logloss left axis style) -> use runs rmse
axes[1].plot(xpos, rw["runs_base"], "o--", color="#999999", label="base rate")
axes[1].plot(xpos, rw["runs_state"], "s-", color=C["state"], label="state only")
axes[1].plot(xpos, rw["runs_state_id"], "^-", color=C["batter"], label="state + identity")
axes[1].set_xticks(xpos); axes[1].set_xticklabels(s)
axes[1].set_xlabel("held-out test season")
axes[1].set_ylabel("E[runs] RMSE")
axes[1].set_title("State < state+identity every season")
axes[1].legend(frameon=False, fontsize=8)
fig.suptitle("Rolling-window evaluation: the identity result is not season-specific", y=1.04)
save(fig, "fig7_rolling_window")

print("done")
