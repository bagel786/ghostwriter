"""Metric computation: log-loss, Brier, ECE, PR-AUC (wicket); RMSE, MAE, CRPS (runs);
match-clustered bootstrap CIs."""
import numpy as np
from sklearn.metrics import log_loss as sk_log_loss, brier_score_loss, average_precision_score

RUN_CLASSES = np.array([0, 1, 2, 3, 4, 6])
EPS = 1e-12


def log_loss_binary(y, p):
    p = np.clip(p, EPS, 1 - EPS)
    return -np.mean(y * np.log(p) + (1 - y) * np.log(1 - p))


def brier(y, p):
    return np.mean((p - y) ** 2)


def ece(y, p, n_bins=10):
    bins = np.linspace(0, 1, n_bins + 1)
    idx = np.digitize(p, bins) - 1
    idx = np.clip(idx, 0, n_bins - 1)
    e = 0.0
    n = len(y)
    for b in range(n_bins):
        m = idx == b
        if m.sum() == 0:
            continue
        conf = p[m].mean()
        acc = y[m].mean()
        e += (m.sum() / n) * abs(acc - conf)
    return e


def pr_auc(y, p):
    if y.sum() == 0 or y.sum() == len(y):
        return np.nan
    return average_precision_score(y, p)


def rmse(y, yhat):
    return float(np.sqrt(np.mean((y - yhat) ** 2)))


def mae(y, yhat):
    return float(np.mean(np.abs(y - yhat)))


def crps_multinomial(y_true, prob_matrix, classes=RUN_CLASSES):
    """CRPS for a discrete predictive distribution over `classes`.
    prob_matrix: (N, K). y_true: actual run value. Uses the integral of squared
    CDF differences over the ordered support."""
    classes = np.asarray(classes)
    order = np.argsort(classes)
    classes = classes[order]
    P = prob_matrix[:, order]
    cdf_pred = np.cumsum(P, axis=1)  # (N,K)
    y = np.asarray(y_true)
    # step CDF of the observation at each class threshold: 1 if class>=y
    obs_cdf = (classes[None, :] >= y[:, None]).astype(float)
    # integrate over support intervals; use unit weights between consecutive classes
    # CRPS_discrete = sum_k (cdf_pred_k - obs_cdf_k)^2 * width_k
    widths = np.diff(np.concatenate([classes, [classes[-1] + 1]]))
    crps = np.sum((cdf_pred - obs_cdf) ** 2 * widths[None, :], axis=1)
    return float(np.mean(crps))


def expected_runs_calibration(y, yhat, n_bins=10):
    bins = np.quantile(yhat, np.linspace(0, 1, n_bins + 1))
    bins = np.unique(bins)
    idx = np.clip(np.digitize(yhat, bins) - 1, 0, len(bins) - 2)
    rows = []
    for b in range(len(bins) - 1):
        m = idx == b
        if m.sum() == 0:
            continue
        rows.append((float(yhat[m].mean()), float(y[m].mean()), int(m.sum())))
    return rows


def match_clustered_bootstrap(match_ids, compute_fn, B=1000, seed=0):
    """Resample whole matches with replacement; compute_fn(mask_or_idx_for_resample) -> scalar.
    We pass resampled row indices. Returns (point, lo, hi)."""
    rng = np.random.default_rng(seed)
    match_ids = np.asarray(match_ids)
    uniq = np.unique(match_ids)
    # precompute row indices per match
    idx_by_match = {m: np.where(match_ids == m)[0] for m in uniq}
    point = compute_fn(np.arange(len(match_ids)))
    stats = np.empty(B)
    for b in range(B):
        sampled = rng.choice(uniq, size=len(uniq), replace=True)
        rows = np.concatenate([idx_by_match[m] for m in sampled])
        stats[b] = compute_fn(rows)
    lo, hi = np.nanpercentile(stats, [2.5, 97.5])
    return float(point), float(lo), float(hi)
