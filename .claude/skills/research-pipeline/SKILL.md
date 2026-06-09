---
name: research-pipeline
description: >
  Run a full autonomous research pipeline from a single idea to a published-quality paper
  with real experiments and results. Use this skill whenever the user has a research idea,
  hypothesis, or question they want to turn into an actual paper — not just a writeup, but
  real research: literature review, hypothesis formation, experiment design, running code,
  analyzing results, building models, and writing it all up. Triggers on: "do research on",
  "I have a research idea", "write a paper with real experiments", "run experiments on",
  "build a model for", "investigate whether", "test the hypothesis that", "I want to publish
  a paper on", "replicate the paper", "build a benchmark for", "prove that", "can you
  actually research X", or any request where the user wants Claude to conduct research
  rather than just write about it. Supports multiple research tracks: empirical/computational
  studies, theory and proofs, simulation studies, benchmark/dataset contributions,
  replication studies, methods-transfer papers, and meta-science. Topics: ML, statistics,
  CS theory, systems, algorithms, data science, simulation, computational social science,
  applied math, bibliometrics, and any domain testable with code and public data.
  Always use this over the basic research-paper skill when the user wants actual
  experiments run, not just a literature-based writeup.
compatibility:
  tools:
    - Read
    - Write
    - Edit
    - Bash
    - Task
    - WebSearch
    - WebFetch
    - mcp__exa__*
    - mcp__papersflow__*
    - mcp__paper-search__*
    - mcp__semantic-scholar__*
    - mcp__sequential-thinking__*
    - mcp__filesystem__*
---

# Research Pipeline — Orchestrator

You run a 7-phase research pipeline. Each phase is handled by a focused subagent.
You are the orchestrator: you spawn agents, receive their outputs, present them to
the user, get approval, then pass context forward to the next agent.

**Never skip a checkpoint.** The user approved checkpointing — present results and
wait for explicit go-ahead before moving to the next phase. If the user says "looks
good" or "continue", proceed. If they push back, revise with the current agent before
moving forward.

---

## Pipeline Overview

```
[Your Idea]
     │
     ▼
Phase 0: INTAKE          → classify research track, constraints, compute budget
     │  (orchestrator — no subagent)
     ▼
Phase 1: SCOUT           → maps the field, finds real gaps, untested assumptions,
     │  [CHECKPOINT]        and transferable methods from adjacent fields
     ▼
Phase 2: IDEATOR         → generates ranked hypotheses, novelty-verifies each
     │  [CHECKPOINT]        against the literature, you pick one
     ▼
Phase 3: ARCHITECT       → designs the experiment, pre-registers predictions
     │
     ├─ DESIGN REVIEW    → reviewer agent attacks the design BEFORE any code runs
     │  [CHECKPOINT]
     ▼
Phase 4: EXPERIMENTER    → writes and runs the code, collects real results,
     │  [CHECKPOINT]        logs deviations from the pre-registered spec
     ▼
Phase 5: WRITER          → writes the paper from the actual results
     │
     ▼
Phase 6: REVIEWER        → adversarial peer review of the paper
     │                      → writer revises until must-fixes are resolved
     │  [FINAL CHECKPOINT]
     ▼
[Submission-ready paper]
```

---

## Phase 0: Intake (you do this — no subagent)

Before spawning anything, classify the research and confirm constraints with the user.

**1. Pick the research track.** This shapes every downstream phase:

| Track | What it produces | Experimenter's job |
|-------|------------------|--------------------|
| **Empirical** (default) | Hypothesis tested with models/code on real data | Implement methods, run on data |
| **Theory** | Theorem, bound, counterexample, or characterization | Formalize, prove, verify numerically |
| **Simulation** | Findings from a simulated system (ABM, Monte Carlo, queueing, epidemic) | Build simulator, validate against known analytic cases, then explore |
| **Benchmark/Dataset** | New dataset or benchmark + baseline suite | Construct data, document it (datasheet), run baseline ladder |
| **Replication** | Reproduction + stress-test/extension of a published result | Reimplement target paper, reproduce, then extend |
| **Methods-transfer** | A method/correction from field A applied to field B, changing conclusions | Implement imported method, compare against field-B status quo |
| **Meta-science** | Findings about the literature itself (bibliometrics, claim audits) | Mine corpora (Semantic Scholar API, OpenAlex), analyze |

If the user's idea fits more than one, ask. Most ideas are Empirical; Methods-transfer
and Replication are underused and often yield the most original papers — suggest them
when the idea hints that way.

**2. Confirm constraints:** compute budget (laptop/CPU vs GPU), wall-clock tolerance for
experiments, target venue, and any data the user already has access to.

**3. Create the workspace:**

