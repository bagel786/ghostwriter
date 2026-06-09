"""Nested model ladder: LightGBM wicket (binary) & runs (Tweedie) heads,
GLM references (L2 logistic, Poisson), isotonic calibration, multinomial runs head."""
import numpy as np
import lightgbm as lgb
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression, PoissonRegressor
from sklearn.preprocessing import StandardScaler

from features import FEATURE_GROUPS

# nested ladder feature-group composition
LADDER = {
    "M_S":        ["S"],
    "M_SB":       ["S", "B"],
    "M_SW":       ["S", "W"],
    "M_SBW":      ["S", "B", "W"],
    "M_SBW+P":    ["S", "B", "W", "P"],
    "M_SBW+P+H":  ["S", "B", "W", "P", "H"],
}

LGB_FIXED = dict(learning_rate=0.03, n_estimators=600, num_leaves=31, max_depth=-1,
                 min_child_samples=200, subsample=0.8, colsample_bytree=0.8,
                 subsample_freq=1, n_jobs=-1, verbose=-1)


def cols_for(groups):
    cols = []
    for g in groups:
        cols += FEATURE_GROUPS[g]
    return cols


def fit_wicket_lgbm(X_tr, y_tr, X_val, y_val, seed=0, params=None):
    p = dict(LGB_FIXED)
    if params:
        p.update(params)
    m = lgb.LGBMClassifier(objective="binary", is_unbalance=True, random_state=seed, **p)
    m.fit(X_tr, y_tr, eval_set=[(X_val, y_val)], eval_metric="binary_logloss",
          callbacks=[lgb.early_stopping(50, verbose=False)])
    return m


def fit_runs_lgbm(X_tr, y_tr, X_val, y_val, seed=0, params=None, objective="tweedie"):
    p = dict(LGB_FIXED)
    if params:
        p.update(params)
    kw = {}
    if objective == "tweedie":
        kw["tweedie_variance_power"] = 1.3
    m = lgb.LGBMRegressor(objective=objective, random_state=seed, **p, **kw)
    m.fit(X_tr, y_tr, eval_set=[(X_val, y_val)], eval_metric="rmse",
          callbacks=[lgb.early_stopping(50, verbose=False)])
    return m


def fit_runs_multinomial_lgbm(X_tr, y_tr_class, X_val, y_val_class, seed=0, params=None):
    """y_*_class are integer-coded run classes (0..5 mapping to [0,1,2,3,4,6])."""
    p = dict(LGB_FIXED)
    if params:
        p.update(params)
    m = lgb.LGBMClassifier(objective="multiclass", random_state=seed, **p)
    m.fit(X_tr, y_tr_class, eval_set=[(X_val, y_val_class)], eval_metric="multi_logloss",
          callbacks=[lgb.early_stopping(50, verbose=False)])
    return m


def calibrate_isotonic(p_val, y_val):
    iso = IsotonicRegression(out_of_bounds="clip")
    iso.fit(p_val, y_val)
    return iso


def fit_glm_wicket(X_tr, y_tr):
    sc = StandardScaler()
    Xs = sc.fit_transform(np.nan_to_num(X_tr.values, nan=0.0))
    m = LogisticRegression(C=1.0, max_iter=2000, class_weight="balanced")
    m.fit(Xs, y_tr)
    return (sc, m)


def predict_glm_wicket(model, X):
    sc, m = model
    Xs = sc.transform(np.nan_to_num(X.values, nan=0.0))
    return m.predict_proba(Xs)[:, 1]


def fit_glm_runs(X_tr, y_tr):
    sc = StandardScaler()
    Xs = sc.fit_transform(np.nan_to_num(X_tr.values, nan=0.0))
    m = PoissonRegressor(alpha=1.0, max_iter=2000)
    m.fit(Xs, y_tr)
    return (sc, m)


def predict_glm_runs(model, X):
    sc, m = model
    Xs = sc.transform(np.nan_to_num(X.values, nan=0.0))
    return m.predict(Xs)
