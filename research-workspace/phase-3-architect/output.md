# Phase 3 — Architect: Experiment Design

One coherent experiment on Cricsheet T20 death-over (overs 16–20) ball-by-ball data that tests the **H1+H2+H3 bundle** as a single paper. All three hypotheses share one parsed dataset, one feature build, and one nested-model family; H3 adds a model-free streak-bias analysis on the same delivery sequences.

The design is **laptop-feasible** (CPU-only, ~100k–300k death-over deliveries, total runtime budget under ~45 min including permutations).

---

## 1. Formalized Hypotheses

**Unit of analysis:** one legal-or-illegal *delivery* in overs 16–20 (0-indexed overs 15–19) of a T20 innings. For sequence/streak analysis the unit is a delivery *within an ordered sequence* (sequence unit defined in §6).

**Two per-ball targets (shared by H1, H2):**
- `runs_off_bat ∈ {0,1,2,3,4,6}` — runs scored off the bat only (extras excluded). Drives **E[runs]** (regression / expected value).
- `wicket ∈ {0,1}` — 1 if a *batter-credited* dismissal occurs on this ball (see §3 for run-out handling). Drives **P(wicket)** (binary classification).

We deliberately model the two targets **separately** (a regressor for runs, a classifier for wickets) rather than a single 8-class multinomial. Reason: the hypotheses make *asymmetric* claims about the two targets (H1) and *opposite-sign* claims (H2), so we need independent, separately-scored heads. A multinomial is reported as a robustness ablation only.

### H1 — State vs identity decomposition (+ asymmetry)
- **Independent variables:** game-state feature group `S`; batter-identity group `B`; bowler-identity group `W`.
- **Dependent variables:** incremental predictive skill (Δlog-loss for wicket; ΔRMSE/ΔMAE for runs) and grouped-SHAP mass between nested models.
- **Claim:** `skill(S) > skill(identity-added)` for *both* targets; AND identity's *share* of total explained skill is strictly larger for E[runs] than for P(wicket).
- **Null H0₁:** identity adds skill ≥ state, or the runs-vs-wicket asymmetry is absent/reversed.
- **Scope:** claims are about *predictive attribution* in T20 death overs only; not causal, not whole-innings, not "skill doesn't matter" (identity may still add real skill — the claim is relative).

### H2 — Residual dot-ball pressure (Markov violation)
- **Independent variable:** pressure-history feature group `H` (length of current consecutive dot-ball run; balls since last wicket; balls since last boundary), added *on top of* the best state(+identity) model.
- **Dependent variables:** incremental skill (Δlog-loss / ΔBrier for wicket; ΔRMSE/CRPS for runs) and the sign of the dot-run coefficient/SHAP.
- **Claim:** conditional on full state, longer preceding dot-ball runs → **P(wicket)↑** and **E[runs]↓**, with bootstrap-significant incremental skill *beyond* both (a) state(+identity) and (b) a deterministic pressure index (Bhattacharjee–Lemmer-style PI built from state).
- **Null H0₂:** history features add no significant skill beyond state, or signs are inconsistent → Markov property holds at the death.
- **Scope:** tests *path-dependence beyond modeled state*. A null here is a positive finding (validates Markov models). Residual confounding with bowler quality is mitigated, not eliminated; H3's stratified permutation is the cleaner causal-ish check.

### H3 — Miller–Sanjurjo-corrected momentum (HEADLINE)
- **Independent variable:** preceding streak indicator (k consecutive "successes" or k consecutive "non-successes"/dots).
- **Dependent variable:** conditional success probability on the *next* ball, and the gap between the **naive** estimator and the **MS-bias-corrected** estimator.
- **Claim:** the naive conditional estimator `D̂ = P(success | k preceding successes) − P(success | k preceding failures)` is biased (per MS, downward) in finite death-over sequences; the corrected estimate differs *materially in sign or magnitude* from the naive one, and its significance is judged against a within-sequence (and a state-stratified) permutation null.
- **Null H0₃:** corrected estimate is statistically indistinguishable from 0 under the permutation null (no momentum beyond chance) — still publishable as the first *correctly estimated* cricket momentum test.
- **Scope:** first import of the MS correction into cricket. Claim is about the *existence and direction of finite-sample bias* and whether momentum survives correction — not a structural/behavioral mechanism.

