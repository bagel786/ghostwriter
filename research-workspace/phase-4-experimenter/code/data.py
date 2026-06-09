"""
Data loading & preprocessing for Cricsheet T20 death-over analysis.
Parses per-match CSVs (csv2 format), filters death overs (16-20 => over index 15-19),
builds targets, flags legal balls and DL-affected matches.
"""
import glob
import os
import re
import numpy as np
import pandas as pd

BATTER_WICKETS = {"bowled", "caught", "lbw", "stumped", "caught and bowled", "hit wicket"}

PER_BALL_COLS = [
    "match_id", "season", "start_date", "venue", "innings", "ball",
    "batting_team", "bowling_team", "striker", "non_striker", "bowler",
    "runs_off_bat", "extras", "wides", "noballs", "byes", "legbyes", "penalty",
    "wicket_type", "player_dismissed", "other_wicket_type", "other_player_dismissed",
]


def _season_to_year(s):
    """Cricsheet season can be '2017' or '2007/08'. Map to a single int year (the later year)."""
    if pd.isna(s):
        return np.nan
    s = str(s)
    m = re.match(r"^(\d{4})/(\d{2})$", s)
    if m:
        base = int(m.group(1))
        return base + 1  # 2007/08 -> 2008
    m = re.match(r"^(\d{4})", s)
    if m:
        return int(m.group(1))
    return np.nan


