"""
Feature engineering: state (S), batter identity (B), bowler identity (W),
deterministic pressure index (P), pressure history (H).
Identity encodings are EB-shrunk and historical-only (computed from deliveries
strictly before each match's start_date) to avoid leakage.
"""
import numpy as np
import pandas as pd

# ---- feature group definitions (each column -> exactly one group) ----
GROUP_S = [
    "balls_remaining_innings", "over", "ball_in_over", "wickets_in_hand",
    "current_score", "current_run_rate", "is_chase", "innings", "target",
    "runs_required", "balls_remaining", "required_run_rate", "rrr_minus_crr",
    "wickets_lost_so_far",
]
GROUP_B = ["bat_deathSR", "bat_boundary_pct", "bat_dot_pct", "bat_dismissal_rate", "bat_n_prior_balls"]
GROUP_W = ["bowl_deathER", "bowl_dot_pct", "bowl_wicket_rate", "bowl_boundary_conceded_pct", "bowl_n_prior_balls"]
GROUP_P = ["PI"]
GROUP_H = ["dot_run_len", "dot_run_len_partnership", "balls_since_wicket",
           "balls_since_boundary", "dot_run_len_x_rrr"]

FEATURE_GROUPS = {"S": GROUP_S, "B": GROUP_B, "W": GROUP_W, "P": GROUP_P, "H": GROUP_H}


def add_pressure_index(df):
    """Group P: Bhattacharjee-Lemmer-style deterministic pressure index (chase only)."""
    df = df.copy()
    # initial rrr at start of over 16 (over index 15) per match-innings (chase only)
    start_rows = df[(df["over"] == 15) & (df["ball_in_over"] == 1) & (df["is_chase"] == 1)]
    init_rrr = start_rows.groupby(["match_id"])["required_run_rate"].first()
    df["init_rrr16"] = df["match_id"].map(init_rrr)
    balls_used_frac = (120 - df["balls_remaining_innings"]) / 120.0
    w_wkts = 1 + (df["wickets_lost_so_far"] / 10.0)
    rrr_ratio = df["required_run_rate"] / df["init_rrr16"]
    pi = rrr_ratio * w_wkts * balls_used_frac
    df["PI"] = np.where(df["is_chase"] == 1, pi, np.nan)
    df["PI"] = df["PI"].replace([np.inf, -np.inf], np.nan)
    return df


def add_history_features(df):
    """Group H: pressure history on legal striker-faced balls, reset at innings start.
    NOTE: these are computed across ALL death-over legal balls within a match-innings,
    ordered by ball. dot_run_len = consecutive immediately-preceding dots faced by striker."""
    df = df.sort_values(["match_id", "innings", "ball"]).reset_index(drop=True)
    df["dot_run_len"] = 0
    df["dot_run_len_partnership"] = 0
    df["balls_since_wicket"] = 0
    df["balls_since_boundary"] = 0

    out_dot = np.zeros(len(df), dtype=float)
    out_dot_p = np.zeros(len(df), dtype=float)
    out_bsw = np.zeros(len(df), dtype=float)
    out_bsb = np.zeros(len(df), dtype=float)

    ball = df["ball"].values
    legal = df["legal"].values
    runs = df["runs_off_bat"].values
    wicket_any = df["wicket_any"].values
    striker = df["striker"].values
    mi = (df["match_id"].astype(str) + "|" + df["innings"].astype(str)).values

    # per-striker dot run (within match-innings), partnership-level dot run, balls since wkt/boundary
    cur_key = None
    striker_dot = {}     # striker -> current consecutive dot count (faced)
    part_dot = 0         # partnership-level consecutive dot (legal, any striker)
    bsw = 0              # legal balls since last wicket (partnership-level)
    bsb = 0              # legal balls since last boundary
    for i in range(len(df)):
        if mi[i] != cur_key:
            cur_key = mi[i]
            striker_dot = {}
            part_dot = 0
            bsw = 0
            bsb = 0
        s = striker[i]
        # record state BEFORE this ball's outcome
        out_dot[i] = striker_dot.get(s, 0)
        out_dot_p[i] = part_dot
        out_bsw[i] = bsw
        out_bsb[i] = bsb
        # update with this ball's outcome (only legal balls advance streaks)
        if legal[i] == 1:
            if runs[i] == 0 and wicket_any[i] == 0:
                striker_dot[s] = striker_dot.get(s, 0) + 1
                part_dot += 1
            else:
                striker_dot[s] = 0
                part_dot = 0
            bsw = 0 if wicket_any[i] == 1 else bsw + 1
            if runs[i] in (4, 6):
                bsb = 0
            else:
                bsb = bsb + 1
    df["dot_run_len"] = out_dot
    df["dot_run_len_partnership"] = out_dot_p
    df["balls_since_wicket"] = out_bsw
    df["balls_since_boundary"] = out_bsb
    df["dot_run_len_x_rrr"] = np.where(df["is_chase"] == 1,
                                       df["dot_run_len"] * df["required_run_rate"].fillna(0), 0.0)
    return df


