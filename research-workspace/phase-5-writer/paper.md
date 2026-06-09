# The Death-Over Momentum Illusion: A Miller–Sanjurjo Correction for T20 Cricket

**Safiullah Baig** · Preprint

**Keywords:** T20 cricket, expected runs, wicket probability, calibration, SHAP, Markov property, hot hand, Miller–Sanjurjo correction.

---

## Abstract

Two beliefs dominate how the death overs (16–20) of Twenty20 (T20) cricket are modelled: that the historical record of the batter and bowler on strike drives the next ball, and that "momentum" or pressure sequences shift outcomes beyond the game state. We test both at the level of an individual delivery and find little support for either. On 223,678 death-over deliveries from 4,402 men's IPL and T20I matches (Cricsheet, 2005–2026), we build calibrated per-ball models of expected runs and wicket probability and decompose their skill into game state versus a historical-rate encoding of identity, using a nested model ladder, grouped SHAP, and match-clustered bootstrap intervals.

Our headline result concerns momentum. Applying the Miller–Sanjurjo streak-selection correction to cricket — to our knowledge for the first time — we show the apparent death-over "cold hand" (naive *D* = −0.114) is almost entirely a finite-sequence artifact (bias −0.121): the corrected estimate is +0.007 and not significant against a state-stratified null (*p* = 0.40). The +0.121 gap between the naive and corrected estimators quantifies the size of the apparent-momentum illusion. On the identity question, we find no evidence that our historical-rate encoding of identity improves out-of-sample skill: a game-state-only model is the best-calibrated wicket model (log-loss 0.2738 vs. 0.2748 base rate), and adding identity worsens held-out log-loss and significantly raises expected-runs RMSE in every one of six rolling held-out seasons — even though SHAP attributes 51–64% of explanatory mass to batter identity. A random-player placebo collapses that mass to 7–8% while skill is unchanged, showing the attribution is faithful but the signal does not generalise: a cautionary dissociation between in-sample attribution and out-of-sample skill. Residual dot-ball pressure adds significant skill to expected runs (RMSE +0.0065, 95% CI [0.0048, 0.0083]; longer dot runs lower expected runs) but nothing to wicket probability, so the Markov property is violated for scoring intensity but not for dismissal risk. The absolute skill differences are small in proper-score terms — these are per-ball outcomes close to the base rate — so our claims rest on the *qualitative* dissociation and the bias correction, not on the magnitude of any single model improvement.

---

## 1. Introduction

In Twenty20 (T20) cricket, the death overs — the final five overs (16–20) of an innings — carry a disproportionate share of the outcome. Scoring rates peak, wickets are spent in pursuit of boundaries, and the required run rate in a chase swings sharply on a single delivery. Two intuitions dominate how commentators, coaches, and models reason about this phase. The first is that *who* is on strike or bowling — a death-overs finisher against a yorker specialist — largely determines the next ball. The second is that *momentum* matters: that a run of dot balls builds pressure that spills into the next delivery, or that a batter who has just found the boundary is "hot." Both intuitions are widely held; neither has been tested cleanly at the level of an individual death-over delivery.

The quantitative cricket literature provides the machinery to test them but has not done so for this regime. Per-ball win-probability and expected-runs models — WASP's dynamic-programming value function (Brooker & Hogan, 2012), the dynamic logistic regression of Asif & McHale (2016), and the hierarchical empirical-Bayes simulators of Swartz (2016, 2020) — either deliberately exclude player identity ("average team vs. average team") or include it for simulation rather than for a clean state-versus-identity attribution. The pressure-index family (Shah & Shah, 2014; Bhattacharjee & Lemmer, 2016; Mallawa Arachchi et al., 2024) *defines* pressure as a deterministic function of game state and then validates it by predicting outcomes; it never isolates a residual, history-beyond-state component. And the near-universal Markov assumption of these models — that the next ball depends only on the current state, not on the path that produced it — has not been tested against pressure sequences at the delivery level. Meanwhile, the general-sports "hot hand" literature has been transformed by the discovery of a streak-selection bias in the naive conditional-probability estimator (Miller & Sanjurjo, 2018, 2024), a correction that overturned the canonical basketball null (Gilovich et al., 1985). No cricket study has imported it.

We address all three gaps in a single experiment on real Cricsheet data. We build calibrated per-ball models of expected runs E[runs] and wicket probability P(wicket) for the T20 death overs, decompose their predictive skill into game state and batter/bowler identity, test whether pressure history adds skill beyond a Markov state model, and apply the Miller–Sanjurjo correction to the question of per-ball momentum.

We find, first, that the apparent death-over "cold hand" is largely a finite-sequence statistical artifact: once the Miller–Sanjurjo bias is removed and the test is run against a state-stratified null, we find no statistically significant per-ball momentum beyond what game state already implies. This correction — new to cricket — is our central, most defensible result. Second, we have no evidence that a *historical-rate encoding* of batter/bowler identity improves held-out per-ball skill over a game-state model on either target — and, more pointedly, that adding this identity encoding *hurts* out-of-sample expected-runs accuracy in every one of six rolling held-out seasons, even as SHAP attributes the majority of explanatory mass to batter identity. A random-player placebo confirms this is a genuine dissociation between faithful in-sample attribution and generalizable skill, not a leakage or feature-encoding artifact. Third, residual dot-ball pressure adds significant skill to expected runs (with the expected negative sign) but nothing to wicket risk, so the Markov property is violated only for scoring intensity, not for dismissal risk. The absolute proper-score differences here are small — per-ball death-over outcomes sit close to the base rate, so even the best models improve on it only modestly — and we therefore lean on the qualitative dissociation and the bias correction rather than the size of any one model gain. All conclusions are specific to per-ball outcomes in the death overs, under our feature set and our historical-rate identity encoding, after state control and bias correction; we distinguish throughout "this encoding of identity does not help" from "identity does not matter," and "no significant momentum" from "momentum proven absent."