---

## 2. Data

### Source & scope (RECOMMENDED)
- **Source:** Cricsheet (https://cricsheet.org/downloads/). Open, CC-BY-4.0, no signup.
- **Recommended scope:** **Men's IPL + all men's T20 Internationals (T20Is).** Rationale: (1) IPL has the richest death-over identity signal (deep batting, recurring death specialists) — essential for H1's identity arm; (2) T20Is add volume and generalizability; (3) both are well-curated in Cricsheet with stable player IDs. This yields roughly **1.0–1.4M total deliveries → ~120k–200k death-over deliveries** after filtering, ample for gradient boosting and for pooling MS estimates across players.
- **Optional expansion (ablation only):** add BBL + PSL + CPL ("all major men's franchise T20") to test robustness of H1/H2 across leagues. Keep women's T20 out of the primary run (different scoring distributions would confound a single model) — use as an out-of-distribution generalization ablation if time allows.
- **Use the CSV "ashwin" / per-ball CSV bundles**, not raw JSON, for parsing speed: Cricsheet ships `ipl_csv2.zip` and `t20s_male_csv2.zip` with one row per delivery plus an `all_matches.csv`-style combined file and per-match metadata. (JSON parser provided as fallback in the skeleton.)

### Acquisition (exact)
```
# Cricsheet stable download URLs (CSV bundles):
#   IPL:   https://cricsheet.org/downloads/ipl_male_csv2.zip   (a.k.a. ipl_csv2.zip)
#   T20Is: https://cricsheet.org/downloads/t20s_male_csv2.zip
# Each zip: one <matchid>.csv per match (ball-by-ball) + <matchid>_info.csv (metadata)
# plus, in the "everything" bundle, an all_matches.csv. We parse per-match CSVs.
```
Per-ball CSV columns (Cricsheet standard): `match_id, season, start_date, venue, innings, ball (over.ball as float, e.g. 15.3), batting_team, bowling_team, striker, non_striker, bowler, runs_off_bat, extras, wides, noballs, byes, legbyes, penalty, wicket_type, player_dismissed, other_wicket_type, other_player_dismissed`.

### Parsing & filtering
1. Concatenate all per-match CSVs; attach league tag.
2. Derive `over = floor(ball)`, `ball_in_over = round((ball - over)*10)`.
3. **Death filter:** keep `over ∈ {15,16,17,18,19}` (display overs 16–20).
4. Keep both innings. Drop matches with D/L-revised targets *flagged* in `_info.csv` for the **chase RRR feature only** (still usable for non-RRR features); record a `dl_affected` flag.
5. **Legal-ball flag:** `legal = (wides==0 & noballs==0)`. Wides/no-balls do not consume a ball and are not batter deliveries — for sequence/streak construction (H2/H3) use **legal deliveries faced by the striker** only; for the predictive models (H1/H2) keep all rows but include an `is_extra_ball` feature and exclude pure-extra rows from the runs-target fit (a wide is not a batter outcome). Decision recorded in §3.

### Splits (leakage-safe)
- **Temporal, match-grouped:** train on all seasons up to season *T−2*; validation = season *T−1*; test = most recent season *T*. (Concretely with data through 2024: train ≤2022, val 2023, test 2024.) No match appears in two splits; no delivery from a test match informs training, including identity encodings (§3).
- **Cross-validation for model selection:** `GroupKFold` (5 folds) with **match_id as the group**, on the training portion only. This prevents within-match leakage. Time-respecting order is preserved for the final train/val/test; CV is for hyperparameter choice within train.

---

## 3. Targets — precise treatment

**Runs target (`runs_off_bat`):** integer in {0,1,2,3,4,6} (3 and 5 are rare; keep as-is). **Extras (wides, no-balls, byes, leg-byes, penalties) are excluded from the bat-runs target.** A separate `delivery_total_runs` is retained only as context, never as the runs target. Rows that are pure extras with no legal bat outcome (a wide with no bat run) are **excluded from the runs regressor** but retained for the wicket classifier (a wicket can occur on a no-ball/stumping context — see below).

**Wicket target (`wicket`):**
- `wicket = 1` if `player_dismissed` is non-null AND `wicket_type ∈ {bowled, caught, lbw, stumped, caught and bowled, hit wicket}` → **batter-attributable dismissals**.
- **Run-outs, obstructing the field, retired-out, timed-out → `wicket = 0` for the primary target** (not a function of the batter's shot-risk on that ball; including them would inject base-running noise into the momentum/pressure signal H2/H3 care about). Provide `wicket_any` (includes run-outs) as a **robustness ablation target**.
- A wicket on a no-ball (only run-out/stumping legally possible) follows the same rule.

**Success definition for H3 (must be fixed up front):** primary `success = (runs_off_bat ≥ 1)` (i.e., a scoring shot vs a dot) computed on **legal balls only**. This makes "streak of failures" = "dot-ball run", linking H3 directly to H2. Secondary success definition (reported alongside): `success = boundary = (runs_off_bat ∈ {4,6})`. Wickets terminate a batter's success-sequence (treated as sequence end, not as a success or failure value — documented in §6).

---

## 4. Feature set (per delivery)

Grouped explicitly so SHAP mass can be partitioned (H1).

### Group S — game state (Markov state)
- `balls_remaining_innings` (120 − legal balls bowled), `over` (16–20), `ball_in_over` (1–6).
- `wickets_in_hand` (10 − wickets lost).
- `current_score`, `current_run_rate`.
- **Chase only:** `target`, `runs_required`, `balls_remaining`, `required_run_rate = runs_required / (balls_remaining/6)`, `rrr_minus_crr`. For 1st-innings rows these are NaN → handled by LightGBM native NaN or a `is_chase` flag + median-impute for linear models.
- `is_chase` (innings==2), `innings`.
- `wickets_lost_so_far`.
- (No identity, no history here — this is the pure-state group.)

### Group B — batter identity (leakage-safe encoding)
**Empirical-Bayes / out-of-fold target encoding, historical-only.** For each striker, compute from deliveries *strictly before the current match's start_date* (and, within training CV, out-of-fold):
- `bat_deathSR` = (runs off bat / balls faced) ×100 in death overs, EB-shrunk toward the global death-over mean: `EB = (n·rate + α·prior)/(n+α)`, α≈50 balls.
- `bat_boundary_pct`, `bat_dot_pct`, `bat_dismissal_rate` (death overs).
- `bat_n_prior_balls` (exposure, also used as a confidence feature).
- New/unseen batter → prior (global death mean).

### Group W — bowler identity (same scheme)
- `bowl_deathER` (economy), `bowl_dot_pct`, `bowl_wicket_rate`, `bowl_boundary_conceded_pct`, `bowl_n_prior_balls`.

> **Leakage audit (required, H1):** because `bat_deathSR` partly reflects the *situations* a batter faces, run a diagnostic regressing each identity encoding on group-S features and report R²; flag any encoding with R²>0.5 against state as state-contaminated. Discuss in results.

### Group H — pressure history (H2)
Computed within the **partnership/innings sequence**, over **legal balls**, reset at innings start:
- `dot_run_len` = number of consecutive immediately-preceding dot balls (runs_off_bat==0 & legal), striker-faced variant AND partnership variant.
- `balls_since_wicket` (capped at innings start).
- `balls_since_boundary`.
- `dot_run_len_x_rrr` (interaction, chase only) — lets pressure scale with chase urgency.

### Deterministic pressure index (H2 baseline) — Group P
- `PI` ≈ Bhattacharjee–Lemmer style: a function of (runs_required, balls_remaining, wickets_in_hand) normalized to the death-over mean. Implement as `PI = (rrr/initial_rrr_at_over16)·w_wkts·(balls_used_fraction)` with wicket weight `w_wkts = 1 + (wickets_lost/10)`. This is a *state-derived* scalar; H2's claim is that Group H adds skill **beyond** Group P+S.

---

## 5. Models (nested family)

Two learner classes, same features, same splits:

**Gradient boosting (primary): LightGBM.**
- Wicket head: `LGBMClassifier`, `objective=binary`, `metric=binary_logloss`, with `scale_pos_weight` or `is_unbalance=True` (wickets are ~4–6% of death balls). Calibrate posteriors with isotonic regression on the validation fold before scoring Brier/reliability.
- Runs head: `LGBMRegressor`, `objective=tweedie` or `poisson` (runs are non-negative, over-dispersed, spiky at 0/1/4) — report both, pick by val RMSE. Also a `LGBMClassifier` multinomial over {0,1,2,3,4,6} as robustness, from which E[runs]=Σ r·p(r).
- Hyperparameters (fixed, modest to avoid overfit on ~150k rows): `n_estimators=600 (early-stopping on val), learning_rate=0.03, num_leaves=31, max_depth=-1, min_child_samples=200, subsample=0.8, colsample_bytree=0.8`. Tune only `num_leaves ∈ {15,31,63}` and `min_child_samples ∈ {100,200,400}` via GroupKFold.

**Reference (trivial/standard baseline): regularized GLM.**
- Wicket: L2 logistic regression on standardized features.
- Runs: Poisson GLM (or linear) on standardized features.
- Identity for the GLM = the same EB encodings (numeric), so it is comparable.

### Nested model ladder (the core H1 design)
| Model | Features | Purpose |
|-------|----------|---------|
| M0 | base rate (mean wicket / mean runs) | trivial floor |
| M_S | S only | state-only baseline (the Markov backbone) |
| M_SB | S + B | + batter identity |
| M_SW | S + W | + bowler identity |
| M_SBW | S + B + W | full identity (H1 "best state+identity") |
| M_SBW+P | + deterministic PI | H2 baseline (state-derived pressure) |
| M_SBW+P+H | + pressure history | H2 test model (Markov-violation) |

Incremental skill: `Δ = score(simpler) − score(richer)` (positive = improvement) for log-loss/Brier (wicket) and RMSE/MAE/CRPS (runs), each with **match-clustered bootstrap CIs** (resample whole matches, 1000 reps). H1 asymmetry test = compare `[skill(M_SBW)−skill(M_S)]` normalized share for the runs head vs the wicket head, CI via paired match-bootstrap.

---

## 6. The H3 test — Miller–Sanjurjo correction, made concrete for cricket

### Sequence unit (RECOMMENDATION)
**Primary unit: a single batter's stay within one innings, restricted to death-over legal balls faced** (the "batter death spell"). Rationale: the hot-hand is an *individual* phenomenon (MS, GVT, Huang); pooling within a batter's own consecutive faced balls is the faithful analogue of a player's consecutive shots. A wicket ends the sequence. Because death spells are short (often 4–18 balls), we (a) **do not** restrict streaks to start mid-sequence only, and (b) **pool the MS-corrected per-sequence statistics across all sequences/players** with exposure weighting — exactly the MS aggregation recipe.
- **Secondary units (reported as robustness):** (i) within-over sequences; (ii) within-innings partnership sequences (dot/boundary streaks at the team level for H2 linkage). Document that unit choice changes sequence length and therefore bias magnitude.

### The estimator and the bias
For streak length `k` and a binary success series `x₁…x_n` (one sequence):
- Naive hot-hand statistic: `P̂(success | k preceding successes)` = (# of indices t where x_{t−k..t−1} are all 1 AND x_t=1) / (# of indices t where x_{t−k..t−1} are all 1).
- **MS result:** conditioning on the *realized* number of streaks inside a finite sequence makes `E[P̂(·|streak)] < p` (true success prob) — a **downward selection bias** that grows with k and shrinks with n. For k=1 the bias has closed form; in general MS give the exact expectation by enumerating sequence permutations.

### Bias-corrected estimator (operational recipe — what to implement)
We use the **permutation-expectation correction** (the form MS actually use for aggregation and the one that transfers cleanly to unequal-length cricket sequences):

For each sequence i of length nᵢ with sᵢ successes:
1. Compute the observed difference `Dᵢ = P̂(x_t=1 | k preceding 1's) − P̂(x_t=1 | k preceding 0's)` (NaN if a conditioning set is empty).
2. Compute the **expected difference under the null of exchangeability**: enumerate (or Monte-Carlo sample if nᵢ large) all `C(nᵢ, sᵢ)` rearrangements of the sequence's 1's and 0's, recompute `D` on each, average → `E₀[Dᵢ]`. This `E₀[Dᵢ]` is the **MS bias** for that sequence (it is generally ≠ 0, typically negative for the success-streak statistic).
3. **Bias-corrected per-sequence statistic:** `D̃ᵢ = Dᵢ − E₀[Dᵢ]`.
4. **Aggregate** across sequences with weights `wᵢ` = number of valid conditioning instances in sequence i (so longer/more-informative spells count more): `D̃ = Σ wᵢ D̃ᵢ / Σ wᵢ`. Report alongside the **naive aggregate** `D̂ = Σ wᵢ Dᵢ / Σ wᵢ`. The **headline number is `D̃ − D̂`** (how much the bias correction moves the answer).

Repeat for the two success definitions (scoring-shot, boundary) and for the symmetric **cold-hand / dot-streak** statistic (P(success | k preceding dots)) which is the H2-linked momentum-after-pressure quantity.

### Permutation null (significance, BEYOND state)
1. **Within-sequence permutation (unconditional null):** for each sequence, shuffle its outcomes (preserving sᵢ) B=5000 times; recompute the aggregate `D̃` each time → null distribution; two-sided p-value. (Note: because the MS correction already centers each sequence at its own permutation mean, this primarily tests dispersion — equivalently we permute and recompute the *naive* aggregate to get the null for `D̂`, the standard MS/GVT permutation test.)
2. **State-stratified permutation (momentum BEYOND state — the key test linking to H2):** bin deliveries into game-state strata (cells of {over, wickets_in_hand bucket, rrr bucket(chase)/score bucket(set)}). Permute outcomes **only within a stratum** (so the permuted series preserves the state-conditional base rate), recompute `D̃`, B=5000. A significant `D̃` under *this* null means the streak effect is not explained by state composition → genuine path-dependence. This is the rigorous version of H2's residual claim.

### Multiple testing
We test k ∈ {1,2,3} × {2 success defs} × {2 momentum directions} × {2 nulls}. Control with **Benjamini–Hochberg FDR at 0.05** across the family; pre-register k=1 scoring-shot, state-stratified null as the *primary* H3 test, the rest as secondary/robustness.

---

## 7. Baselines (≥3, per agent spec)

1. **Trivial:** global death-over base rate for each target (M0) + naive uncorrected `D̂` (the explicit H3 comparator).
2. **Standard:** state-only GLM (logistic / Poisson) — the field's identity-agnostic WASP/Asif–McHale analogue, plus the deterministic Bhattacharjee–Lemmer-style PI baseline (H2).
3. **Strong:** state-only LightGBM (M_S) — the best calibrated *state-only* model; the bar identity (H1) and history (H2) must beat.

---

## 8. Metrics

**Wicket (P(wicket)):**
- **Log-loss** `−1/N Σ [y log p + (1−y) log(1−p)]` (↓) — primary, proper.
- **Brier** `1/N Σ (p−y)²` (↓) — proper, robust to imbalance reporting.
- **Reliability diagram + ECE** (calibration) (↓).
- **PR-AUC** (↑) reported because wickets are rare (~4–6%); ROC-AUC secondary.

**Runs (E[runs]):**
- **RMSE**, **MAE** (↓) on runs_off_bat.
- **CRPS** of the predictive run distribution (multinomial head) (↓) — proper.
- **Calibration of E[runs]:** binned predicted-vs-actual mean runs.

**Attribution (H1):** grouped-SHAP mass `Σ|SHAP|` partitioned into S / B / W (% of total), per target; plus incremental Δ-skill table.

**H2:** Δlog-loss, ΔBrier, ΔRMSE, ΔCRPS of (M_SBW+P+H − M_SBW+P), with match-clustered bootstrap 95% CIs; sign of `dot_run_len` SHAP/coef.

**H3:** naive `D̂`, corrected `D̃`, `D̃−D̂`, permutation p-values (both nulls), per k and per success def; BH-FDR adjusted.

**Reproducibility:** all model metrics reported as **mean ± std over 5 seeds** {0,1,2,3,4} (seed governs LightGBM bagging + bootstrap + permutation RNG).

---

## 9. Ablations

1. **Identity-encoding leakage ablation (H1):** swap EB target-encoding for (a) frequency/one-hot of top-N players + "other", (b) random-player-id shuffle (placebo — should add ~0 skill). Confirms H1's identity skill isn't a leakage artifact.
2. **Run-out inclusion ablation:** rerun wicket head with `wicket_any` (incl. run-outs); check H1/H2 conclusions are stable.
3. **Sequence-unit ablation (H3):** rerun MS test for batter-stay vs within-over vs partnership; report how bias and significance change with sequence length.
4. **League-scope ablation:** IPL-only vs IPL+T20I vs +BBL/PSL/CPL; tests H1/H2 robustness across competitions.
5. **Learner ablation:** LightGBM vs GLM head-to-head on all proper scores (shows results aren't learner-specific).
6. **Regime ablation (optional, the H4 supporting study):** death-trained vs whole-innings-trained model evaluated on the death test set.

---

## 10. Runtime & feasibility (laptop, CPU)

| Step | Est. time |
|------|-----------|
| Download + unzip Cricsheet CSV bundles | 1–3 min |
| Parse + filter + feature build (~150k death rows) | 2–5 min |
| Fit nested ladder × 2 heads × 5 seeds (LightGBM) | 5–12 min |
| SHAP (TreeSHAP, sampled 20k rows) | 2–4 min |
| Bootstrap CIs (1000 match-resamples) | 2–4 min |
| MS correction + permutations (B=5000, vectorized; MC-sample enumeration for long seqs) | 5–15 min |
| **Total** | **~25–45 min** |

All fits CPU-only, peak RAM < 4 GB. The permutation engine is the runtime risk — mitigate by Monte-Carlo sampling rearrangements when `C(nᵢ,sᵢ)` is large (cap at 2000 samples/sequence) and vectorizing with NumPy.

---

## 11. Honest risks & mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| **Short per-player death sequences** (H3) | noisy per-batter MS estimates | pool across players with exposure weights; report permutation CIs not per-player point estimates; sequence-unit ablation |
| **Wicket class imbalance** (~4–6%) | unstable P(wicket), inflated AUC | proper scoring (log-loss/Brier) not accuracy; PR-AUC; isotonic calibration; `is_unbalance` |
| **Identity/state leakage** (H1) | inflated identity skill, muddied decomposition | historical-only + out-of-fold EB encodings; explicit leakage-audit regression; placebo-shuffle ablation |
| **Extras / wides in sequences** | corrupt dot-run counts | sequence features on legal striker-faced balls only; `is_extra_ball` feature in models |
| **Run-outs** | inject base-running noise into momentum signal | primary target excludes run-outs; `wicket_any` ablation |
| **Dot-streak ↔ bowler-quality confound** (H2) | spurious "pressure" effect | condition on bowler identity (W) + deterministic PI as baselines; H3 state-stratified permutation isolates beyond-state effect |
| **Multiple testing across k & defs** (H3) | false positives | pre-registered primary test; BH-FDR across the family |
| **D/L-affected chases** | wrong RRR | flag and exclude `dl_affected` rows from RRR-dependent features only |
| **Cricsheet schema drift / URL change** | parse breaks | pin to CSV "csv2" bundles; JSON fallback parser in skeleton; assert column presence |

---

## 12. Code skeleton (file layout + key functions)

```
project/
├── config.yaml                 # leagues, overs={15..19}, seeds, paths, k_values, B_perm
├── data/
│   ├── raw/                     # downloaded zips
│   └── processed/deliveries.parquet
├── src/
│   ├── download.py
│   │   └── download_cricsheet(leagues) -> raw zips        # urllib/requests to cricsheet csv2 urls
│   ├── parse.py
│   │   ├── load_match_csv(path) -> DataFrame
│   │   ├── derive_over_ball(df), flag_legal(df)
│   │   └── build_delivery_table(leagues) -> deliveries.parquet
│   ├── features.py
│   │   ├── add_state_features(df)            # Group S (+ chase RRR)
│   │   ├── add_pressure_index(df)            # Group P (B–L style)
│   │   ├── add_history_features(df)          # Group H (dot_run_len, balls_since_*) legal-only
│   │   ├── fit_eb_identity_encoders(train_df, alpha) -> encoders   # historical-only, OOF
│   │   ├── apply_identity_encoders(df, encoders)                   # Groups B, W
│   │   └── make_targets(df)                  # runs_off_bat, wicket (batter-credited), wicket_any
│   ├── splits.py
│   │   ├── temporal_split(df) -> (train,val,test)         # by season
│   │   └── group_kfold(train, n=5)                        # group=match_id
│   ├── models.py
│   │   ├── fit_wicket_lgbm(X,y,...), fit_runs_lgbm(X,y,...)
│   │   ├── fit_glm_baselines(...)
│   │   ├── calibrate_isotonic(p_val, y_val)
│   │   └── nested_ladder(train,val) -> {M_S,M_SB,...,M_SBW+P+H}   # dict of fitted heads
│   ├── metrics.py
│   │   ├── log_loss, brier, ece, pr_auc, reliability(df)
│   │   ├── rmse, mae, crps_multinomial
│   │   └── match_clustered_bootstrap(metric_fn, df, B=1000)
│   ├── attribution.py
│   │   ├── grouped_shap(model, X, feature_groups) -> %mass per group   # TreeSHAP, sampled
│   │   └── incremental_skill_table(ladder, test) -> DataFrame
│   ├── momentum_ms.py            # H3 core (model-free)
│   │   ├── build_sequences(df, unit='batter_stay', success='score') -> list[np.array]
│   │   ├── naive_D(seq, k) -> (D, n_valid)
│   │   ├── ms_expected_D(seq, k, max_perm=2000) -> E0   # enumerate or MC-sample rearrangements
│   │   ├── corrected_aggregate(seqs, k) -> {D_naive, D_corrected, gap, weights}
│   │   ├── perm_null_unconditional(seqs, k, B=5000) -> p
│   │   └── perm_null_state_stratified(df, k, strata_cols, B=5000) -> p   # permute within state cells
│   ├── leakage_audit.py
│   │   └── audit_identity_vs_state(encoders, X_state) -> R2 table
│   └── run_all.py                # orchestrates: H1 ladder+SHAP, H2 incremental, H3 MS+perm, ablations
└── results/
    ├── main_results.csv          # cols: model, target, logloss, brier, ece, prauc, rmse, mae, crps, seed
    ├── h1_attribution.csv        # cols: target, group(S/B/W), shap_pct, incr_skill, ci_lo, ci_hi
    ├── h2_incremental.csv        # cols: target, metric, delta, ci_lo, ci_hi, dotrun_sign, p
    ├── h3_momentum.csv           # cols: unit, success_def, k, D_naive, D_corrected, gap, p_uncond, p_strat, p_bh
    ├── ablation_*.csv
    ├── figures/                  # reliability diagrams, grouped-SHAP bars, incr-skill forest,
    │                             #   D_naive-vs-D_corrected plot, momentum-by-k curve
    └── summary.md
```

**Key function contracts (most error-prone):**
- `ms_expected_D(seq,k,max_perm)`: if `C(n,s) ≤ max_perm` enumerate exactly via `itertools` over positions of the `s` ones; else draw `max_perm` random permutations of the multiset; return mean of `naive_D` over rearrangements. Returns `np.nan` if no valid conditioning instance exists in *any* rearrangement.
- `build_sequences(unit='batter_stay')`: group by (match_id, innings, striker), order by ball, **legal balls only**, cut a new sequence when a wicket to that striker ends the stay; success per §3.
- `match_clustered_bootstrap`: resample **match_ids** with replacement (not rows) to respect within-match correlation.
- `grouped_shap`: assign every feature column to exactly one of {S,B,W,P,H}; report each group's share of total mean(|SHAP|).

---

## 13. Quality check (against agent rubric)
- **Laptop < 1h:** yes (~25–45 min). ✔
- **Tests the hypotheses, not adjacents:** H1 = nested Δ-skill + grouped SHAP on both targets with asymmetry contrast; H2 = incremental skill of history beyond state+PI with sign check; H3 = the actual MS correction + state-stratified permutation. ✔
- **Fair baselines:** same data/splits/features/compute across the ladder; placebo-shuffle guards leakage. ✔
- **Interpretable outputs:** Δ-skill in proper-score units, SHAP %mass, wicket-prob percentage-points per dot ball, naive-vs-corrected gap in pp. ✔

See `experiment-spec.md` for the machine-readable version the experimenter implements directly.
</content>
</invoke>