def _eb_encode(stat_n, stat_rate, alpha, prior):
    return (stat_n * stat_rate + alpha * prior) / (stat_n + alpha)


def fit_identity_encoders(hist_df, alpha=50):
    """Compute per-player EB-shrunk death-over rates from a HISTORICAL dataframe
    (legal death balls only). Returns dict of lookup tables + global priors."""
    h = hist_df[hist_df["legal"] == 1].copy()
    # global death priors
    g_sr = h["runs_off_bat"].mean() * 100  # SR per 100 balls (runs/ball*100)
    g_bnd = h["runs_off_bat"].isin([4, 6]).mean()
    g_dot = (h["runs_off_bat"] == 0).mean()
    g_bat_dismiss = h["wicket"].mean()
    g_er = h["runs_off_bat"].mean() * 6  # economy: runs/over off bat
    g_bowl_wkt = h["wicket"].mean()

    # batter aggregates
    bat = h.groupby("striker").agg(
        n=("runs_off_bat", "size"),
        runs=("runs_off_bat", "sum"),
        bnd=("runs_off_bat", lambda x: x.isin([4, 6]).mean()),
        dot=("runs_off_bat", lambda x: (x == 0).mean()),
        dismiss=("wicket", "mean"),
    )
    bat["sr"] = bat["runs"] / bat["n"] * 100
    bat_enc = pd.DataFrame(index=bat.index)
    bat_enc["bat_deathSR"] = _eb_encode(bat["n"], bat["sr"], alpha, g_sr)
    bat_enc["bat_boundary_pct"] = _eb_encode(bat["n"], bat["bnd"], alpha, g_bnd)
    bat_enc["bat_dot_pct"] = _eb_encode(bat["n"], bat["dot"], alpha, g_dot)
    bat_enc["bat_dismissal_rate"] = _eb_encode(bat["n"], bat["dismiss"], alpha, g_bat_dismiss)
    bat_enc["bat_n_prior_balls"] = bat["n"]

    bowl = h.groupby("bowler").agg(
        n=("runs_off_bat", "size"),
        runs=("runs_off_bat", "sum"),
        bnd=("runs_off_bat", lambda x: x.isin([4, 6]).mean()),
        dot=("runs_off_bat", lambda x: (x == 0).mean()),
        wkt=("wicket", "mean"),
    )
    bowl["er"] = bowl["runs"] / bowl["n"] * 6
    bowl_enc = pd.DataFrame(index=bowl.index)
    bowl_enc["bowl_deathER"] = _eb_encode(bowl["n"], bowl["er"], alpha, g_er)
    bowl_enc["bowl_dot_pct"] = _eb_encode(bowl["n"], bowl["dot"], alpha, g_dot)
    bowl_enc["bowl_wicket_rate"] = _eb_encode(bowl["n"], bowl["wkt"], alpha, g_bowl_wkt)
    bowl_enc["bowl_boundary_conceded_pct"] = _eb_encode(bowl["n"], bowl["bnd"], alpha, g_bnd)
    bowl_enc["bowl_n_prior_balls"] = bowl["n"]

    priors = {
        "bat_deathSR": g_sr, "bat_boundary_pct": g_bnd, "bat_dot_pct": g_dot,
        "bat_dismissal_rate": g_bat_dismiss, "bat_n_prior_balls": 0.0,
        "bowl_deathER": g_er, "bowl_dot_pct": g_dot, "bowl_wicket_rate": g_bowl_wkt,
        "bowl_boundary_conceded_pct": g_bnd, "bowl_n_prior_balls": 0.0,
    }
    return {"bat": bat_enc, "bowl": bowl_enc, "priors": priors}


def apply_identity_encoders(df, encoders, shuffle_seed=None):
    """Map encodings onto df. If shuffle_seed is set, shuffle the player->encoding mapping
    (placebo). Unseen players -> prior."""
    df = df.copy()
    bat_enc = encoders["bat"]
    bowl_enc = encoders["bowl"]
    priors = encoders["priors"]

    if shuffle_seed is not None:
        rng = np.random.default_rng(shuffle_seed)
        bat_enc = bat_enc.sample(frac=1.0, random_state=shuffle_seed)
        bat_enc.index = encoders["bat"].index  # rows shuffled, labels original -> placebo
        bowl_enc = bowl_enc.sample(frac=1.0, random_state=shuffle_seed + 1)
        bowl_enc.index = encoders["bowl"].index

    for col in GROUP_B:
        df[col] = df["striker"].map(bat_enc[col]).fillna(priors[col])
    for col in GROUP_W:
        df[col] = df["bowler"].map(bowl_enc[col]).fillna(priors[col])
    return df


def attach_historical_identity(all_death, train_max_year, alpha=50):
    """Build identity encoders from death deliveries strictly before each split.
    Simplification respecting temporal split: encoders fit on all death deliveries with
    season_year <= train_max_year (the train+val pool boundary handled by caller via
    per-split encoder fitting). Returns encoders fit on the supplied historical pool."""
    hist = all_death[all_death["season_year"] <= train_max_year]
    return fit_identity_encoders(hist, alpha=alpha)