def _dl_affected_matches(info_paths):
    """Return set of match_ids whose info.csv contains a D/L method line."""
    dl = set()
    for p in info_paths:
        mid = os.path.basename(p).replace("_info.csv", "")
        try:
            with open(p, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if line.startswith("info,method"):
                        dl.add(mid)
                        break
        except Exception:
            pass
    return dl


def load_raw(raw_dir, leagues=("ipl", "t20s")):
    """Concatenate all per-match CSVs across requested leagues."""
    frames = []
    dl_all = set()
    for lg in leagues:
        ddir = os.path.join(raw_dir, lg)
        match_files = [f for f in glob.glob(os.path.join(ddir, "*.csv"))
                       if not f.endswith("_info.csv") and "all_matches" not in os.path.basename(f)]
        info_files = glob.glob(os.path.join(ddir, "*_info.csv"))
        dl_all |= _dl_affected_matches(info_files)
        print(f"  [{lg}] {len(match_files)} match files")
        for mf in match_files:
            try:
                df = pd.read_csv(mf, dtype={"match_id": str}, low_memory=False)
                df["league"] = lg
                frames.append(df)
            except Exception as e:
                print(f"    skip {mf}: {e}")
    full = pd.concat(frames, ignore_index=True)
    full["dl_affected"] = full["match_id"].astype(str).isin(dl_all).astype(int)
    print(f"  total deliveries (all overs, both leagues): {len(full):,}")
    print(f"  DL-affected matches flagged: {len(dl_all):,}")
    return full


def derive_and_filter(df, death_over_idx=(15, 16, 17, 18, 19)):
    """Derive over/ball_in_over, build targets, filter to death overs. Returns full-innings
    table too so we can compute running state correctly before filtering."""
    df = df.copy()
    for c in ["runs_off_bat", "extras", "wides", "noballs", "byes", "legbyes", "penalty"]:
        if c not in df.columns:
            df[c] = 0
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

    df["ball"] = pd.to_numeric(df["ball"], errors="coerce")
    df["over"] = np.floor(df["ball"]).astype(int)
    df["ball_in_over"] = (np.round((df["ball"] - df["over"]) * 10)).astype(int)
    df["innings"] = pd.to_numeric(df["innings"], errors="coerce")
    # restrict to first two innings (ignore super overs etc.)
    df = df[df["innings"].isin([1, 2])].copy()
    df["innings"] = df["innings"].astype(int)

    df["season"] = df["season"].astype(str)
    df["season_year"] = df["season"].map(_season_to_year)
    df["legal"] = ((df["wides"] == 0) & (df["noballs"] == 0)).astype(int)

    # batter-credited wicket
    wt = df["wicket_type"].astype(str).str.strip().str.lower()
    pd_nonnull = df["player_dismissed"].notna() & (df["player_dismissed"].astype(str).str.len() > 0)
    df["wicket"] = (pd_nonnull & wt.isin(BATTER_WICKETS)).astype(int)
    # any dismissal on this ball (incl run-outs etc.)
    any_dismiss = pd_nonnull | (df["other_player_dismissed"].notna() &
                                (df["other_player_dismissed"].astype(str).str.len() > 0))
    df["wicket_any"] = any_dismiss.astype(int)

    df["total_runs"] = df["runs_off_bat"] + df["extras"]
    df["is_extra_ball"] = (df["legal"] == 0).astype(int)

    # ---- running state computed over the FULL innings (then filter) ----
    df = df.sort_values(["match_id", "innings", "ball"]).reset_index(drop=True)
    g = df.groupby(["match_id", "innings"], sort=False)
    # legal balls bowled so far (exclusive of current)
    df["legal_cum"] = g["legal"].cumsum()
    df["legal_before"] = df["legal_cum"] - df["legal"]
    # cumulative score before this ball
    df["score_cum"] = g["total_runs"].cumsum()
    df["current_score"] = df["score_cum"] - df["total_runs"]
    # wickets fallen before this ball (use wicket_any for "wickets in hand" realism)
    df["wkt_cum"] = g["wicket_any"].cumsum()
    df["wickets_lost_so_far"] = df["wkt_cum"] - df["wicket_any"]
    df["wickets_in_hand"] = 10 - df["wickets_lost_so_far"]
    df["balls_remaining_innings"] = 120 - df["legal_before"]
    crr = df["current_score"] / (df["legal_before"] / 6.0)
    df["current_run_rate"] = crr.replace([np.inf, -np.inf], np.nan)

    # innings-1 final score => target for innings-2 (chase)
    inn1 = df[df["innings"] == 1].groupby("match_id")["total_runs"].sum()
    df["inn1_total"] = df["match_id"].map(inn1)
    df["target"] = np.where(df["innings"] == 2, df["inn1_total"] + 1, np.nan)
    df["is_chase"] = (df["innings"] == 2).astype(int)
    df["runs_required"] = np.where(df["innings"] == 2, df["target"] - df["current_score"], np.nan)
    df["balls_remaining"] = np.where(df["innings"] == 2, df["balls_remaining_innings"], np.nan)
    rrr = df["runs_required"] / (df["balls_remaining"] / 6.0)
    df["required_run_rate"] = rrr.replace([np.inf, -np.inf], np.nan)
    df["rrr_minus_crr"] = df["required_run_rate"] - df["current_run_rate"]
    # blank out RRR features for DL-affected chases
    dl_chase = (df["dl_affected"] == 1) & (df["innings"] == 2)
    for c in ["target", "runs_required", "required_run_rate", "rrr_minus_crr", "balls_remaining"]:
        df.loc[dl_chase, c] = np.nan

    # death filter
    death = df[df["over"].isin(death_over_idx)].copy().reset_index(drop=True)
    return death


def basic_sanity(death):
    print("\n=== SANITY CHECKS (death overs) ===")
    print(f"death deliveries: {len(death):,}")
    print(f"unique matches: {death['match_id'].nunique():,}")
    print(f"seasons: {sorted(death['season_year'].dropna().unique().astype(int).tolist())}")
    print(f"runs_off_bat value counts:\n{death['runs_off_bat'].value_counts().sort_index()}")
    print(f"legal frac: {death['legal'].mean():.3f}")
    print(f"wicket rate (batter-credited, legal): "
          f"{death.loc[death['legal']==1,'wicket'].mean():.4f}")
    print(f"wicket_any rate (legal): {death.loc[death['legal']==1,'wicket_any'].mean():.4f}")
    print(f"mean runs_off_bat (legal): {death.loc[death['legal']==1,'runs_off_bat'].mean():.3f}")
    print(f"by league:\n{death.groupby('league').size()}")