**Contributions.**

- We release a calibrated per-ball benchmark for T20 death overs on 223,678 deliveries from 4,402 men's IPL and T20I matches (2005–2026, held-out 2026 test season), reporting proper scores for both E[runs] (RMSE 1.728 → 1.686 over the base rate) and P(wicket) (log-loss 0.2748 → 0.2738) — and show that a state-only model is the best-calibrated wicket model, with identity *worsening* held-out log-loss.
- We document a SHAP-versus-skill dissociation and stress-test it: TreeSHAP credits batter identity with 51–64% of explanatory mass, yet our historical-rate encoding of that identity adds zero or negative held-out incremental skill (runs RMSE −0.0053, 95% CI [−0.0089, −0.0019]). A random-player placebo collapses batter SHAP mass to 7–8% while leaving skill unchanged, and a six-season rolling-window evaluation finds identity significantly hurts expected-runs RMSE in *every* season — showing the gap is genuine overfitting of non-stationary player form, not contamination or a single-season fluke.
- We test the Markov assumption directly and find it violated for E[runs] only: pressure history adds significant skill (RMSE +0.0065, 95% CI [0.0048, 0.0083], dot-run sign negative) but nothing to P(wicket).
- To our knowledge, we provide the first application of the Miller–Sanjurjo streak-selection correction to cricket. The naive death-over momentum estimate is a strong negative (*D* = −0.114), but the finite-sequence bias is nearly equal and opposite (−0.121); the corrected estimate (+0.007) is not significant against a state-stratified null (*p* = 0.40). We quantify the apparent-momentum illusion as the +0.121 gap between the naive and corrected estimators.

---

## 2. Related Work

**Per-ball win-probability and expected-runs models.** The methodological backbone of in-play cricket modeling is a dynamic-programming value function over remaining balls and wickets, *V*(b,w) = *r*(b,w) + *p*(b,w)·*V*(b+1,w+1) + (1−*p*(b,w))·*V*(b+1,w), whose ingredients are exactly the two quantities we target: per-ball expected runs *r*(b,w) and wicket probability *p*(b,w). WASP (Brooker & Hogan, 2012) popularized this recursion but deliberately models an average team against an average team, treating player identity as out of scope. Asif & McHale (2016) forecast win probability with a dynamic logistic regression. Davis et al. (2021) predict second-innings outcomes ball by ball with engineered per-player metrics, and Lamsal & Kahle (2024) extend the dynamic-regression line to IPL T20 with Bayesian priors. Swartz (2016, 2020) builds hierarchical empirical-Bayes per-ball outcome models that *do* condition on identity, but for simulation rather than a state-versus-identity decomposition. None reports the relative weight of identity against state, isolated to the death overs and scored properly for both targets.

**Pressure indices and contextual performance.** A second strand operationalizes "pressure" as a deterministic function of game state (Shah & Shah, 2014; Bhattacharjee & Lemmer, 2016; Mallawa Arachchi et al., 2024; Thomson et al., 2021). A recent higher-order Markov analysis (arXiv:2505.01849, 2025) confirms that pressure-index variance is largest in the death overs. Every member of this family *derives* pressure from state and then validates it by predicting outcomes; none separates pressure-as-state from pressure-as-residual-history.

**Machine learning for cricket, including the death phase.** A large applied-ML literature predicts match winners or innings totals with gradient boosting (Raju et al., 2024; Hassan et al., 2025), typically reporting accuracy or R² on aggregate quantities. A few works engage the death phase directly: Sahoo et al. (2024) use SHAP to model shot selection in the final over, and Jamil et al. (2023) identify death-phase performance factors in fifty-over cricket. These establish the death overs as a distinct regime and SHAP as the natural attribution tool, but stop short of a calibrated per-ball model of both targets.

**The hot hand and the streak-selection correction.** Gilovich et al. (1985) reported no positive autocorrelation in basketball shooting. Miller & Sanjurjo (2018) proved that the conditional-probability estimator used in that analysis carries a finite-sequence selection bias: conditioning on a realized streak inside a finite sequence makes the expected post-streak success rate strictly below the true rate, with the bias growing in streak length and shrinking in sequence length. Correcting for it reverses the canonical result (Miller & Sanjurjo, 2024). The tennis-momentum literature (Huang et al., 2025; Wang et al., 2024) has adopted permutation testing. Cricket has its own hot-hand strand, but it does not use the streak-selection correction: Durbach & Thiart (2007) test the perception of randomness in cricket scoring with run-based tests that predate Miller & Sanjurjo (2018), and Ram et al. (2022) report a significant hot-hand effect across players' *careers* using a self-exciting Hawkes point process on match-level performances, citing Miller–Sanjurjo only to frame the debate rather than applying their finite-sequence bias correction. Neither operates at the per-ball level nor de-biases the conditional-probability estimator. To our knowledge the streak-selection correction itself has not been imported into cricket.

