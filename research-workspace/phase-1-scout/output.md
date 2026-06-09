# Phase 1 — Scout: Literature Search & Gap Analysis

**Research idea.** Per-delivery prediction of expected runs and wicket probability in T20 death overs (overs 16–20) from game state (over, balls remaining, wickets in hand, required run rate in chases) and batter–bowler identity — identifying which factors carry the most weight; plus whether "pressure sequences" (dot-ball runs, recent wickets) shift outcomes beyond what game state alone predicts.

---

## 1. Search Log

Tools used: Semantic Scholar MCP (`relevanceSearch`), Exa MCP (`web_search_exa`), arXiv search (`search_arxiv`), and WebSearch. Searches run:

1. **Broad** — "T20 cricket ball-by-ball predictive modeling expected runs win probability" (Semantic Scholar; rate-limited on first pass, partial)
2. **ML/outcome** — "cricket match outcome prediction machine learning gradient boosting" (Semantic Scholar) → BPL/IPL ensemble studies, Davis/Goel ball-by-ball
3. **Momentum/hot hand** — "momentum pressure hot hand sports outcome prediction" (Semantic Scholar) → GVT-lineage, tennis momentum ML
4. **Win-prob models** — "cricket win probability WASP Duckworth-Lewis expected runs ball by ball" (Exa) → WASP, Swartz simulator, Asif–McHale, In-Game Win Prediction (Bayesian)
5. **Pressure index** — "pressure index cricket scoring rate dot balls T20 batting" (Exa) → Bhattacharjee–Lemmer, Shah–Shah, Mallawa Arachchi, Markov/PI arXiv, dot-ball win-prob study
6. **Hot-hand foundations** — "Gilovich Tversky hot hand + Miller Sanjurjo correction" (Exa) → GVT 1985, Miller–Sanjurjo 2018/2024
7. **Expected runs ML** — "expected runs per ball cricket gradient boosting XGBoost feature importance Cricsheet" (Exa) → Swartz xER (xG-for-cricket), numerous Cricsheet/XGBoost projects
8. **Asif–McHale** (WebSearch) — confirmed venue/DOI
9. **Bhattacharjee–Lemmer** (WebSearch) — confirmed venue/DOI
10. **Death overs** — "T20 cricket death overs analysis overs 16-20" (Exa) → Jamil death-phase studies, Swartz contextual/clutch, MDP optimisation

All papers below were retrieved directly via these tools. None are reconstructed from memory. A few popular/preprint sources are marked accordingly.

---

## 2. Literature Map

### Cluster A — Per-delivery / in-play win-probability and expected-runs models
These works model cricket at the ball level, predicting either win probability or expected runs as a function of match state, and form the methodological backbone for the proposed work. The dominant formalism is the dynamic-programming/Markov value function V(b,w) = r(b,w) + p(b,w)·V(b+1,w+1) + (1−p(b,w))·V(b+1,w), where r is per-ball expected runs and p is per-ball wicket probability — exactly the two quantities this project targets.

