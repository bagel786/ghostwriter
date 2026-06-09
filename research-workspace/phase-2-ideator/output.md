# Phase 2 — Ideator: Testable Hypotheses

**Source gaps:** Phase-1 scout Gaps 1–5. **User steer:** make BOTH the predictive-modeling question (per-ball E[runs] + P(wicket) from state + identity, with factor weighting) and the momentum/"pressure-sequence" question answerable, with the Markov-violation test using the Miller–Sanjurjo correction as the novel headline.

**Data substrate for all hypotheses:** Cricsheet open ball-by-ball T20 data (men's + women's; international + major franchise leagues — IPL, BBL, PSL, CPL, etc.). Each delivery row carries: match/innings/over/ball, striker, non-striker, bowler, runs (off bat + extras), wicket flag + dismissal type, and derivable state (balls remaining, wickets in hand, score, target, required run rate). Filter to overs 16–20 for the death-over regime. Per-ball outcome target is the standard 8-class multinomial {0,1,2,3,4,6,wicket, (extras bucket)} from which E[runs] and P(wicket) are read off. All hypotheses are testable with gradient boosting (XGBoost/LightGBM/CatBoost) + SHAP, logistic/multinomial regression, and permutation/resampling — no GPU or proprietary data required.

---

### Hypothesis 1: Identity adds less than state in T20 death overs, and adds it asymmetrically (more to E[runs] than to P[wicket])

**Statement:** In overs 16–20, batter–bowler identity contributes a smaller share of explained variation in per-ball outcomes than game state does, and its marginal contribution is larger for expected runs than for wicket probability.

**Grounded in gap:** Gap 1 — "No clean variance-decomposition of state vs. batter–bowler identity for per-ball expected runs *and* wicket probability, isolated to T20 death overs."

**Rationale:**
The death-over regime compresses the decision space: with few balls and wickets left, the situation (required run rate, wickets in hand, balls remaining) dictates intent so strongly that most batters attack and most bowlers defend regardless of who they are. State should therefore dominate. But the *scoring* channel (boundaries vs singles) is where elite finishers and death specialists actually separate from the field — a top finisher converts the same state into more runs — so identity should carry more weight on E[runs]. Wickets at the death are dominated by high-variance events (mis-hits on yorkers/slower balls under maximum-aggression intent), which are noisier and less skill-separable per ball, so identity should add less to P(wicket).

Prior work supports the setup but never does the decomposition: WASP and Asif–McHale (2016) deliberately exclude identity ("average team vs average team"); Swartz's simulator/xER include identity but for simulation/evaluation, not a state-vs-identity attribution; Sahoo et al. (2024) use SHAP for death-over shot selection but not for an E[runs]/P(wicket) variance split. Raju et al. (2024) prove identity-level matchup features are extractable from Cricsheet.

**Experiment sketch:**
- Setup: Death-over deliveries (overs 16–20), temporal train/test split (train on earlier seasons, test on the most recent ~2 seasons). Two targets per ball: runs off bat (for E[runs]) and wicket indicator (for P[wicket]); fit a multinomial outcome model that yields both.
- Method: Fit nested gradient-boosting models — (a) state-only, (b) state + batter identity features, (c) state + bowler identity, (d) state + both. Identity encoded as shrinkage/empirical-Bayes target encodings (career + recent death-over strike rate, boundary %, dismissal rate) to avoid leakage and handle rare players. Attribute contributions with (i) incremental skill (Δ log-loss / ΔRMSE / ΔCRPS between nested models) and (ii) global SHAP value mass partitioned into state vs identity feature groups.
- Baselines: Bookmaker-free baselines — global death-over base rates, and a state-only model — are the references identity must beat.
- Success metric: Hypothesis confirmed if state's grouped SHAP mass and incremental skill exceed identity's for both targets, AND identity's share of incremental skill is strictly larger for E[runs] than for P(wicket). Refuted if identity dominates state, or if the E[runs]>P(wicket) asymmetry reverses.
- Estimated complexity: ~400–600 LOC (Cricsheet parsing + feature build + nested fits + SHAP). Runs in minutes–low tens of minutes on a laptop; data is ~100k–300k death-over balls.

