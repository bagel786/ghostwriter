"""H1 attribution: grouped TreeSHAP mass per feature group; leakage audit (identity vs state)."""
import numpy as np
import pandas as pd
import shap
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler

from features import FEATURE_GROUPS


def _col_to_group(cols):
    mapping = {}
    for g, gc in FEATURE_GROUPS.items():
        for c in gc:
            if c in cols:
                mapping[c] = g
    return mapping


def grouped_shap(model, X, n_sample=20000, seed=0):
    """TreeSHAP on a sampled subset; return dict group -> % of total mean(|SHAP|)."""
    if len(X) > n_sample:
        X = X.sample(n_sample, random_state=seed)
    expl = shap.TreeExplainer(model)
    sv = expl.shap_values(X)
    # binary classifier may return list [neg, pos] or array
    if isinstance(sv, list):
        sv = sv[1] if len(sv) == 2 else sv[0]
    sv = np.asarray(sv)
    if sv.ndim == 3:  # (N, F, classes)
        sv = sv[:, :, -1]
    mean_abs = np.abs(sv).mean(axis=0)  # per feature
    mapping = _col_to_group(list(X.columns))
    grp_mass = {}
    for i, c in enumerate(X.columns):
        g = mapping.get(c, "?")
        grp_mass[g] = grp_mass.get(g, 0.0) + mean_abs[i]
    total = sum(grp_mass.values())
    return {g: (v / total if total > 0 else np.nan) for g, v in grp_mass.items()}


def leakage_audit(df, identity_cols, state_cols):
    """Regress each identity feature on state features; report R^2."""
    Xs = df[state_cols].copy()
    Xs = Xs.fillna(Xs.median(numeric_only=True)).fillna(0.0)
    scaler = StandardScaler()
    Xs_ = scaler.fit_transform(Xs.values)
    rows = []
    for c in identity_cols:
        y = df[c].fillna(df[c].median()).values
        if np.std(y) < 1e-9:
            rows.append((c, np.nan)); continue
        lr = LinearRegression().fit(Xs_, y)
        r2 = lr.score(Xs_, y)
        rows.append((c, float(r2)))
    return pd.DataFrame(rows, columns=["identity_feature", "r2_vs_state"])
