"""H3: Miller-Sanjurjo streak-selection-bias correction + within-state permutation null.
Model-free analysis on per-ball death-over success sequences (legal striker-faced balls)."""
import numpy as np
from math import comb
from itertools import combinations


def build_sequences(df, unit="batter_stay", success="score"):
    """Return list of dicts: {x: np.array of 0/1 outcomes, strata: np.array of stratum ids}.
    Legal balls only. A wicket ENDS a sequence (the wicket ball itself is excluded as an
    outcome value). success='score' => runs_off_bat>=1; 'boundary' => in {4,6}."""
    d = df[df["legal"] == 1].copy()
    d = d.sort_values(["match_id", "innings", "ball"]).reset_index(drop=True)

    if success == "score":
        d["succ"] = (d["runs_off_bat"] >= 1).astype(int)
    elif success == "boundary":
        d["succ"] = d["runs_off_bat"].isin([4, 6]).astype(int)
    else:
        raise ValueError(success)

    # stratum id for state-stratified null
    if "stratum" not in d.columns:
        d["stratum"] = _make_strata(d)

    seqs = []
    if unit == "batter_stay":
        keys = ["match_id", "innings", "striker"]
    elif unit == "within_over":
        keys = ["match_id", "innings", "over"]
    elif unit == "partnership":
        keys = ["match_id", "innings"]
    else:
        raise ValueError(unit)

    for _, grp in d.groupby(keys, sort=False):
        grp = grp.sort_values("ball")
        x = grp["succ"].values.astype(int)
        strata = grp["stratum"].values
        wkt = grp["wicket_any"].values
        # cut sequence at a wicket (exclude the wicket-ball outcome, end the stay)
        if unit in ("batter_stay", "partnership"):
            cut = np.where(wkt == 1)[0]
            if len(cut) > 0:
                end = cut[0]  # end before first wicket
                x = x[:end]
                strata = strata[:end]
        if len(x) >= 2:
            seqs.append({"x": x, "strata": strata})
    return seqs


