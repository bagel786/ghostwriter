# Ghostwriter

An autonomous end-to-end research agent that takes a raw idea and produces a publication-quality paper with real experiments — not a writeup, but actual research.

## What it does

Ghostwriter is a Claude Code skill that runs a 7-phase research pipeline, spawning a focused subagent for each phase and presenting checkpoints so you stay in control. Each phase builds on the last:

```
[Your Idea]
     │
     ▼
Phase 0: INTAKE          → classify research track, confirm constraints
     ▼
Phase 1: SCOUT           → maps the field, finds gaps and transferable methods
     │  [CHECKPOINT]
     ▼
Phase 2: IDEATOR         → generates ranked, novelty-verified hypotheses
     │  [CHECKPOINT]
     ▼
Phase 3: ARCHITECT       → designs the experiment, pre-registers predictions
     │  [DESIGN REVIEW CHECKPOINT]
     ▼
Phase 4: EXPERIMENTER    → writes and runs code, collects real results
     │  [CHECKPOINT]
     ▼
Phase 5: WRITER          → writes the paper from the actual results
     ▼
Phase 6: REVIEWER        → adversarial peer review + revision until submission-ready
     │  [FINAL CHECKPOINT]
     ▼
[Submission-ready paper]
```

## Example output

The cricket paper ([`research-workspace/phase-5-writer/paper.md`](research-workspace/phase-5-writer/paper.md)) was produced end-to-end by this pipeline from a single idea:

> *"Does batter/bowler identity actually matter in T20 death overs, and is momentum real or a statistical artifact?"*

The pipeline scouted the literature, formed falsifiable hypotheses (including importing the Miller–Sanjurjo streak-selection correction — new to cricket), designed and ran experiments on 223,678 real Cricsheet deliveries, and produced a calibrated per-ball model with SHAP attribution, a Markov test, and a full paper. No human wrote any of the experiment code or the paper text.

## Installation

Ghostwriter is distributed as a Claude Code skill (`.skill` file).

### Prerequisites

- [Claude Code](https://claude.ai/code) installed and authenticated
- MCP servers (optional but recommended for richer literature search):
  - `paper-search`, `semantic-scholar`, `exa` — for Phase 1 (Scout)

### Install the skill

1. Download `research-pipeline.skill` from this repo.
2. In your terminal, run:

   ```bash
   claude skill install research-pipeline.skill
   ```

3. Claude Code will unpack it into your project's `.claude/skills/research-pipeline/` directory.

### Use it

Start a new conversation in Claude Code and describe your research idea. The skill triggers on phrases like:

- *"I have a research idea…"*
- *"Do research on X"*
- *"Run experiments on X"*
- *"Test the hypothesis that…"*
- *"Write a paper with real experiments"*

Claude will automatically detect the intent, invoke the pipeline, and walk you through each phase with a checkpoint before moving on.

You can also invoke it explicitly:

```
/research-pipeline
```

## Research tracks

The pipeline supports multiple tracks — pick the one that fits or let the orchestrator suggest:

| Track | Best for |
|-------|----------|
| **Empirical** | Hypothesis tested on real data with models/code |
| **Methods-transfer** | A method from field A applied to field B |
| **Replication** | Reproducing + stress-testing a published result |
| **Simulation** | ABM, Monte Carlo, queueing, epidemic models |
| **Benchmark/Dataset** | New dataset + baseline suite |
| **Theory** | Theorems, proofs, bounds |

## Repository layout

```
research-pipeline.skill          # distributable skill package
.claude/skills/research-pipeline/
  SKILL.md                       # orchestrator instructions
  agents/
    scout.md                     # Phase 1 subagent
    ideator.md                   # Phase 2 subagent
    architect.md                 # Phase 3 subagent
    experimenter.md              # Phase 4 subagent
    writer.md                    # Phase 5 subagent
    reviewer.md                  # Phase 6 subagent
  references/                    # writing guides, figure templates, LaTeX templates
research-workspace/              # output from the cricket paper run
```
