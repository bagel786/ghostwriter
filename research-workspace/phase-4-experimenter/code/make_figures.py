"""Generate publication-ready figures from the experiment result CSVs.
Pure post-processing of saved results (no model refitting). Outputs PDF+PNG.
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

R = os.path.join(os.path.dirname(__file__), "..", "results")
FIG = os.path.join(R, "figures")
os.makedirs(FIG, exist_ok=True)

plt.rcParams.update({
    "font.size": 10, "axes.titlesize": 11, "axes.labelsize": 10,
    "figure.dpi": 150, "savefig.bbox": "tight", "axes.spines.top": False,
    "axes.spines.right": False, "font.family": "DejaVu Sans",
})
C = {"state": "#2c6fbb", "batter": "#d9722b", "bowler": "#3a9b6e",
     "naive": "#b0b0b0", "corr": "#2c6fbb", "bias": "#c44e52", "pos": "#2c6fbb", "neg": "#c44e52"}


def save(fig, name):
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(FIG, f"{name}.{ext}"))
    plt.close(fig)
    print("wrote", name)


# ---- Fig 1: grouped SHAP mass (H1) ----
att = pd.read_csv(os.path.join(R, "h1_attribution.csv"))
piv = att.pivot(index="target", columns="group", values="shap_pct").loc[["runs", "wicket"], ["S", "B", "W"]] * 100
fig, ax = plt.subplots(figsize=(5.2, 3.0))
labels = ["E[runs]", "P(wicket)"]
left = np.zeros(2)
for g, name, col in [("S", "Game state", C["state"]), ("B", "Batter id", C["batter"]), ("W", "Bowler id", C["bowler"])]:
    vals = piv[g].values
    ax.barh(labels, vals, left=left, color=col, label=name, edgecolor="white")
    for i, (v, l) in enumerate(zip(vals, left)):
        ax.text(l + v / 2, i, f"{v:.0f}%", ha="center", va="center", color="white", fontsize=9, fontweight="bold")
    left += vals
ax.set_xlabel("Share of total |SHAP| attribution")
ax.set_title("H1: SHAP attribution over-credits batter identity")
ax.set_xlim(0, 100)
ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.38), ncol=3, frameon=False)
save(fig, "fig1_grouped_shap")


# ---- Fig 2: H1 incremental held-out skill forest (identity over state) ----
inc = pd.read_csv(os.path.join(R, "h1_incremental_skill.csv"))
# normalize sign so positive = identity HELPS. wicket metric=logloss (lower better => skill stored as reduction);
# the CSV stores incr_skill where negative means worse. Plot as-is with zero line.
order = inc.reset_index(drop=True)
ylabels = [f"{r.target} : {r.added}" for r in order.itertuples()]
y = np.arange(len(order))[::-1]
fig, ax = plt.subplots(figsize=(5.6, 3.2))
for yi, r in zip(y, order.itertuples()):
    col = C["pos"] if r.incr_skill > 0 else C["neg"]
    ax.plot([r.ci_lo, r.ci_hi], [yi, yi], color=col, lw=2)
    ax.plot(r.incr_skill, yi, "o", color=col, ms=6)
ax.axvline(0, color="k", lw=0.8, ls="--")
ax.set_yticks(y)
ax.set_yticklabels(ylabels)
ax.set_xlabel("Incremental held-out skill of identity over state  (>0 = helps)")
ax.set_title("H1: identity adds no positive out-of-sample skill")
save(fig, "fig2_h1_incremental_forest")


# ---- Fig 3: model ladder skill (main_results) ----
mr = pd.read_csv(os.path.join(R, "main_results.csv"))
agg = mr.groupby(["model", "target"]).mean(numeric_only=True).reset_index()
ladder = ["M0", "M_S", "M_SB", "M_SW", "M_SBW", "M_SBW+P", "M_SBW+P+H"]
nice = {"M0": "base", "M_S": "+state", "M_SB": "+batter", "M_SW": "+bowler",
        "M_SBW": "+both", "M_SBW+P": "+PI", "M_SBW+P+H": "+history"}
fig, axes = plt.subplots(1, 2, figsize=(8.2, 3.2))
w = agg[agg.target == "wicket"].set_index("model").reindex(ladder)
axes[0].plot(range(len(ladder)), w["logloss"].values, "o-", color=C["state"])
axes[0].set_xticks(range(len(ladder)))
axes[0].set_xticklabels([nice[m] for m in ladder], rotation=45, ha="right")
axes[0].set_ylabel("log-loss  (lower better)")
axes[0].set_title("P(wicket): state-only is best")
ru = agg[agg.target == "runs"].set_index("model").reindex(ladder)
axes[1].plot(range(len(ladder)), ru["rmse"].values, "o-", color=C["batter"])
axes[1].set_xticks(range(len(ladder)))
axes[1].set_xticklabels([nice[m] for m in ladder], rotation=45, ha="right")
axes[1].set_ylabel("RMSE  (lower better)")
axes[1].set_title("E[runs]: history rung gives lowest RMSE")
fig.suptitle("Nested model ladder, held-out 2026 season (mean of 5 seeds)", y=1.02)
save(fig, "fig3_model_ladder")


# ---- Fig 4: H2 incremental skill (history beyond state+id+PI) ----
h2 = pd.read_csv(os.path.join(R, "h2_incremental.csv"))
fig, ax = plt.subplots(figsize=(5.6, 2.8))
rows = h2.reset_index(drop=True)
lab = [f"{r.target}\n({r.metric})" for r in rows.itertuples()]
y = np.arange(len(rows))[::-1]
for yi, r in zip(y, rows.itertuples()):
    sig = int(r.sig_ci_excl0) == 1
    col = C["pos"] if sig else C["naive"]
    ax.plot([r.ci_lo, r.ci_hi], [yi, yi], color=col, lw=2)
    ax.plot(r.delta, yi, "o", color=col, ms=6, label="sig (CI excl. 0)" if (sig and yi == y[-1]) else None)
ax.axvline(0, color="k", lw=0.8, ls="--")
ax.set_yticks(y)
ax.set_yticklabels(lab)
ax.set_xlabel("Δ skill of pressure-history beyond state+identity+PI  (>0 = helps)")
ax.set_title("H2: residual dot-ball pressure helps E[runs], not P(wicket)")
save(fig, "fig4_h2_incremental")


# ---- Fig 5: H3 Miller-Sanjurjo headline (primary k=1 scoring-shot, plus k sweep) ----
h3 = pd.read_csv(os.path.join(R, "h3_momentum.csv"))
prim = h3[(h3.unit == "batter_stay") & (h3.success_def == "score") & (h3.direction == "hot")].sort_values("k")
fig, axes = plt.subplots(1, 2, figsize=(8.4, 3.3))
# left: decomposition for k=1
p1 = prim[prim.k == 1].iloc[0]
bars = ["naive\nD̂", "MS bias\nE₀", "corrected\nD̃"]
vals = [p1.D_naive, p1.mean_bias, p1.D_corrected]
cols = [C["naive"], C["bias"], C["corr"]]
axes[0].bar(bars, vals, color=cols)
axes[0].axhline(0, color="k", lw=0.8)
for i, v in enumerate(vals):
    axes[0].text(i, v + (0.004 if v >= 0 else -0.004), f"{v:+.3f}", ha="center",
                 va="bottom" if v >= 0 else "top", fontsize=9)
axes[0].set_ylabel("P(score | streak) − P(score | no streak)")
axes[0].set_title("H3 (k=1): naive 'cold hand' is\nalmost entirely MS selection bias")
# right: naive vs corrected across k
axes[1].plot(prim.k, prim.D_naive, "o-", color=C["naive"], label="naive D̂")
axes[1].plot(prim.k, prim.D_corrected, "s-", color=C["corr"], label="corrected D̃")
axes[1].axhline(0, color="k", lw=0.8, ls="--")
axes[1].set_xticks([1, 2, 3])
axes[1].set_xlabel("streak length k (consecutive dots, hot-hand test)")
axes[1].set_ylabel("momentum estimate")
axes[1].set_title("Bias grows with k; corrected stays ≈ 0")
axes[1].legend(frameon=False)
fig.suptitle("H3: Miller–Sanjurjo correction removes apparent death-over momentum", y=1.12)
fig.subplots_adjust(top=0.74)
save(fig, "fig5_h3_momentum")

print("\nAll figures written to", FIG)