**What this paper does that prior work does not.** We combine these strands into one experiment on the death-over regime: a state-versus-identity skill decomposition with held-out incremental skill (not just attribution); a direct test of the Markov assumption against pressure sequences; and the first application of the Miller–Sanjurjo correction — with a state-stratified permutation null — to per-ball cricket momentum.

---

## 3. Problem Formulation

**Targets.** The unit of analysis is a single delivery in overs 16–20 (zero-indexed overs 15–19). We model two per-ball targets separately, because our hypotheses make asymmetric and opposite-sign claims about them.

- **Expected runs.** `runs_off_bat ∈ {0,1,2,3,4,6}`, runs off the bat only (extras excluded), giving E[runs] via regression. The mean over legal balls is 1.424.
- **Wicket probability.** `wicket ∈ {0,1}`, set to 1 only for batter-attributable dismissals (bowled, caught, lbw, stumped, caught and bowled, hit wicket). Run-outs and similar are coded 0 for the primary target; a variant including them (`wicket_any`) is retained for robustness. The batter-credited wicket rate on legal balls is 8.0% (`wicket_any` 9.1%).

**The Markov value recursion.** Most in-play cricket models assume the Markov property: the distribution over the next ball depends only on the current state, not the path that reached it. Hypotheses H2 and H3 both test this assumption.

**The streak-selection bias.** For a binary success series *x₁…xₙ* and streak length *k*, the naive hot-hand statistic is *D̂* = P̂(*xₜ*=1 | preceding *k* successes) − P̂(*xₜ*=1 | preceding *k* failures). Miller & Sanjurjo (2018) show that, in a finite sequence with a fixed number of successes, conditioning on a realized streak biases the post-streak rate *below* the true probability, so E[*D̂*] < 0 even under exchangeability. The bias grows with *k* and shrinks with *n*. This matters acutely for cricket death-over stays, which are short (often 4–18 balls).

---

## 4. Method

### 4.1 Data and splits

We use the open Cricsheet ball-by-ball corpus, taking the men's IPL and men's T20I CSV bundles (`ipl_male_csv2.zip`, `t20s_male_csv2.zip`), downloaded 2026-05-29. From 1,052,624 parsed deliveries we keep the 223,678 death-over deliveries (overs 16–20) from 4,402 matches (IPL 67,071; T20I 156,607), spanning 2005–2026. The legal-ball fraction is 0.952, and 139 Duckworth–Lewis-affected matches are flagged so required-run-rate features are blanked for those chases.

We use a temporal, match-grouped split: train on seasons ≤ 2024 (172,593 deliveries), validate on 2025 (28,202), and test on 2026 (22,883). No match appears in two splits, and no test delivery informs training, including the identity encodings. Hyperparameters are chosen by 5-fold GroupKFold (grouped by `match_id`) on the training portion only.

### 4.2 Feature groups

- **State (S):** balls remaining, over, ball-in-over, wickets in hand, current score and run rate, and (chase only) target, runs required, balls remaining, required run rate, RRR − CRR, plus an `is_chase` flag.
- **Batter identity (B):** empirical-Bayes target encodings from deliveries strictly before the current match — death strike rate, boundary rate, dot rate, dismissal rate, prior-balls exposure — shrunk toward the global death mean (α ≈ 50 balls).
- **Bowler identity (W):** analogous encodings (economy, dot rate, wicket rate, boundary-conceded rate, prior balls).
- **Deterministic pressure index (P):** a Bhattacharjee–Lemmer-style scalar from required rate, balls used, and a wicket weight — a function of state, the baseline that history must beat.
- **Pressure history (H):** length of the current consecutive dot-ball run, balls since last wicket, balls since last boundary, and a dot-run × RRR interaction, on legal striker-faced balls, reset at innings start.

To guard against identity encodings smuggling in state information, we regress each encoding on the state group and report its R² (leakage audit).

### 4.3 Models and the nested ladder

The primary learner is LightGBM: a binary classifier for the wicket head (with class balancing, isotonic-calibrated on validation) and a regressor for the runs head, plus a multinomial head over {0,1,2,3,4,6} from which E[runs] and a CRPS are read off. Hyperparameters are fixed and modest: 600 estimators with early stopping, learning rate 0.03, 31 leaves, `min_child_samples` 200, 0.8 subsample/column sampling, tuning only `num_leaves` and `min_child_samples` by GroupKFold. A regularized GLM is retained as a reference learner.

| Model | Features | Purpose |
|---|---|---|
| M0 | base rate | naive floor |
| M_S | S | state-only (Markov backbone) |
| M_SB | S + B | + batter identity |
| M_SW | S + W | + bowler identity |
| M_SBW | S + B + W | full identity (H1) |
| M_SBW+P | + P | state-derived pressure (H2 baseline) |
| M_SBW+P+H | + H | pressure history (H2 test) |

*Table 1. The nested model ladder. H1 compares M_S against the identity models; H2 compares M_SBW+P+H against M_SBW+P.*

