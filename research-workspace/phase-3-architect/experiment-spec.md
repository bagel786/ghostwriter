# Experiment Spec

## Hypothesis
In T20 death overs (16–20), game state explains more per-ball outcome variation than batter–bowler identity (identity helping E[runs] more than P[wicket]) (H1); a residual dot-ball-run effect raises next-ball wicket probability / lowers expected runs beyond state, violating the Markov assumption (H2); and the Miller–Sanjurjo streak-selection-bias correction (+ state-stratified permutation tests) materially changes the estimated per-ball momentum effect relative to the naive estimator (H3, headline).

## Environment
- Python version: 3.11 (3.10+ fine)
- Key libraries: pandas, numpy, scipy, scikit-learn, lightgbm, shap, statsmodels, matplotlib, requests, pyarrow, pyyaml
- Expected runtime: ~25–45 min total on CPU (download+parse ~5 min; model fits ~12 min; SHAP+bootstrap ~8 min; MS permutations ~15 min)
- Hardware requirements: CPU-only, < 4 GB RAM, ~1 GB disk

## Data
- Dataset: Cricsheet T20 ball-by-ball. RECOMMENDED scope = men's IPL + men's T20Is.
- Source:
  - IPL CSV bundle: `https://cricsheet.org/downloads/ipl_male_csv2.zip`
  - T20I CSV bundle: `https://cricsheet.org/downloads/t20s_male_csv2.zip`
  - Each zip = one `<matchid>.csv` per match (per-ball) + `<matchid>_info.csv` (metadata). JSON bundles are a fallback.
- Per-ball CSV columns: `match_id, season, start_date, venue, innings, ball, batting_team, bowling_team, striker, non_striker, bowler, runs_off_bat, extras, wides, noballs, byes, legbyes, penalty, wicket_type, player_dismissed, other_wicket_type, other_player_dismissed`.
- Expected size: ~1.0–1.4M total deliveries → ~120k–200k death-over deliveries (overs 16–20).
- Split: temporal + match-grouped. Train = seasons ≤ T−2, Val = season T−1, Test = season T (latest). GroupKFold(5, group=match_id) on train for HP tuning. No match/identity-encoding leakage across splits.
- Preprocessing (exact):
  1. Concatenate per-match CSVs, tag league.
  2. `over = floor(ball)`, `ball_in_over = round((ball-over)*10)`; filter `over ∈ {15,16,17,18,19}`.
  3. `legal = (wides==0) & (noballs==0)`.
  4. Targets: `runs_off_bat ∈ {0..6}` (extras excluded; pure-extra rows dropped from runs head, kept for wicket head). `wicket=1` iff `player_dismissed` non-null AND `wicket_type ∈ {bowled,caught,lbw,stumped,caught and bowled,hit wicket}`; run-outs/obstructing/retired/timed-out → `wicket=0` (primary). Also build `wicket_any` (incl. run-outs) for ablation.
  5. Flag `dl_affected` matches from `_info.csv`; exclude from RRR features only.
  6. Save `data/processed/deliveries.parquet`.

## Method to Implement
Two separate per-ball heads (NOT one multinomial as primary): wicket = LightGBM binary classifier; runs = LightGBM Tweedie/Poisson regressor. GLM references: L2 logistic (wicket), Poisson GLM (runs). Calibrate wicket posteriors with isotonic on val.

Feature groups (each column maps to exactly one group for SHAP partition):
- **S (state):** balls_remaining_innings, over, ball_in_over, wickets_in_hand, current_score, current_run_rate, is_chase, innings, target, runs_required, balls_remaining, required_run_rate, rrr_minus_crr.
- **B (batter identity, EB target-encoded, historical-only + OOF):** bat_deathSR, bat_boundary_pct, bat_dot_pct, bat_dismissal_rate, bat_n_prior_balls. EB shrink: `(n*rate + alpha*prior)/(n+alpha)`, alpha=50; unseen→global death prior.
- **W (bowler identity, same scheme):** bowl_deathER, bowl_dot_pct, bowl_wicket_rate, bowl_boundary_conceded_pct, bowl_n_prior_balls.
- **P (deterministic pressure index, state-derived):** PI = (rrr/initial_rrr_at_over16) * (1+wickets_lost/10) * balls_used_fraction.
- **H (pressure history, legal striker-faced balls):** dot_run_len (striker + partnership variants), balls_since_wicket, balls_since_boundary, dot_run_len_x_rrr.

Nested ladder (fit each for both heads): M0(base rate), M_S, M_SB, M_SW, M_SBW, M_SBW+P, M_SBW+P+H.