| Paper | Year | Venue | Key Contribution |
|-------|------|-------|-----------------|
| Brooker & Hogan — WASP (Win and Score Predictor) | ~2012 | Industry/Sky NZ; documented on Wikipedia & author blog [UNVERIFIED as peer-reviewed paper — primary source is creators' blog + NZC] | Dynamic-programming value function over (balls, wickets) giving per-ball expected runs r(b,w) and wicket prob p(b,w); explicitly "average team vs average team" — deliberately excludes player identity. |
| Asif & McHale — In-play forecasting of win probability in ODI cricket | 2016 | Int. J. Forecasting 32(1):34–43 | Dynamic logistic regression (DLR): logistic win-prob model whose coefficients evolve smoothly with match progress; few parameters, stable forecasts comparable to betting markets. |
| Davis, Goel et al. — Dynamic cricket match outcome prediction | 2021 | J. Sports Analytics | Ball-by-ball second-innings outcome model using engineered per-player metrics + dynamic target; compares classical ML (~76%) vs LSTM/GRU (~76%). |
| Lamsal & Kahle — In-Game Win Prediction Models for Cricket | 2024 | Springer CCIS (SDSC 2024) | Bayesian extension of Asif–McHale for IPL T20: power priors for historical data + Gaussian-process smoothing of dynamic coefficients; improves Brier score/accuracy. |
| Swartz — A Simulator for Twenty20 Cricket | ~2016 | SFU working paper / JQAS-lineage | Hierarchical empirical-Bayes multinomial per-ball outcome model conditioned on batsman, bowler, over, wickets; second-innings aggressiveness keyed to target. Directly yields E[runs] per ball. |
| Swartz — Expected Economy Rate (xER) | ~2020 | SFU working paper | Brings the "expected goals (xG)" idea to cricket: random-forest per-ball outcome probabilities from 25 covariates; Brier 0.33 (RF) vs 0.73/0.84 baselines on 123k men's / 167k women's balls. |

### Cluster B — Pressure indices and contextual/clutch performance in cricket
This cluster operationalizes "pressure" as deterministic functions of game state (required run rate, resources consumed, wickets lost). They are descriptive constructs, not predictive tests — pressure is *defined* from state, then used to evaluate players or predict outcomes, rather than tested as a residual effect beyond state.

| Paper | Year | Venue | Key Contribution |
|-------|------|-------|-----------------|
| Shah & Shah — Pressure Index in Cricket | 2014 | J. Sports & Physical Education 1(5):9–11 | Original ball-by-ball Pressure Index (function of req. rate / initial req. rate, wicket weight, balls/runs left), benchmarked to 100; built from ~150 T20 matches (Cricinfo). |
| Bhattacharjee & Lemmer — Quantifying the pressure on teams batting/bowling, 2nd innings | 2016 | Int. J. Sports Science & Coaching 11(5):683–692 | PI3 (mean of PI1 sensitive to wickets, PI2 sensitive to resources used) using D/L resources; used for player evaluation, turning points, and outcome prediction. The most-cited cricket pressure index. |
| Mallawa Arachchi, Manage & Scariano — A pressure index for the team batting second in T20I | 2024 | J. Sports Analytics (JSA-240792) | Derives PI from a differential equation; scales 0–10 keyed to target; couples to per-delivery stage-specific logistic regressions to predict win probability. Critiques that earlier indices all start at unity (can't distinguish target difficulty). |
| Thomson, Davis & Swartz — Contextual batting & bowling (clutch) | ~2021 | SFU working paper | Uses runs-to-resources ratio r as contextual urgency; defines "clutch batting/bowling" on a shared scale for challenging chases; r>3.33 → batting wins only 25%. |
| (arXiv 2505.01849) — Higher-order Markov + Pressure Index for controlled run chases | 2025 | arXiv preprint | Third-order Markov chain on over-end PI over 6,537 T20 matches; phase-wise (incl. death overs 16–20) gamma fits; prescriptive PI targets. Confirms PI variance is largest in death overs. |

### Cluster C — ML for cricket outcome / score / player-performance prediction (incl. death overs)
A large, somewhat repetitive applied-ML literature. Gradient boosting (XGBoost/LightGBM/CatBoost) and random forests are the consensus workhorses. Most predict match winner or innings total (aggregate), not calibrated per-ball expected runs/wicket probability; reported "98–99% R²" figures are usually score-prediction artifacts of cumulative features. A handful touch death overs or batter–bowler matchups specifically.

| Paper | Year | Venue | Key Contribution |
|-------|------|-------|-----------------|
| Sahoo, Deyar & Gupta — Shot selection in the death over of T20 using ML | 2024 | IEEE I2CT | Ensemble + SHAP to predict batter shot selection in the final over (Cricsheet/ESPNcricinfo); one of the few explicitly death-over, per-ball, interpretability-focused works. |
| Jamil, Kerruish et al. — Factors impacting batting/bowling in the "death" phase (50-over) | 2023 | Int. J. Performance Analysis in Sport 23(2):111–124 | Identifies death-phase performance factors via regression; establishes death overs as a distinct modeling regime (50-over, not T20). |
| Raju et al. — IPL Dream11 fantasy team prediction | 2024 | World Symp. Software Eng. (ACM) | Builds explicit batsman–bowler matchup rows from Cricsheet 2016–2023; RF/XGBoost/CatBoost for runs/wickets/economy. Demonstrates feasibility of identity-level features from Cricsheet. |
| Hassan et al. — BPL T20 outcome via ensemble learning | 2025 | IEEE QPAIN | XGBoost/GBM ~97.7% match-winner accuracy with team-form + venue features (aggregate, not per-ball). |
| (arXiv 2604.13861) — Simulation-based optimisation of batting order & bowling plans in T20 | 2026 | arXiv (submitted JQAS) [UNVERIFIED — future-dated preprint] | MDP over (runs remaining, balls, wickets); three-phase (PP/Middle/Death) per-ball outcome profiles with James–Stein shrinkage from 1,161 IPL matches; optimizes win prob, not expected runs. |
| Goel et al. (above, also Cluster A) | 2021 | JSA | Per-player engineered metrics tracked ball-by-ball. |

### Cluster D — "Hot hand" / momentum: foundations and the methodological correction
The general-sports literature on whether streaks/momentum exist beyond chance. Critical for framing the secondary question rigorously: any "pressure sequence" test must benchmark against the correct conditional expectation, not the naive base rate.

| Paper | Year | Venue | Key Contribution |
|-------|------|-------|-----------------|
| Gilovich, Vallone & Tversky — The Hot Hand in Basketball | 1985 | Cognitive Psychology 17(3):295–314 | Canonical "hot hand is a misperception of random sequences" result; no positive autocorrelation in shot outcomes (≈100+ citations foundational). |
| Miller & Sanjurjo — Surprised by the Hot Hand Fallacy? | 2018 | Econometrica | Proves a streak-selection bias in GVT's conditional-probability estimator; bias-corrected re-analysis *reverses* GVT and finds real hot-hand effects (~+13pp). Methodologically essential. |
| Miller & Sanjurjo — A Cold Shower for the Hot Hand Fallacy | 2024 | Review of Economics & Statistics 106(6):1607 | Robust multi-dataset confirmation of hot-hand performance within individuals over time. |
| Huang et al. — Unraveling psychological momentum in tennis via ML | 2025 | IEEE BDAI | FSM + entropy-weighted features + permutation tests + GBDT (94.3% acc.); validates momentum non-randomness and ranks momentum-shift features. A template for "momentum-beyond-state" testing. |
| Wang, Guo & Zhou — Multidimensional momentum chain model for tennis | 2024 | PLoS ONE | Difference-equation momentum model with forgetting curve; >80% prediction accuracy across 6,870 matches. |

---

## 3. Synthesis

**Broad agreement.** The field converges on a small, stable set of state variables — balls remaining, wickets in hand, and (in chases) the target / required run rate — as the core determinants of per-ball outcomes. This is true whether the framework is dynamic programming (WASP; Brooker & Hogan), dynamic logistic regression (Asif & McHale 2016; Lamsal & Kahle 2024), hierarchical empirical Bayes (Swartz simulator), or pressure indices (Shah & Shah 2014; Bhattacharjee & Lemmer 2016). Crucially, the WASP value recursion *already decomposes win probability into exactly the two per-ball quantities this project targets*: expected runs r(b,w) and wicket probability p(b,w). So the primary question is well-posed and grounded in an established formalism.

**Where methods diverge.** Two axes. (1) **Identity vs. average team.** WASP, Asif–McHale, and the pressure-index family deliberately model an "average top-eight team vs average team" and treat batter/bowler identity as out-of-scope (WASP creators state this explicitly and reframe player skill as deviation from the WASP benchmark). In contrast, Swartz's simulator and xER, Goel et al. (2021), and the fantasy/matchup ML works (Raju et al. 2024) build identity in via per-player outcome distributions or matchup rows — but typically for player *evaluation* or *simulation*, not for a clean variance-decomposition answering "how much does identity add over state?" (2) **Target quantity & calibration.** The statistics/OR literature (Swartz, Asif–McHale, Lamsal–Kahle) prizes probabilistic calibration (Brier scores, betting-market comparison), whereas the applied-ML literature (Cluster C) overwhelmingly reports point-prediction R²/accuracy on aggregate score or match winner and rarely calibrates per-ball probabilities. xER (Swartz) is the clearest exception that pairs ML per-ball outcome probabilities with proper scoring (Brier 0.33 vs baselines).

**Shared assumptions.** Most in-play models assume the **Markov property** — that the distribution over future outcomes depends only on current state (runs remaining, balls, wickets), independent of *how* that state was reached (explicit in WASP and in the 2026 MDP preprint). This assumption is precisely what the secondary "pressure sequence" question challenges: if recent dot balls or a recent wicket shift the next ball's outcome *beyond* what state predicts, the Markov assumption is violated. No cricket in-play paper found here directly tests that violation at the delivery level.

**Metrics & data.** Cricsheet is the de facto open ball-by-ball source for T20 across nearly all applied works (Raju et al. 2024; numerous GitHub pipelines that engineer CRR/RRR, balls-left, wickets-left, rolling form). Proper-scoring metrics (Brier, log-loss) appear in the statistics tradition; R²/accuracy dominate applied ML. SHAP-based feature attribution is emerging (Sahoo et al. 2024 for death-over shot selection) and is the natural tool for the "which factors carry most weight" sub-question.

**State of the art & weaknesses.** The best-calibrated per-ball machinery (Swartz xER; Asif–McHale/Lamsal–Kahle DLR) is strong but (a) largely excludes or only partially incorporates batter–bowler identity, (b) treats the innings as a whole or via coarse phases rather than isolating death overs (16–20), and (c) assumes Markovian state with no test of within-innings sequence/momentum effects. The pressure-index family *defines* pressure from state and then validates by predicting outcomes — it never separates "pressure-as-state" from "pressure-as-residual-history-effect." The hot-hand literature (Cluster D) supplies the rigorous test design (Miller–Sanjurjo bias correction; permutation tests as in Huang et al. 2025) that the cricket literature has not yet imported for per-delivery momentum.

---

## 4. Gap Analysis

**Gap 1: No clean variance-decomposition of state vs. batter–bowler identity for per-ball expected runs *and* wicket probability, isolated to T20 death overs.**
- **What's missing:** A single model that predicts both per-delivery E[runs] and P(wicket) in overs 16–20 and quantifies how much predictive power comes from game state vs. batter/bowler identity (e.g., via SHAP / ablation / nested-model deviance).
- **Evidence it's real:** WASP and Asif–McHale (2016) deliberately exclude identity ("average team vs average team"); Swartz's simulator/xER include identity but for simulation/evaluation, not a state-vs-identity attribution. None reports the relative weight of identity vs state specifically for the death-over regime.
- **Why it matters:** Answers the user's "which factors carry the most weight" directly and tells practitioners whether death-over outcomes are driven by situation or by who is on the field.
- **Feasibility:** High. Cricsheet gives identity + state per ball (Raju et al. 2024 already build matchup rows from it); gradient boosting + SHAP is established (Sahoo et al. 2024).
- **Novelty:** Novel framing (the components exist; the decomposition for death overs does not).

**Gap 2: The Markov assumption underlying in-play cricket models is untested at the delivery level against "pressure sequences."**
- **What's missing:** A direct test of whether a run of dot balls or a recent wicket changes next-ball E[runs]/P(wicket) *after controlling for game state* — i.e., a residual momentum effect.
- **Evidence it's real:** WASP and the 2026 MDP preprint assert the Markov property; pressure indices (Bhattacharjee–Lemmer; Mallawa Arachchi 2024) *define* pressure from current state and never isolate a history-beyond-state component. No cricket paper found tests the residual.
- **Why it matters:** If momentum effects exist beyond state, every Markovian win-prob/expected-runs model (the field's backbone) is mis-specified in death overs, where stakes are highest.
- **Feasibility:** High. Add lagged-sequence features (dot-ball run length, balls since last wicket) to a state-only baseline and test incremental skill; or condition on state and test residual dependence.
- **Novelty:** Novel framing for cricket; methodologically anchored in an existing adjacent literature.

**Gap 3: The cricket "pressure"/momentum literature has not adopted the hot-hand methodological correction (streak-selection bias / permutation tests).**
- **What's missing:** Use of the Miller–Sanjurjo (2018) bias-corrected conditional-probability test (or permutation tests as in Huang et al. 2025 for tennis) to evaluate momentum in cricket sequences.
- **Evidence it's real:** Cluster B cricket works use deterministic indices and naive validation; none cite or apply the streak-selection-bias correction that overturned the canonical basketball result.
- **Why it matters:** Without the correction, any naive "dot balls → next-ball outcome" comparison is biased toward finding *no* effect (or the wrong sign) — exactly the error that hid the basketball hot hand for 31 years.
- **Feasibility:** High. The correction and permutation procedures are published and directly transplantable to binary/ordinal ball outcomes.
- **Novelty:** Novel framing (cross-disciplinary import; acknowledged gap in the general hot-hand literature, unaddressed in cricket).

**Gap 4: Death overs (16–20) are rarely modeled as a distinct per-ball regime; most work uses whole-innings or coarse three-phase splits.**
- **What's missing:** A model trained/evaluated specifically on the death-over regime, where scoring/wicket dynamics, variance, and required-run-rate pressure differ sharply.
- **Evidence it's real:** Phase splits exist (PP/Middle/Death) in the 2026 MDP preprint and arXiv 2505.01849, and Jamil et al. (2023) study death bowling — but in 50-over cricket and largely descriptively, not as calibrated per-ball T20 expected-runs/wicket models. arXiv 2505.01849 confirms PI variance is *largest* in death overs, underscoring that this regime behaves differently.
- **Why it matters:** Death overs decide T20 matches; a regime-specific model is both more accurate and more decision-relevant than a whole-innings average.
- **Feasibility:** High. Straightforward filtering of Cricsheet to overs 16–20; sample size remains large.
- **Novelty:** Partially acknowledged (phases are recognized) but under-executed as a calibrated per-ball T20 death-over model.

**Gap 5: Predictive performance is rarely reported with proper probabilistic scoring for *both* expected runs and wicket probability together.**
- **What's missing:** Joint, calibrated reporting (Brier/log-loss for wicket prob; RMSE/CRPS for expected runs) on a held-out death-over test set, with batter–bowler identity included.
- **Evidence it's real:** Applied-ML cluster reports inflated R²/accuracy on aggregate scores; Swartz's xER calibrates only the bowling/runs side (Brier 0.33) and not wicket prob jointly in death overs.
- **Why it matters:** Establishes a credible, reproducible benchmark on open Cricsheet data that future work can build on.
- **Feasibility:** High; standard scoring rules on a clean temporal train/test split.
- **Novelty:** Novel framing as a benchmark contribution.

---

### Verification notes
- Peer-reviewed / archival, confirmed via tools: Gilovich–Vallone–Tversky 1985; Miller–Sanjurjo 2018 (Econometrica) & 2024 (REStat); Asif–McHale 2016 (IJF); Bhattacharjee–Lemmer 2016 (IJSSC); Shah–Shah 2014; Mallawa Arachchi et al. 2024 (JSA); Goel/Davis et al. 2021 (JSA); Lamsal–Kahle 2024 (Springer CCIS); Jamil et al. 2023 (IJPAS); Raju et al. 2024 (ACM); Hassan et al. 2025 (IEEE QPAIN); Huang et al. 2025 (IEEE BDAI); Wang et al. 2024 (PLoS ONE).
- Working papers / preprints (real, retrieved, but not formally peer-reviewed): Swartz "Simulator for T20", "Expected Economy Rate", Thomson–Davis–Swartz "Contextual batting/bowling" (SFU); arXiv 2505.01849 (higher-order Markov + PI).
- **[UNVERIFIED]**: WASP as a *peer-reviewed paper* — it is a real, well-documented tool (Wikipedia, NZC, creators' blog, and a non-archival conference PDF), but the canonical description is non-archival; cite via the documented dynamic-programming formulation rather than a journal article.
- **[UNVERIFIED — future-dated]**: arXiv 2604.13861 (T20 MDP optimisation, "April 2026") — retrieved and content-rich, but its date is in the future relative to a normal timeline; treat with caution and re-verify before citing.