Incremental skill is Δ = score(simpler) − score(richer) (positive denotes improvement), with match-clustered bootstrap 95% CIs (1000 replicates resampling whole matches).

### 4.4 The Miller–Sanjurjo momentum test (H3)

The primary sequence unit is a single batter's death-over stay within one innings, restricted to legal balls faced; a wicket ends the stay. The primary success definition is a scoring shot (`runs_off_bat ≥ 1`); a boundary definition is reported alongside. For each sequence *i* of length *nᵢ* with *sᵢ* successes and streak length *k*: (1) compute the observed difference *Dᵢ*; (2) compute the permutation-expected difference E₀[*Dᵢ*] by enumerating all C(*nᵢ*,*sᵢ*) rearrangements (or Monte-Carlo sampling up to 2000 when large) — the Miller–Sanjurjo bias; (3) form *D̃ᵢ* = *Dᵢ* − E₀[*Dᵢ*]; (4) aggregate, weighted by the number of valid conditioning instances, to obtain *D*_corr alongside *D*_naive. The quantity we report is the gap *D*_corr − *D*_naive. Significance uses two permutation nulls (*B* = 2000, reduced from a preregistered 5000 for runtime; because the bias and the corrected effect differ by an order of magnitude, this changes only *p*-value resolution, not which side of significance the result falls on): an unconditional within-sequence null, and a state-stratified null that permutes outcomes only within cells of {over, wickets-in-hand bucket, required-rate/score bucket}. We sweep *k* ∈ {1,2,3} over both success definitions and both directions, controlling the family with Benjamini–Hochberg FDR; the preregistered primary test is *k*=1, scoring shot, hot hand, state-stratified null.

All model metrics are reported as the mean over five seeds {0,1,2,3,4}; H1 SHAP, H2 incremental, and H3 use the seed-0 fitted models on the held-out 2026 season. Grouped SHAP is computed with TreeSHAP on ~20,000 sampled test rows.

---

## 5. Experiments

**Overview.** Three findings emerge. (i) A game-state-only model is the best-calibrated wicket model; adding identity *worsens* held-out log-loss and does not lower runs RMSE, even though SHAP attributes most mass to identity. (ii) Pressure history adds significant skill to expected runs but nothing to wicket probability. (iii) The apparent death-over momentum effect is largely a Miller–Sanjurjo finite-sequence artifact; no cell survives correction.

### 5.1 Calibrated per-ball benchmark

For the wicket head, the state-only model M_S achieves the best log-loss (0.27381), improving only marginally on the base rate (0.27484); every model that adds identity is worse, with full-identity M_SBW at 0.27495 — above the base rate. For the runs head, state captures most of the gain over the base rate (RMSE 1.728 → 1.688); adding identity *raises* RMSE while *lowering* MAE. The full model M_SBW+P+H attains the lowest RMSE (1.686) and MAE (1.233); the history group, not identity, moves RMSE back below state-only. Seed stability is high (M_S wicket log-loss std 7.9×10⁻⁵; M_S runs RMSE std 1.4×10⁻⁴); identity models show larger seed variance.

| Model | log-loss ↓ | Brier ↓ | ECE ↓ | PR-AUC ↑ |
|---|---|---|---|---|
| M0 (base rate) | 0.27484 | 0.07225 | 0.0000 | 0.0784 |
| **M_S (state-only)** | **0.27381** | 0.07211 | 0.0029 | 0.0904 |
| M_SB (+batter) | 0.27413 | 0.07214 | 0.0029 | 0.0880 |
| M_SW (+bowler) | 0.27462 | 0.07212 | 0.0019 | 0.0881 |
| M_SBW (+both) | 0.27495 | 0.07220 | 0.0026 | 0.0847 |
| M_SBW+P | 0.27423 | 0.07216 | 0.0021 | 0.0858 |
| M_SBW+P+H | 0.27408 | 0.07214 | 0.0019 | 0.0869 |

*Table 2. Wicket head P(wicket) on the held-out 2026 season, mean over five seeds. State-only is the best-calibrated model; adding identity worsens log-loss, and no model meaningfully beats the base rate.*

| Model | RMSE ↓ | MAE ↓ | CRPS ↓ |
|---|---|---|---|
| M0 (base rate) | 1.72835 | 1.29117 | — |
| M_S (state-only) | 1.68751 | 1.25512 | — |
| M_SB (+batter) | 1.69154 | 1.24305 | — |
| M_SW (+bowler) | 1.69029 | 1.24746 | — |
| M_SBW (+both) | 1.69208 | 1.24063 | — |
| M_SBW+P | 1.69173 | 1.23991 | — |
| **M_SBW+P+H** | **1.68639** | **1.23287** | — |
| M_mult (multinomial) | 1.69063 | 1.23843 | 0.81604 |

*Table 3. Runs head E[runs] on the held-out 2026 season, mean over five seeds. The full model attains the lowest RMSE and MAE, driven by the history group.*

![Model ladder](paper-latex/figures/fig3_model_ladder.png)

*Figure 3. The nested model ladder for both targets. Adding identity fails to improve held-out wicket log-loss and does not lower runs RMSE; the gains over the base rate come from game state, and only the pressure history group pushes runs RMSE below state-only.*

### 5.2 H1: state versus identity, and the SHAP–skill dissociation