LightGBM HPs (fixed): learning_rate=0.03, n_estimators=600 (early stop on val), num_leaves=31, min_child_samples=200, subsample=0.8, colsample_bytree=0.8; wicket head is_unbalance=True. Tune only num_leaves∈{15,31,63}, min_child_samples∈{100,200,400} via GroupKFold.

### H3 Miller–Sanjurjo procedure (model-free, on same data)
- Sequence unit (primary): batter stay within an innings, death overs, legal striker-faced balls, ordered by ball; wicket ends the sequence. Secondary units: within-over, partnership.
- success (primary) = runs_off_bat≥1 (dot = failure); secondary = boundary (4/6). Also run symmetric dot-streak ("cold/pressure") direction.
- For streak length k∈{1,2,3}:
  - `naive_D(seq,k)` = P(x_t=1 | k preceding 1s) − P(x_t=1 | k preceding 0s).
  - `ms_expected_D(seq,k)` = mean of naive_D over all rearrangements of the sequence's multiset (exact enumerate if C(n,s)≤2000, else MC-sample 2000) = the MS bias E0.
  - per-sequence corrected `D_tilde_i = D_i − E0_i`.
  - aggregate with weights w_i = # valid conditioning instances: D_corrected = Σw_i D_tilde_i / Σw_i; D_naive = Σw_i D_i / Σw_i; report gap = D_corrected − D_naive.
- Permutation nulls (B=5000): (1) within-sequence shuffle (preserve s_i) → p_uncond; (2) state-stratified: bin {over, wickets_in_hand bucket, rrr/score bucket}, permute outcomes only within strata, recompute D_corrected → p_strat (tests momentum BEYOND state, links to H2).
- Multiple testing: BH-FDR 0.05 across {k × success-def × direction × null}. Primary preregistered test: k=1, success=score, state-stratified null.

## Baselines to Implement
1. Trivial: global death-over base rates (M0) for both targets; naive uncorrected D̂ for H3.
2. Standard: state-only GLM (logistic wicket, Poisson runs); deterministic Bhattacharjee–Lemmer-style PI added to state (H2 baseline M_SBW+P).
3. Strong: state-only LightGBM (M_S) — the bar identity (H1) and history (H2) must beat.

## Metrics to Compute
- Primary wicket: log-loss (↓), Brier (↓). Secondary: ECE/reliability (↓), PR-AUC (↑).
- Primary runs: RMSE (↓), MAE (↓). Secondary: CRPS (↓, multinomial head), E[runs] calibration bins.
- H1: grouped-SHAP %mass {S,B,W} per target (TreeSHAP, 20k sampled rows) + incremental Δ-skill table per ladder rung; asymmetry = identity's skill-share for runs vs wicket, paired match-bootstrap CI.
- H2: Δlog-loss, ΔBrier, ΔRMSE, ΔCRPS of (M_SBW+P+H − M_SBW+P) with match-clustered bootstrap 95% CIs; sign of dot_run_len SHAP/coef.
- H3: D_naive, D_corrected, gap, p_uncond, p_strat, BH-adjusted p — per unit × success_def × k.
- Report: mean ± std over 5 runs with seeds 0,1,2,3,4.

## Ablations
1. Identity-encoding: EB vs one-hot-top-N vs random-player placebo (placebo should add ~0 skill).
2. Run-out inclusion: rerun wicket head with `wicket_any`.
3. Sequence-unit (H3): batter-stay vs within-over vs partnership.
4. League scope: IPL-only vs IPL+T20I vs +BBL/PSL/CPL.
5. Learner: LightGBM vs GLM on all proper scores.
6. (Optional, H4 support) Regime: death-trained vs whole-innings-trained, evaluated on death test set.

## Output Files Expected
- results/main_results.csv — cols: model, target, logloss, brier, ece, prauc, rmse, mae, crps, seed
- results/h1_attribution.csv — cols: target, group, shap_pct, incr_skill, ci_lo, ci_hi
- results/h2_incremental.csv — cols: target, metric, delta, ci_lo, ci_hi, dotrun_sign, p
- results/h3_momentum.csv — cols: unit, success_def, k, D_naive, D_corrected, gap, p_uncond, p_strat, p_bh
- results/ablation_{identity,runout,sequnit,league,learner,regime}.csv
- results/leakage_audit.csv — cols: identity_feature, r2_vs_state
- results/figures/ — reliability diagrams (wicket); grouped-SHAP bar (per target); incremental-skill forest plot; D_naive-vs-D_corrected plot; momentum-by-k curve; calibration of E[runs]
- results/summary.md — written interpretation: H1 confirmed/refuted (+asymmetry), H2 confirmed/refuted (+effect size in pp wicket-prob per dot ball), H3 confirmed/refuted (+naive-vs-corrected gap, significance)
</content>