```bash
mkdir -p research-workspace/{phase-1-scout,phase-2-ideator,phase-3-architect,phase-4-experimenter,phase-5-writer,phase-6-review}
```

Record the track + constraints in `research-workspace/intake.md` — every subsequent
agent prompt includes them.

---

## How to Spawn Subagents

Use the `Task` tool to spawn each agent as a subagent. Pass the full context packet
from prior phases so the agent has everything it needs. Each agent saves its output
to `research-workspace/phase-N-<name>/output.md` (and any code/data files alongside it).
Always include the track and constraints from `intake.md` in every agent prompt.

---

## Phase 1: Scout

**Spawn the scout agent.** Pass: the user's raw idea + track + constraints.

Task prompt:
```
Read agents/scout.md for instructions.
User's research idea: [IDEA]
Research track: [track from intake]
Constraints: [from intake.md]
Save all output to research-workspace/phase-1-scout/output.md
```

**What you get back:** A literature map with real sources, a synthesis, a gap analysis,
an inventory of untested assumptions the field shares, and a list of methods from
adjacent fields that haven't been applied here (transfer candidates).

**Checkpoint:** Present the gap analysis, untested assumptions, and transfer candidates.
Ask:
- "Does this match the gap you were thinking about?"
- "Any key papers we missed?"
- "Any of these gaps, assumptions, or transfer candidates more interesting to you?"

Get explicit approval before Phase 2.

---

## Phase 2: Ideator

**Spawn the ideator agent.** Pass: scout output + user's feedback from checkpoint.

Task prompt:
```
Read agents/ideator.md for instructions.
Scout output: [paste research-workspace/phase-1-scout/output.md]
Research track: [track] / Constraints: [from intake.md]
User feedback: [any refinements from checkpoint]
Save output to research-workspace/phase-2-ideator/output.md
```

**What you get back:** 3–5 specific, testable hypotheses ranked by novelty and
feasibility — each one *novelty-verified*: the ideator ran targeted searches for each
hypothesis and lists its nearest-neighbor papers with the explicit delta from each.

**Checkpoint:** Present the hypotheses as a numbered list, **including each one's
nearest-neighbor papers and delta** — the user should see exactly how close existing
work is before committing. Ask the user to pick one. Don't proceed until they've chosen.

If the novelty audit killed every candidate (all too close to existing work), say so
and loop: re-spawn the scout focused on adjacent fields and untested assumptions,
then re-ideate. Don't push a weak hypothesis through.

---

## Phase 3: Architect + Design Review

**Spawn the architect agent.** Pass: chosen hypothesis + scout output.

Task prompt:
```
Read agents/architect.md for instructions.
Chosen hypothesis: [hypothesis text from user selection]
Research track: [track] / Constraints: [from intake.md]
Literature context: [research-workspace/phase-1-scout/output.md]
Nearest-neighbor papers for this hypothesis: [from ideator output]
Save output to research-workspace/phase-3-architect/output.md
Save experiment spec to research-workspace/phase-3-architect/experiment-spec.md
```

**What you get back:** A full experiment design — methodology, baselines, metrics,
datasets, controls, a statistical analysis plan, and a **pre-registration block**
(directional predictions + decision rules recorded before any code runs).

**Then immediately spawn the reviewer agent in design-review mode** — this is cheap
and catches flawed designs before compute is spent:

```
Read agents/reviewer.md for instructions. Mode: DESIGN REVIEW.
Experiment spec: [research-workspace/phase-3-architect/experiment-spec.md]
Design doc: [research-workspace/phase-3-architect/output.md]
Hypothesis + nearest neighbors: [from ideator]
Save review to research-workspace/phase-6-review/design-review.md
```

If the reviewer returns MUST-FIX items, re-spawn the architect with them and update
the spec before showing the user.

**Checkpoint:** Present the experiment design + the design review verdict. Ask:
- "Does this setup make sense for testing the hypothesis?"
- "Any baselines we should add or remove?"
- "Any constraints on runtime or compute?"

This is the most important checkpoint — a flawed design produces useless results.
Once approved, the spec's pre-registration block is **locked**: later deviations are
allowed but must be logged and disclosed in the paper.

---

## Phase 4: Experimenter

**Spawn the experimenter agent.** Pass: architect output + experiment spec.

Task prompt:
```
Read agents/experimenter.md for instructions.
Experiment spec: [research-workspace/phase-3-architect/experiment-spec.md]
Architecture design: [research-workspace/phase-3-architect/output.md]
Research track: [track] / Constraints: [from intake.md]
Save all code to research-workspace/phase-4-experimenter/code/
Save results to research-workspace/phase-4-experimenter/results/
Save analysis to research-workspace/phase-4-experimenter/output.md
```

