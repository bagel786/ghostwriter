# Example run: the cricket momentum paper

Everything in [research-workspace/](../research-workspace/) comes from one real run of the pipeline, left unedited. The input was a single question:

> Does batter/bowler identity actually matter in T20 cricket death overs, and is momentum real or a statistical artifact?

The output, six phases later, was [The Death-Over Momentum Illusion: A Miller–Sanjurjo Correction for T20 Cricket](../research-workspace/phase-5-writer/paper.md), an 18-page preprint with an arXiv-ready LaTeX package. No human wrote any of the experiment code or the paper text. The human contribution was the question, the answers at each checkpoint, and one scoping decision along the way (restricting the data to men's IPL and T20 internationals).

This page traces what each phase actually produced, with links to the artifacts.

If you don't follow cricket: the "death overs" are the last five overs of a T20 innings, when scoring is most frantic. A "dot ball" is a delivery with no runs scored, and the folk belief is that strings of dot balls build pressure that causes wickets.

## Phase 1: Scout

Artifact: [phase-1-scout/output.md](../research-workspace/phase-1-scout/output.md)

The scout ran ten searches across Semantic Scholar, Exa, arXiv, and plain web search, and organized roughly thirty sources into clusters: per-ball win-probability models (WASP, Asif–McHale, Swartz's simulators), the pressure-index literature, applied ML for cricket, and the general sports hot-hand literature. The output ends with the two sections that drive everything downstream: an inventory of assumptions the field never tests (notably, that nearly every in-play cricket model assumes the next ball depends only on the current game state) and a list of transfer candidates, methods from adjacent fields never applied to cricket.

The decisive find was in the transfer list: Miller and Sanjurjo's 2018 proof that the standard hot-hand estimator carries a finite-sequence selection bias, the correction that overturned the famous basketball null. No cricket study had used it.

## Phase 2: Ideator

Artifact: [phase-2-ideator/output.md](../research-workspace/phase-2-ideator/output.md)

The ideator proposed ranked hypotheses grounded in the scout's gaps, each with a falsifiable statement, an experiment sketch with estimated runtime and lines of code, and a novelty assessment naming the nearest published work and the delta from it. Three were chosen as a bundle for one paper, since they share a dataset and model family:

- **H1:** game state contributes more out-of-sample skill than batter/bowler identity, asymmetrically (identity should matter more for expected runs than for wicket probability).
- **H2:** dot-ball pressure history adds skill beyond game state, which would violate the Markov assumption the field relies on.
- **H3** (the headline): the apparent death-over momentum effect is a streak-selection artifact that the Miller–Sanjurjo correction will remove.

## Phase 3: Architect, plus design review

Artifacts: [phase-3-architect/output.md](../research-workspace/phase-3-architect/output.md) and [phase-3-architect/experiment-spec.md](../research-workspace/phase-3-architect/experiment-spec.md)

The architect produced a 331-line design document: formal hypothesis statements with explicit nulls and scope limits, the data plan (Cricsheet ball-by-ball archives, filtered to overs 16 through 20, with a temporal train/validation/test split so the test season is never seen during training), a nested model ladder for attributing skill to state versus identity, leakage controls for the identity encoding, and a statistical plan built on match-clustered bootstrap intervals.

Most importantly, it pre-registered directional predictions and decision rules for every claim before any code existed. The reviewer agent then attacked the design in design-review mode, and the spec was locked after the checkpoint. That lock matters in phase 4.

## Phase 4: Experimenter

Artifacts: [phase-4-experimenter/output.md](../research-workspace/phase-4-experimenter/output.md), [code/](../research-workspace/phase-4-experimenter/code/), [results/](../research-workspace/phase-4-experimenter/results/)

The experimenter downloaded the real Cricsheet archives, parsed 1,052,624 deliveries, and filtered to 223,678 death-over deliveries across 4,402 matches (2005 to 2026). It then built the feature pipeline, trained the nested model ladder over five seeds, ran the grouped SHAP attribution, implemented the Miller–Sanjurjo correction with a state-stratified permutation null, and ran the ablations, including a random-player placebo and a six-season rolling-window evaluation. The code is ordinary Python ([main.py](../research-workspace/phase-4-experimenter/code/main.py) is the entry point, with [verify_repro.py](../research-workspace/phase-4-experimenter/code/verify_repro.py) re-running the primary result to check reproducibility), and every number in the paper traces to a CSV in [results/](../research-workspace/phase-4-experimenter/results/).

What it found, in brief:

- **The momentum headline.** The naive momentum estimate looks like a strong "cold hand" (D = −0.114), but the Miller–Sanjurjo bias for these short sequences is almost exactly that size (−0.121). Corrected, the estimate is +0.007 with p = 0.40. The apparent momentum effect is an artifact of the estimator.
- **A SHAP-versus-skill dissociation.** SHAP attributes 51 to 64 percent of the explanatory mass to batter identity, yet adding identity features makes held-out predictions slightly *worse*, in every one of six rolling test seasons. The placebo test (random player labels) confirms the attribution machinery itself is faithful; the identity signal is real in-sample and simply fails to generalize.
- **A partial Markov violation.** Dot-ball pressure history adds small but significant skill for expected runs, and nothing for wicket probability. So the folk belief that dot-ball pressure causes wickets found no support, while its effect on scoring is real but modest.

This phase is also where the pre-registration earned its keep: two of the three hypotheses came out partly contrary to prediction (identity mattering even less than predicted, and the wicket half of H2 coming up null), and because the predictions were locked in advance, those results went into the paper as findings rather than being quietly reframed.

## Phase 5: Writer

Artifacts: [phase-5-writer/paper.md](../research-workspace/phase-5-writer/paper.md), [phase-5-writer/output/](../research-workspace/phase-5-writer/output/)

The writer produced the full paper from the result files: abstract, introduction, related work, formal problem statement, methods, results with all seven figures, threats to validity, and a bibliography of the scout's verified sources. The preprint package in [output/](../research-workspace/phase-5-writer/output/) contains the standalone abstract, the Markdown version, and self-contained arXiv LaTeX source (the compiled PDF is excluded from the repo by .gitignore, but `cd arxiv-src && pdflatex main.tex` rebuilds it).

Notice the hedging in the paper. It distinguishes "this encoding of identity does not help" from "identity does not matter," and "no significant momentum" from "momentum proven absent." That language survived from the architect's scope limits through the reviewer's overclaiming checks.

## Phase 6: Review

The reviewer checked the draft's numbers against the result CSVs and pushed revisions until no must-fix items remained; the final text reflects that loop. One honest caveat about this particular run: the review artifacts themselves were not preserved in the workspace, so unlike the other phases you cannot read the review thread here. The current skill version saves them to `research-workspace/phase-6-review/`.

## What this run suggests

The pipeline's value was less in any single phase than in the constraints between them: the scout finding a genuinely unused method, the novelty check forcing explicit deltas from prior work, the locked pre-registration keeping inconvenient results in the paper, and the reviewer keeping the claims matched to the evidence. The result is a paper whose every number can be traced to a file in this repo, which is the standard any auto-generated research should be held to.