**Novelty assessment:**
- Different from existing work because it is the first state-vs-identity variance decomposition for *both* per-ball E[runs] and P(wicket) isolated to the T20 death regime, with the directional (asymmetry) prediction.
- A reviewer could argue "feature importance for cricket ML is common." Address by (a) restricting to the death regime, (b) reporting proper-scored *incremental* skill (not just SHAP rank), and (c) making a falsifiable directional claim rather than just listing top features.

**Risk assessment:**
- Risk: identity target-encodings leak game-state information (e.g., a batter's career SR partly reflects the situations they bat in), muddying the "state vs identity" boundary. Mitigate with strictly out-of-fold/historical-only encodings and an explicit leakage audit.
- A null/partial result (identity ≈ state, or no asymmetry) is still informative: it would justify identity-agnostic WASP-style models for death overs and is publishable as a calibrated benchmark finding.

---

### Hypothesis 2: A residual "dot-ball pressure" effect violates the Markov assumption — recent dot balls raise next-ball wicket probability beyond what state predicts

**Statement:** Conditional on full game state, the count of consecutive immediately-preceding dot balls (faced by the current batter/partnership) has a positive, statistically significant association with next-ball wicket probability and a negative association with next-ball expected runs — i.e., the per-ball process is non-Markovian at the death.

**Grounded in gap:** Gap 2 — "The Markov assumption underlying in-play cricket models is untested at the delivery level against 'pressure sequences.'"

**Rationale:**
The field's backbone models (WASP, the MDP/value-function family) assume outcomes depend only on current state, not on the path taken to reach it. But there is a plausible behavioral mechanism for path-dependence at the death: a run of dot balls inflates the *required* rate and the psychological cost of not scoring, pushing the batter to force a higher-risk shot on the next ball than the same state reached without a dot-ball streak would warrant. That predicts both a P(wicket) increase and (because forcing also produces boundaries) a more dispersed but possibly lower-mean run outcome. If true, every Markovian in-play model is mis-specified precisely where matches are decided.

The pressure-index literature (Bhattacharjee–Lemmer 2016; Mallawa Arachchi 2024) *defines* pressure from current state and validates by predicting outcomes — it never isolates a history-beyond-state residual. No cricket in-play paper found tests the Markov violation at the delivery level. This is a clean, falsifiable test of an assumption everyone makes and no one has checked for T20 death overs.

**Experiment sketch:**
- Setup: Death-over deliveries. Build a state-only model M0 (best-calibrated baseline, possibly with identity from H1). Define sequence features: length of current consecutive dot-ball run, balls since last boundary, balls since last wicket (partnership-level and batter-level variants).
- Method: (a) Add sequence features to M0 → M1; test incremental skill (Δlog-loss for wicket, ΔCRPS/RMSE for runs) on held-out data, with significance via match-clustered bootstrap. (b) Complementary residual test: regress M0's per-ball residuals on dot-ball-run length to detect any systematic sign. (c) Report effect size in interpretable units (Δ percentage points of wicket prob per additional preceding dot ball).
- Baselines: State-only M0; and M0 with the deterministic Bhattacharjee–Lemmer/Shah–Shah pressure index added (to show the *sequence* features add beyond an existing state-derived pressure construct).
- Success metric: Confirmed if sequence features yield positive, bootstrap-significant incremental skill AND the dot-ball coefficient sign matches the prediction (P[wicket]↑, E[runs]↓), beyond both M0 and the deterministic-PI baseline. Refuted if incremental skill is null or signs are inconsistent.
- Estimated complexity: ~250–400 LOC on top of H1's pipeline. Minutes to run. The Miller–Sanjurjo correction (H3) is what makes the *raw conditional-probability* version of this test unbiased; here the regression/incremental-skill framing is naturally less bias-prone but should be cross-checked against H3.

**Novelty assessment:**
- First delivery-level test of the Markov assumption against pressure sequences in T20 cricket, distinguishing path-dependence from state.
- Reviewer pushback: "pressure indices already capture this." Address by including the deterministic PI as a baseline and showing sequence features add *incremental* skill beyond it — the PI is a function of state, the sequence feature is a function of history.

**Risk assessment:**
- Risk: dot-ball streaks are correlated with state (good bowling spell, low wickets in hand), so the effect could be confounded; mitigate by conditioning richly on state and by H3's within-stratum permutation test.
- Risk: streak-selection bias can mask a real effect in the naive conditional estimator — this is exactly why H3 is paired with it. A null result here, if robust to H3, is itself a strong finding: it would *validate* the Markov assumption for death overs and reassure users of WASP-style models.

---

### Hypothesis 3 (HEADLINE): With the Miller–Sanjurjo streak-selection-bias correction, a genuine "hot-hand"/momentum effect appears in death-over deliveries that naive (uncorrected) estimation hides

**Statement:** Applying the Miller–Sanjurjo (2018) bias correction (and matched within-state permutation tests) to per-ball death-over sequences reveals a momentum effect — a batter scoring a boundary raises the probability of a positive outcome on the next ball, and/or a dot/wicket streak shifts subsequent outcomes — whose sign and/or magnitude differs materially from the biased naive conditional-probability estimate.

**Grounded in gap:** Gap 3 — "The cricket 'pressure'/momentum literature has not adopted the hot-hand methodological correction (streak-selection bias / permutation tests)" (and directly informs Gap 2).

**Rationale:**
Miller–Sanjurjo (2018) proved that the intuitive estimator "P(success | preceding streak of successes)" is *downward biased* in finite sequences because of how streaks are selected — the very error that made basketball's hot hand look nonexistent for 31 years, and whose correction *reversed* the canonical GVT result (~+13pp). Every cricket pressure/momentum paper found by the scout uses naive conditional comparisons or deterministic indices; none applies this correction. So the cricket literature is currently making, untested, exactly the inferential mistake the basketball literature spent three decades unwinding. Importing the correction is both a methodological contribution and a substantive test: it can change the *answer* about whether cricket momentum is real.

Death overs are the ideal proving ground: outcomes per ball are short binary/ordinal sequences (exactly the regime where the finite-sample streak bias bites hardest), the stakes are highest, and arXiv 2505.01849 confirms pressure variance peaks here. Huang et al. (2025, tennis) provide a permutation-test template for "momentum beyond chance" that transfers directly.

**Experiment sketch:**
- Setup: Within each batter's death-over delivery sequence (and separately for partnership-level dot/wicket streaks), define "success" (e.g., boundary, or any score ≥1) and compute the conditional-probability difference D = P(success | k preceding successes) − P(success | k preceding non-successes).
- Method: (a) Compute the naive D̂. (b) Apply the Miller–Sanjurjo finite-sample bias correction to obtain the expected-bias-adjusted estimate. (c) Run a within-batter permutation test (shuffle each batter's outcome sequence many times, recompute D, build the null) — and a *state-stratified* permutation (permute only within matched game-state cells) to separate momentum from state, linking back to H2. Aggregate across players with appropriate weighting.
- Baselines: The naive uncorrected D̂ is the explicit comparison — the contribution is the *difference* between corrected and naive estimates plus the permutation-null significance.
- Success metric: Confirmed if the corrected estimate is significant under permutation AND differs materially (sign or magnitude) from the naive estimate, demonstrating the bias matters in cricket. The result is publishable whether the corrected effect is positive (momentum exists) or null (momentum absent even after correction) — both overturn or confirm current naive practice.
- Estimated complexity: ~300–500 LOC (sequence extraction + MS correction + permutation engine; permutations are the runtime cost — seconds to a few minutes with vectorization). No model training required for the core test, though it dovetails with H2's modeling.

**Novelty assessment:**
- First import of the Miller–Sanjurjo streak-selection-bias correction into cricket; first rigorous, bias-corrected per-delivery momentum test in T20. This is the headline novelty the scout flagged.
- Reviewer pushback: "hot-hand methods are known." Yes — in basketball/tennis; the novelty is the cricket application *and* showing the bias changes the substantive answer for an assumption (Markov) baked into the field's standard models. Quantifying the naive-vs-corrected gap is the defensible core.

**Risk assessment:**
- Risk: per-player death-over sequences are short, so per-batter estimates are noisy; mitigate by pooling across players (the MS correction is defined per-sequence then aggregated) and reporting confidence via the permutation null.
- Risk: effect could genuinely be null after correction. That is still a strong, publishable result — it would be the first *correctly estimated* cricket momentum test and would validate Markovian models. The methodological contribution (correction + cross-checked permutation design) stands either way.

---

### Hypothesis 4: A death-over-specific per-ball model is better calibrated than a whole-innings model evaluated on death overs

**Statement:** A model trained only on overs 16–20 produces better-calibrated per-ball E[runs] and P(wicket) (lower log-loss/Brier for wicket, lower CRPS/RMSE for runs, better reliability) on a held-out death-over test set than an otherwise-identical model trained on all overs, because death-over outcome dynamics are a distinct regime.

**Grounded in gap:** Gap 4 — "Death overs (16–20) are rarely modeled as a distinct per-ball regime" (and Gap 5 on joint proper-scored calibration).

**Rationale:**
Scoring intent, boundary rates, wicket rates, and required-run-rate pressure differ sharply at the death from the powerplay/middle; arXiv 2505.01849 confirms pressure-index variance is *largest* in overs 16–20. A whole-innings model averages over heterogeneous regimes and will systematically mis-calibrate at the tails that matter most at the death (very high required rates, last-over boundaries). A regime-specific model trades some sample size for reduced regime bias and should win on proper scoring in the death-over test cells. This also delivers the calibrated joint benchmark (Gap 5) on open data that future work can build on.

**Experiment sketch:**
- Setup: Same feature set and learner for both arms; temporal train/test split. Arm A trains on overs 16–20 only; Arm B trains on all overs. Both evaluated only on the held-out death-over test set.
- Method: Fit both; evaluate with proper scoring (log-loss + Brier + reliability diagrams for P[wicket]; RMSE + CRPS for E[runs]). Slice results by over (16,17,18,19,20) and by required-run-rate bands to locate where the regime model helps most.
- Baselines: Whole-innings model (Arm B) is the baseline; also report vs death-over base rates.
- Success metric: Confirmed if Arm A beats Arm B on the death-over test set across the majority of proper-scoring metrics, especially in high-RRR/last-over cells. Refuted if Arm B (more data) wins everywhere.
- Estimated complexity: ~150–250 LOC reusing H1's pipeline (just swap the training filter). Minutes to run.

**Novelty assessment:**
- Establishes the calibrated, joint (runs + wickets) death-over benchmark that the scout found missing (Gaps 4+5). Novelty is moderate (phases are recognized) but execution as a calibrated per-ball T20 death model is absent.
- Reviewer pushback: "obvious that regime-specific helps." Address by the possibility it does *not* (more data can win) and by quantifying *where* in state-space the regime model matters — a practically useful map, not just a yes/no.

**Risk assessment:**
- Risk: death-over subsample may be large enough that the whole-innings model gains nothing or the regime model loses on sparse cells (over 20 with rare states). Mitigate by reporting per-cell results.
- Null result (no calibration gain) is informative: it tells practitioners a single whole-innings model suffices, simplifying deployment. Either way the benchmark artifact is the contribution.

---

## Ranking

| Rank | Hypothesis | Novelty (1-5) | Feasibility (1-5) | Impact (1-5) | Recommended? |
|------|-----------|---------------|-------------------|--------------|--------------|
| 1 | H3 — Miller–Sanjurjo-corrected death-over momentum (headline) | 5 | 4 | 5 | ✓ (headline) |
| 2 | H2 — Residual dot-ball pressure / Markov-violation test | 4 | 5 | 5 | ✓ (core) |
| 3 | H1 — State-vs-identity variance decomposition + asymmetry | 4 | 5 | 4 | ✓ (primary-question backbone) |
| 4 | H4 — Death-regime-specific vs whole-innings calibration | 3 | 5 | 3 | ✓ (benchmark / supporting) |

**Recommended package.** H1 + H2 + H3 form a coherent paper that answers both user questions: H1 delivers the primary predictive-modeling result (per-ball E[runs] + P(wicket) from state + identity, with factor weighting) and supplies the calibrated state-only baseline that H2 and H3 build on; H2 tests the Markov assumption via incremental model skill; H3 is the methodological headline that imports the Miller–Sanjurjo correction and is the most novel contribution. H4 is a low-cost supporting study that produces the open calibrated benchmark and strengthens the modeling claims — include it if time allows. All four run on Cricsheet on a laptop in minutes to tens of minutes; the only real risk to manage is identity/state leakage in feature encoding (H1) and short per-player sequences (H3), both with stated mitigations.