TreeSHAP attributes the majority of explanatory mass to batter identity — 50.6% for runs and 63.7% for wickets — with state at 31.1%/26.0% and bowler at 18.3%/10.3%. Yet the held-out incremental skill of identity over state is zero or negative. For the wicket head, adding batter identity changes log-loss by −0.00033 with a CI including zero; for runs, adding identity is significantly *negative* (B|S RMSE −0.0053, 95% CI [−0.0089, −0.0019]). A leakage audit finds only modest shared variance between the identity encodings and state (max R² = 0.17 for `bat_deathSR`), ruling out the crudest contamination but not establishing the mechanism; the random-player placebo (§5.3) is the cleaner control and confirms in-sample overfitting of non-stationary player form: EB historical rates explain training variance — hence the SHAP mass — but do not transfer to the next season.

The predicted asymmetry holds: identity's share of total state-plus-identity skill is −0.137 for runs and −0.493 for wickets, an asymmetry (runs − wicket) of +0.356. State explains ~40× more skill for runs (RMSE gain 0.0409) than for wickets (log-loss gain 0.0010).

![Grouped SHAP](paper-latex/figures/fig1_grouped_shap.png)

*Figure 1. Grouped SHAP mass (% of total |SHAP|) for M_SBW. Batter identity dominates attribution for both targets despite adding no positive held-out skill.*

| Target | Added | Incr. skill | 95% CI |
|---|---|---|---|
| wicket (log-loss) | B \| S | −0.00033 | [−0.00097, +0.00036] |
| wicket (log-loss) | W \| S | +0.00024 | [−0.00035, +0.00082] |
| wicket (log-loss) | BW \| S | −0.00033 | [−0.00128, +0.00062] |
| runs (RMSE) | B \| S | −0.00531 | [−0.00889, −0.00192] |
| runs (RMSE) | W \| S | −0.00271 | [−0.00496, −0.00056] |
| runs (RMSE) | BW \| S | −0.00492 | [−0.00840, −0.00153] |

*Table 4. Held-out incremental skill of identity over state (match-clustered bootstrap, 1000 reps). Positive denotes improvement. Wickets include zero; runs are significantly negative.*

![H1 incremental forest](paper-latex/figures/fig2_h1_incremental_forest.png)

*Figure 2. Forest plot of identity's held-out incremental skill over state. No identity addition yields a significant positive improvement; for runs the effect is significantly negative.*

| Identity feature | R² vs. state |
|---|---|
| bat_deathSR | 0.169 |
| bat_boundary_pct | 0.151 |
| bat_dot_pct | 0.147 |
| bat_n_prior_balls | 0.111 |
| bowl_boundary_conceded_pct | 0.083 |
| bowl_n_prior_balls | 0.077 |
| bowl_deathER | 0.073 |
| bowl_dot_pct | 0.039 |
| bat_dismissal_rate | 0.020 |
| bowl_wicket_rate | 0.009 |

*Table 5. Leakage audit: R² of each identity encoding regressed on state. Shared variance is modest (max 0.17), so the encodings are not simply restating state; the random-player placebo (§5.3) provides a more direct control for the dissociation.*

### 5.3 Robustness: a placebo and a six-season rolling window

The H1 dissociation invites two objections: that the SHAP mass is an artifact of feeding the model high-variance numeric features rather than real player signal, and that "identity hurts" is specific to the single 2026 test season. We address both.

**Random-player placebo.** We refit the full M_SBW model with the player→encoding mapping randomly shuffled, so each player receives another player's historical encoding: the marginal feature distribution is preserved but player-specific signal is destroyed. Batter SHAP mass collapses from 50.6%/63.7% (runs/wicket) to 7.5%/6.9% under the placebo, with the freed mass flowing to state — so the attribution is *faithful*: the model genuinely keys on real players. Yet real identity's out-of-sample skill is actually *worse* than the placebo's: real identity significantly hurts expected-runs RMSE (−0.0049, 95% CI [−0.0085, −0.0013]) while random encodings are harmless (+0.0002, CI spanning zero). The dissociation is genuine overfitting of non-stationary form, not a leakage or cardinality artifact.

| Encoding | Batter SHAP (runs/wkt) | Runs incr. skill (BW\|S) | Wicket incr. (BW\|S) |
|---|---|---|---|
| Real identity | 50.6% / 63.7% | −0.0049 [−0.0085, −0.0013] | −0.00033 [−0.0013, +0.0006] |
| Shuffled placebo | 7.5% / 6.9% | +0.0002 [−0.0006, +0.0011] | +0.00008 [−0.0004, +0.0005] |

*Table 6. Random-player placebo. Real identity dominates SHAP yet hurts runs RMSE; shuffling collapses the attribution and leaves skill at zero — faithful attribution, no generalizable skill.*

![Identity placebo](paper-latex/figures/fig6_identity_placebo.png)

*Figure 6. Left: batter-group SHAP mass collapses from ~50–64% to ~7–8% when player identities are shuffled. Right: real identity significantly hurts expected-runs RMSE while the placebo is harmless.*