**What you get back:** Working code, result files (CSVs, model outputs, stats),
figures, a pinned `requirements.txt`, a deviation log (any departures from the
pre-registered spec), control-experiment results, and a results analysis written
in the agent's own words.

**Checkpoint:** Present the key results + figures + control outcomes + any deviations.
Ask:
- "Do these results look meaningful to you?"
- "Anything you want to dig into further (more ablations, edge cases, etc.)?"
- "Happy with these as the paper's results?"

If results are weak or inconclusive, offer to re-run the experimenter with adjusted
parameters before moving to writing. Remember: a clean, well-controlled null result
on a pre-registered prediction is publishable — a fished-for positive is not.

---

## Phase 5: Writer

**Spawn the writer agent.** Pass: everything — scout, ideator, architect, experimenter outputs.

Task prompt:
```
Read agents/writer.md for instructions.
Literature: [research-workspace/phase-1-scout/output.md]
Hypothesis chosen + nearest neighbors: [from ideator]
Experiment design + pre-registration: [research-workspace/phase-3-architect/output.md]
Results and analysis: [research-workspace/phase-4-experimenter/output.md]
Deviation log: [research-workspace/phase-4-experimenter/results/deviations.md if present]
Figures directory: research-workspace/phase-4-experimenter/results/figures/
Target venue: [venue from user, or "arXiv preprint" if unspecified]
Save paper to research-workspace/phase-5-writer/
```

**What you get back:** A complete paper — all sections, LaTeX source, compiled PDF
(if LaTeX is available), a claims–evidence audit table, and a preprint package.

---

## Phase 6: Review & Revise

**Spawn the reviewer agent in paper-review mode:**

```
Read agents/reviewer.md for instructions. Mode: PAPER REVIEW.
Paper: [research-workspace/phase-5-writer/paper.md]
Claims audit: [research-workspace/phase-5-writer/claims-audit.md]
Results directory: research-workspace/phase-4-experimenter/results/
Pre-registered spec: [research-workspace/phase-3-architect/experiment-spec.md]
Scout literature: [research-workspace/phase-1-scout/output.md]
Save review to research-workspace/phase-6-review/paper-review.md
```

The reviewer checks numbers in the paper against the actual result files, attacks
the statistics, hunts for overclaiming, and verifies the related-work coverage.

**Revision loop:** If the review contains MUST-FIX items, re-spawn the writer with
the review and have it revise + write a point-by-point response
(`phase-6-review/response.md`). Repeat until no MUST-FIX items remain (max 3 rounds —
if still failing, surface the disagreement to the user).

**Final checkpoint:** Present the paper, the review verdict, and the response letter.
Ask if they want any revisions before considering it done.

---

## Context Packet Format

When passing context between agents, always structure it like this so agents know
exactly what they're working with:

```
=== CONTEXT FROM PRIOR PHASES ===

[INTAKE — TRACK + CONSTRAINTS]
<contents of intake.md>

[PHASE 1 - SCOUT OUTPUT]
<contents of phase-1-scout/output.md>

[PHASE 2 - CHOSEN HYPOTHESIS + NEAREST NEIGHBORS]
<hypothesis text + its novelty-verification section>

[PHASE 3 - EXPERIMENT DESIGN + PRE-REGISTRATION]
<contents of phase-3-architect/output.md>

[PHASE 4 - RESULTS + DEVIATIONS]
<contents of phase-4-experimenter/output.md>

=== END CONTEXT ===
```

---

## Failure Handling

- If a subagent fails or produces garbage output, re-read its agent .md file and
  re-spawn with a more constrained prompt — don't just retry the same prompt.
- If the experimenter can't get code working after 2 attempts, tell the user and
  offer to simplify the experiment design.
- If literature search returns nothing useful, tell the user and ask them to clarify
  the topic before proceeding.
- If the novelty audit kills all hypotheses, loop scout → ideator with an
  adjacent-field / untested-assumptions focus rather than proposing near-duplicates.
- If a control experiment fails (negative control shows an effect, or positive
  control doesn't), the experimenter must stop and debug — results produced past a
  failed control are not results.
- If reviewer and writer deadlock after 3 revision rounds, present both positions
  to the user and let them adjudicate.
- Never fabricate results or citations. If something can't be found or run, say so.

---

## Reference Files

- `agents/scout.md` — literature search, gap analysis, assumptions inventory,
  adjacent-field methods scan
- `agents/ideator.md` — hypothesis generation + mandatory novelty verification
- `agents/architect.md` — experiment design + pre-registration + controls
- `agents/experimenter.md` — code writing, execution, controls, reproducibility
- `agents/writer.md` — paper writing + claims–evidence audit
- `agents/reviewer.md` — adversarial design review and paper review
- `references/` — writing guide, figure standards, citation styles, LaTeX templates
  (same as research-paper skill — read as needed during writing phase)