def _make_strata(d):
    over = d["over"].values
    wih = np.clip(d["wickets_in_hand"].values, 0, 10)
    wih_b = np.where(wih >= 7, 2, np.where(wih >= 4, 1, 0))
    # rrr bucket (chase) else score bucket
    rrr = d["required_run_rate"].values
    score = d["current_score"].values
    state_b = np.where(~np.isnan(rrr),
                       np.clip(np.nan_to_num(rrr, nan=0) // 4, 0, 4),  # rrr buckets of width 4
                       10 + np.clip(score // 40, 0, 5))               # score buckets width 40
    sid = over.astype(int) * 1000 + wih_b.astype(int) * 100 + state_b.astype(int)
    return sid


def naive_D(x, k, direction="hot"):
    """direction='hot': P(x=1 | k preceding 1s) - P(x=1 | k preceding 0s).
    direction='cold': P(x=1 | k preceding 0s) - overall (the after-dot momentum quantity).
    Returns (D, n_valid_after_streak). NaN if conditioning arm(s) empty.
    Vectorized with numpy rolling windows."""
    x = np.asarray(x, dtype=np.int8)
    n = len(x)
    if n <= k:
        return np.nan, 0
    # rolling sum of k preceding values for each target index t in [k, n)
    csum = np.concatenate([[0], np.cumsum(x)])
    # preceding-window sum for t: x[t-k:t] => csum[t]-csum[t-k]
    t_idx = np.arange(k, n)
    win_sum = csum[t_idx] - csum[t_idx - k]
    targets = x[t_idx]
    after1 = win_sum == k          # all preceding ones
    after0 = win_sum == 0          # all preceding zeros
    n1 = after1.sum(); n0 = after0.sum()
    if direction == "hot":
        if n1 == 0 or n0 == 0:
            return np.nan, 0
        D = targets[after1].mean() - targets[after0].mean()
        return float(D), int(n1)
    elif direction == "cold":
        if n0 == 0:
            return np.nan, 0
        D = targets[after0].mean() - x.mean()
        return float(D), int(n0)
    else:
        raise ValueError(direction)


# memoize MS bias by (n, s, k, direction) since E0 depends only on these
_E0_CACHE = {}


def ms_expected_D(x, k, direction="hot", max_perm=2000, rng=None):
    """Expected naive_D over all rearrangements of the multiset (preserving #successes).
    E0 depends only on (n, s, k, direction); memoized. Exact enumeration if C(n,s)<=max_perm
    else MC sample. Returns the MS bias E0."""
    x = np.asarray(x, dtype=np.int8)
    n = len(x)
    s = int(x.sum())
    if s == 0 or s == n:
        return np.nan
    key = (n, s, k, direction)
    cached = _E0_CACHE.get(key)
    if cached is not None:
        return cached
    total = comb(n, s)
    vals = []
    if total <= max_perm:
        base = np.zeros(n, dtype=np.int8)
        for ones_pos in combinations(range(n), s):
            arr = base.copy()
            arr[list(ones_pos)] = 1
            D, _ = naive_D(arr, k, direction)
            if not np.isnan(D):
                vals.append(D)
    else:
        if rng is None:
            rng = np.random.default_rng(0)
        arr = np.zeros(n, dtype=np.int8); arr[:s] = 1
        for _ in range(max_perm):
            rng.shuffle(arr)
            D, _ = naive_D(arr, k, direction)
            if not np.isnan(D):
                vals.append(D)
    out = float(np.mean(vals)) if len(vals) else np.nan
    _E0_CACHE[key] = out
    return out


def corrected_aggregate(seqs, k, direction="hot", max_perm=2000, seed=0):
    """Per-sequence D, E0, D_tilde; exposure-weighted aggregates.
    Returns dict with D_naive, D_corrected, gap, and arrays for permutation reuse."""
    rng = np.random.default_rng(seed)
    Ds, E0s, ws = [], [], []
    for sq in seqs:
        x = sq["x"]
        D, nv = naive_D(x, k, direction)
        if np.isnan(D) or nv == 0:
            continue
        E0 = ms_expected_D(x, k, direction, max_perm=max_perm, rng=rng)
        if np.isnan(E0):
            continue
        Ds.append(D); E0s.append(E0); ws.append(nv)
    Ds = np.array(Ds); E0s = np.array(E0s); ws = np.array(ws, dtype=float)
    if ws.sum() == 0:
        return dict(D_naive=np.nan, D_corrected=np.nan, gap=np.nan, n_seq=0,
                    mean_bias=np.nan)
    D_naive = np.sum(ws * Ds) / np.sum(ws)
    D_tilde = Ds - E0s
    D_corrected = np.sum(ws * D_tilde) / np.sum(ws)
    return dict(D_naive=float(D_naive), D_corrected=float(D_corrected),
                gap=float(D_corrected - D_naive), n_seq=len(Ds),
                mean_bias=float(np.sum(ws * E0s) / np.sum(ws)))


def perm_null_unconditional(seqs, k, direction="hot", observed=None, B=5000, seed=0):
    """Within-sequence shuffle (preserve #successes per sequence) -> null for the NAIVE
    aggregate D_naive (the standard MS/GVT permutation test). Two-sided p."""
    rng = np.random.default_rng(seed)
    # precompute per-seq arrays and weights using naive D on observed
    arrs = [sq["x"].copy() for sq in seqs]
    obs_vals = []
    ws = []
    for x in arrs:
        D, nv = naive_D(x, k, direction)
        if np.isnan(D) or nv == 0:
            continue
        obs_vals.append((x, D, nv))
    if len(obs_vals) == 0:
        return np.nan, np.nan
    xs = [o[0] for o in obs_vals]
    w = np.array([o[2] for o in obs_vals], dtype=float)
    D_obs = np.sum(np.array([o[1] for o in obs_vals]) * w) / w.sum() if observed is None else observed

    null_stats = np.empty(B)
    for b in range(B):
        ds = np.empty(len(xs))
        for i, x in enumerate(xs):
            xp = x.copy()
            rng.shuffle(xp)
            D, _ = naive_D(xp, k, direction)
            ds[i] = D if not np.isnan(D) else 0.0
        null_stats[b] = np.sum(ds * w) / w.sum()
    p = (np.sum(np.abs(null_stats) >= abs(D_obs)) + 1) / (B + 1)
    return float(p), float(D_obs)


def perm_null_state_stratified(seqs, k, direction="hot", observed=None, B=2000,
                               max_perm=2000, seed=0):
    """State-stratified permutation: permute outcomes only within state strata (across the
    whole pool), then re-segment back into the original sequence shapes and recompute the
    CORRECTED aggregate. Tests momentum BEYOND state. Two-sided p vs observed D_corrected."""
    rng = np.random.default_rng(seed)
    # observed corrected aggregate
    if observed is None:
        obs = corrected_aggregate(seqs, k, direction, max_perm=max_perm, seed=seed)
        observed = obs["D_corrected"]
    if np.isnan(observed):
        return np.nan, observed

    # Build a global pool: for each stratum, collect all outcome values across sequences,
    # remembering (seq_idx, position). Permuting within stratum reassigns outcomes while
    # preserving each stratum's base rate.
    seq_lens = [len(sq["x"]) for sq in seqs]
    strata_concat = np.concatenate([sq["strata"] for sq in seqs])
    x_concat = np.concatenate([sq["x"] for sq in seqs])
    offsets = np.concatenate([[0], np.cumsum(seq_lens)])
    uniq_strata = np.unique(strata_concat)
    strata_idx = {s: np.where(strata_concat == s)[0] for s in uniq_strata}

    seg_bounds = [(offsets[i], offsets[i + 1]) for i in range(len(seqs))]
    null_stats = np.empty(B)
    for b in range(B):
        xp = x_concat.copy()
        # permute outcome VALUES within each state stratum (preserves stratum base rate)
        for s in uniq_strata:
            idx = strata_idx[s]
            vals = xp[idx]
            xp[idx] = rng.permutation(vals)
        # recompute corrected aggregate inline (memoized E0)
        Ds = []; E0s = []; ws = []
        for (a, z) in seg_bounds:
            seg = xp[a:z]
            D, nv = naive_D(seg, k, direction)
            if np.isnan(D) or nv == 0:
                continue
            E0 = ms_expected_D(seg, k, direction, max_perm=max_perm, rng=rng)
            if np.isnan(E0):
                continue
            Ds.append(D); E0s.append(E0); ws.append(nv)
        if len(ws) == 0:
            null_stats[b] = 0.0
            continue
        Ds = np.array(Ds); E0s = np.array(E0s); ws = np.array(ws, dtype=float)
        null_stats[b] = np.sum(ws * (Ds - E0s)) / ws.sum()
    p = (np.sum(np.abs(null_stats) >= abs(observed)) + 1) / (B + 1)
    return float(p), float(observed)


def bh_fdr(pvals):
    """Benjamini-Hochberg adjusted p-values."""
    p = np.array(pvals, dtype=float)
    mask = ~np.isnan(p)
    out = np.full_like(p, np.nan)
    pv = p[mask]
    n = len(pv)
    order = np.argsort(pv)
    ranked = pv[order]
    adj = ranked * n / (np.arange(1, n + 1))
    adj = np.minimum.accumulate(adj[::-1])[::-1]
    adj = np.clip(adj, 0, 1)
    res = np.empty(n)
    res[order] = adj
    out[mask] = res
    return out