**Rolling-window evaluation.** We repeat the held-out-season protocol for every feasible test season 2021–2026 (train ≤ T−2, validate on T−1, test on T). In *all six* seasons a state-only model beats state-plus-identity on expected-runs RMSE, and the identity increment is significantly negative (interval excludes zero) every season, ranging −0.0049 to −0.0131. Identity never improves wicket log-loss either. The finding is a consistent multi-season property, not a 2026 artifact.

| Test season | n | Runs RMSE: state → state+id | Identity incr. (runs) | Sig.? |
|---|---|---|---|---|
| 2021 | 14,437 | 1.710 → 1.717 | −0.0074 [−0.0126, −0.0021] | yes |
| 2022 | 25,545 | 1.701 → 1.712 | −0.0112 [−0.0152, −0.0071] | yes |
| 2023 | 20,373 | 1.679 → 1.692 | −0.0131 [−0.0183, −0.0082] | yes |
| 2024 | 28,969 | 1.684 → 1.689 | −0.0049 [−0.0080, −0.0012] | yes |
| 2025 | 28,202 | 1.700 → 1.708 | −0.0079 [−0.0118, −0.0043] | yes |
| 2026 | 22,883 | 1.687 → 1.692 | −0.0049 [−0.0085, −0.0013] | yes |

*Table 7. Rolling-window evaluation. Adding identity significantly raises expected-runs RMSE in every held-out season; state-only is never improved upon.*

![Rolling window](paper-latex/figures/fig7_rolling_window.png)

*Figure 7. Six-season rolling window. Left: identity's incremental skill on expected runs is negative with intervals excluding zero in all six seasons. Right: state-only RMSE is below state-plus-identity every season.*

### 5.4 H2: a Markov violation for runs, not wickets

Adding pressure history on top of the full state+identity+PI model (M_SBW+P+H − M_SBW+P) yields significant incremental skill for expected runs (RMSE Δ = +0.0065, 95% CI [0.0048, 0.0083], excluding zero), with the `dot_run_len` SHAP sign *negative* — longer preceding dot runs lower the next ball's expected runs. For wicket probability the history group adds nothing significant (both intervals include zero). The Markov property is violated for scoring intensity but holds for dismissal risk: the residual pressure effect is scoring suppression, not added wicket risk.

| Target | Metric | Δ | 95% CI | sig. |
|---|---|---|---|---|
| wicket | log-loss | +0.000165 | [−0.000132, +0.000440] | no |
| wicket | Brier | +0.000021 | [−0.000023, +0.000065] | no |
| runs | RMSE | **+0.006500** | **[+0.00481, +0.00826]** | **yes** |

*Table 8. H2 incremental skill of pressure history beyond state + identity + pressure index. History helps expected runs significantly (negative dot-run sign), nothing for wickets.*

![H2 incremental](paper-latex/figures/fig4_h2_incremental.png)

*Figure 4. Incremental skill of the pressure-history group. Significant for expected runs (interval excludes zero), null for wicket probability.*

### 5.5 H3: momentum is a Miller–Sanjurjo artifact

On the preregistered primary test (*k*=1, scoring shot, hot hand, state-stratified null), the naive estimator reports a strong negative effect, *D*_naive = −0.114 — an apparent "cold hand." But the Miller–Sanjurjo bias is E₀ = −0.121, nearly equal and opposite. The corrected estimate is *D*_corr = +0.007, and the gap is +0.121 — the correction moves the answer about twelve percentage points. Against the state-stratified null the corrected estimate is not significant (*p* = 0.402, BH-adjusted 0.9995).

Across the full sweep (1,760 sequences for the primary cell), the naive estimate is always sizeable (|*D*_naive| up to 0.31 at *k*=3) while the corrected estimate stays small (|*D*_corr| ≤ 0.07), and the bias grows monotonically with *k* — the signature Miller–Sanjurjo pattern. After Benjamini–Hochberg correction, *none* of the twelve tests is significant at 0.05 (smallest adjusted *p* = 0.072, for boundary/cold/*k*=1). The naive uncorrected *p*-values flag several "significant" cells (e.g. *k*=3 raw *p* ≈ 0.0005) that are bias artifacts. We therefore find no statistically significant per-ball momentum once the bias is removed and game state is controlled. We report the +0.121 gap as the primary quantity: an estimate of the apparent momentum introduced by the naive estimator.

| Test (*k*, def, dir) | *D*_naive | bias | *D*_corr | *p*_strat | BH |
|---|---|---|---|---|---|
| 1, score, hot★ | −0.114 | −0.121 | +0.007 | 0.402 | 0.9995 |
| 2, score, hot | −0.156 | −0.225 | +0.069 | 0.096 | 0.579 |
| 3, score, hot | −0.222 | −0.290 | +0.069 | 0.737 | 0.9995 |
| 1, score, cold | +0.090 | +0.088 | +0.002 | 0.696 | 0.9995 |
| 1, bndry, hot | −0.131 | −0.127 | −0.004 | 0.698 | 0.9995 |
| 1, bndry, cold | +0.038 | +0.031 | +0.007 | 0.006 | 0.072 |

*Table 9. Selected H3 results on batter death-over stays. ★ = preregistered primary test. The naive estimate is large in every cell; after removing the bias the corrected estimate is near zero, and no cell survives Benjamini–Hochberg correction.*

![H3 momentum](paper-latex/figures/fig5_h3_momentum.png)

*Figure 5. Naive versus Miller–Sanjurjo-corrected momentum by streak length. The naive estimate grows with k, tracked almost exactly by the finite-sequence bias; the corrected estimate stays near zero. The +0.121 gap at the primary test is the size of the illusion.*

---

## 6. Discussion

**Why identity adds little over state at the death.** A plausible reading is that the death overs compress the decision space. With few balls and wickets left, the situation constrains intent strongly — most batters attack and most bowlers defend regardless of who they are — so the state features appear to capture most of the recoverable signal. That state explains ~40× more skill for runs than for wickets is consistent with the mechanism we hypothesized: scoring is where elite finishers separate, while death-over wickets are driven by high-variance events that are largely unpredictable from the observed state. The wicket head barely improves on the base rate for any model, and H2 finds no path-dependence in wicket risk — two consistent indications of the same limited predictability.

**The SHAP–skill dissociation.** A result worth dwelling on is the gap between attribution and skill. TreeSHAP credits batter identity with the majority of explanatory mass, yet identity adds no positive held-out skill and significantly hurts runs RMSE in every one of six seasons. The random-player placebo isolates the mechanism: shuffling player identities collapses batter SHAP mass from 51–64% to 7–8%, so the model genuinely keys on real players (faithful attribution, not a high-variance-feature artifact), but real identity is no more useful out-of-sample than the shuffled placebo and in fact slightly worse. The explanation is overfitting of non-stationary form. Practitioners who read SHAP mass as importance, without an out-of-sample skill check, would conclude that death-over modeling should center on player identity; the held-out evidence says the opposite. This is a concrete cautionary case for pairing attribution with proper out-of-sample scoring. We are careful about scope: this shows that *our* identity representation does not generalize, not that player identity is irrelevant in principle.

**What the Markov violation does and does not mean.** H2 shows a genuine but narrow departure from the Markov assumption: longer preceding dot runs lower the next ball's expected runs, beyond state, identity, and a deterministic pressure index. The effect is on scoring suppression, not dismissal risk. This asymmetry is the finding that most complicates a blanket "momentum is an illusion" reading, and our design identifies the effect but not its mechanism. Several non-exclusive pathways are consistent with it: bowler–captain adaptation (a dot run marks a bowler executing well and field settings the over-level state does not capture), batter recalibration (rationally lowering risk after consecutive dots), and strike-rotation/matchup effects (the striker pinned against a difficult matchup). We cannot separate these observationally, and the dot-run feature is plausibly confounded with bowler quality even after our controls, so the H2 effect should be read as associational. What we can say is narrow: conditional on a rich state-plus-identity model, recent dot balls carry residual information about scoring intensity but not about wicket risk.

**Apparent momentum and the streak-selection bias.** H3 returns to the momentum question. The naive cricket momentum estimator reports a strong "cold hand," and a reader applying the standard conditional-probability comparison would be liable to treat that as real and even "significant" at higher *k*. We find it is largely a finite-sequence selection artifact. Death-over stays are short, the regime where the bias is largest, so it is a setting where omitting the correction is particularly consequential. We frame the conclusion as an absence of evidence rather than evidence of absence: after correction and state control we find no statistically significant per-ball momentum, which is not the same as proving momentum cannot exist at any scale or for any player. We report the +0.121 gap as the study's main quantity: it estimates how much of the apparent momentum is introduced by the estimator rather than supported by the data.

**Limitations.** The most important limitation is that our finding concerns a *representation* of identity, not identity in principle. We encode players by empirical-Bayes historical death-over rates; this omits handedness, explicit batter–bowler matchup terms, venue/conditions, and short-horizon recent form. It is possible that identity "did not fail" so much as our encoding of it did, and that a richer, interaction-aware representation would recover out-of-sample skill. The placebo shows our encoding carries genuine, faithfully-attributed signal that nonetheless does not generalize; it does not show that no representation could. Second, the identity encoders use a simplified two-pool historical scheme (pre-(T−3) for training, pre-(T−2) for evaluation) rather than strict per-match encoding; the leakage audit and placebo argue against contamination, but a stricter encoding could shift the estimates. Third, the main calibration tables use a single held-out test season (2026); the rolling-window study extends the central identity result across 2021–2026, but the H2 and H3 analyses are reported on 2026 only. Fourth, the H3 permutation count was B = 2000 (from a preregistered 5000), affecting *p*-value resolution, not the conclusions. Fifth, the dot-run pressure feature is plausibly confounded with bowler quality, so the H2 effect is associational. Finally, WASP's canonical description is non-archival, so we cite it by its dynamic-programming formulation.

**Future work.** (1) Build a richer identity representation — handedness, explicit batter–bowler matchup encodings, venue and recent-form features — and test whether it recovers the out-of-sample skill the historical-rate encoding does not. (2) Extend the rolling-window protocol to the H2 and H3 analyses (currently 2026 only), with a stricter per-match identity encoding and a GLM-versus-LightGBM learner check. (3) Extend the Miller–Sanjurjo analysis to women's T20 and to other phases, where sequence lengths and base rates differ, to map how the size of the apparent-momentum illusion varies with the regime.

---

## 7. Conclusion

We built calibrated per-ball models of expected runs and wicket probability for the T20 death overs on 223,678 deliveries and decomposed their predictive skill into game state and a historical-rate encoding of player identity. We find no evidence that this identity encoding improves on a state-only model out-of-sample: the state-only model is the best-calibrated wicket model, and adding identity worsens held-out log-loss and significantly raises runs RMSE in all six rolling test seasons, even though SHAP attributes the majority of explanatory mass to identity. A random-player placebo shows this attribution is faithful but does not generalize — a dissociation we trace to overfitting of non-stationary form, with the caveat that it concerns our historical-rate encoding of identity rather than identity in principle. Pressure history violates the Markov assumption for scoring intensity (RMSE +0.0065, dot-run sign negative) but not for wicket risk. Applying the Miller–Sanjurjo correction to cricket — to our knowledge for the first time — we show the apparent death-over momentum is almost entirely a finite-sequence artifact: the naive −0.114 estimate is matched by a −0.121 bias, the corrected estimate is +0.007, and no cell survives a state-stratified null. These results support identity-agnostic, state-based per-ball models for the death overs as a calibrated default, caution against reading SHAP attribution as out-of-sample importance, and give the cricket pressure literature a bias correction it has lacked.

---

## References

- Asif, M. & McHale, I. G. (2016). In-play forecasting of win probability in One-Day International cricket: A dynamic logistic regression model. *International Journal of Forecasting*, 32(1), 34–43.
- Benjamini, Y. & Hochberg, Y. (1995). Controlling the False Discovery Rate. *Journal of the Royal Statistical Society: Series B*, 57(1), 289–300.
- Bhattacharjee, D. & Lemmer, H. H. (2016). Quantifying the pressure on the teams batting or bowling in the second innings of limited overs cricket matches. *International Journal of Sports Science and Coaching*, 11(5), 683–692.
- Brooker, S. & Hogan, S. (2012). The WASP (Win and Score Predictor): a dynamic-programming value function for limited-overs cricket. Non-archival; documented by New Zealand Cricket and the authors.
- Davis, J., Perera, H. & Swartz, T. B. (2021). Dynamic cricket match outcome prediction. *Journal of Sports Analytics*, 7(3), 185–196.
- Durbach, I. N. & Thiart, J. (2007). On a common perception of a random sequence in cricket. *South African Statistical Journal*, 41(2), 161–187.
- Gilovich, T., Vallone, R. & Tversky, A. (1985). The hot hand in basketball. *Cognitive Psychology*, 17(3), 295–314.
- Hassan, M. et al. (2025). Outcome Prediction of Bangladesh Premier League T20 Cricket via Ensemble Learning. *IEEE QPAIN*.
- Huang, Y. et al. (2025). Unraveling Psychological Momentum in Tennis via Machine Learning. *IEEE BDAI*.
- Jamil, M., Kerruish, S., Hughes, M. & Liu, H. (2023). Factors impacting batting and bowling performance in the "death" phase of one-day international cricket. *International Journal of Performance Analysis in Sport*, 23(2), 111–124.
- Ke, G. et al. (2017). LightGBM: A Highly Efficient Gradient Boosting Decision Tree. *NeurIPS*.
- Lamsal, R. & Kahle, C. (2024). In-Game Win Prediction Models for Cricket. *Springer CCIS (SDSC 2024)*.
- Lundberg, S. M. & Lee, S.-I. (2017). A Unified Approach to Interpreting Model Predictions. *NeurIPS*.
- Mallawa Arachchi, S., Manage, A. B. W. & Scariano, S. M. (2024). A pressure index for the team batting second in a T20I cricket match. *Journal of Sports Analytics*.
- Miller, J. B. & Sanjurjo, A. (2018). Surprised by the Hot Hand Fallacy? A Truth in the Law of Small Numbers. *Econometrica*, 86(6), 2019–2047.
- Miller, J. B. & Sanjurjo, A. (2024). A Cold Shower for the Hot Hand Fallacy. *Review of Economics and Statistics*, 106(6), 1607–1620.
- Raju, S. et al. (2024). IPL Dream11 Fantasy Team Prediction using Machine Learning. *ACM World Symposium on Software Engineering*.
- Ram, S. K., Nandan, S. & Sornette, D. (2022). Significant hot hand effect in the game of cricket. *Scientific Reports*, 12, 11663.
- Rushe, S. (2024). Cricsheet: Ball-by-ball data for cricket matches. https://cricsheet.org
- Sahoo, S., Deyar, S. & Gupta, P. (2024). Shot Selection in the Death Over of T20 Cricket using Machine Learning. *IEEE I2CT*.
- Shah, P. & Shah, M. (2014). Pressure Index in Cricket. *IOSR Journal of Sports and Physical Education*, 1(5), 9–11.
- Swartz, T. B. (2016). A Simulator for Twenty20 Cricket. SFU working paper.
- Swartz, T. B. (2020). Expected Economy Rate (xER). SFU working paper.
- Thomson, C., Davis, J. & Swartz, T. B. (2021). Contextual Batting and Bowling in Twenty20 Cricket. SFU working paper.
- Wang, J., Guo, Y. & Zhou, X. (2024). A multidimensional momentum chain model for tennis match prediction. *PLoS ONE*.
- Anonymous (2025). Higher-order Markov chains and a pressure index for controlled run chases in T20 cricket. arXiv:2505.01849.
