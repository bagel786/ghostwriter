# How Ghostwriter works

Ghostwriter is a set of Markdown instruction files that Claude Code executes. There is one orchestrator ([SKILL.md](../.claude/skills/research-pipeline/SKILL.md)) and six agents, each defined by a single file in [agents/](../.claude/skills/research-pipeline/agents/). The orchestrator spawns each agent as a subagent, collects its output from disk, presents it to you at a checkpoint, and passes a structured context packet to the next phase.

This page explains the design choices. For a concrete trace of a real run, see [example-run.md](example-run.md).

## Why subagents instead of one long conversation

A full research project produces far more text than fits in one context window: dozens of papers worth of literature notes, an experiment spec, thousands of lines of code, result tables, and an 18-page draft. Running each phase as a fresh subagent means each one starts with a clean window containing only its instruction file and the distilled outputs of prior phases. The agents communicate through files in `research-workspace/`, so every intermediate product is inspectable and survives the session.

A second benefit is role separation. The reviewer agent works adversarially precisely because it arrives with no memory of writing the design or the paper. It reads the artifacts cold, the same way a human reviewer would.

## The six agents

**Scout** ([scout.md](../.claude/skills/research-pipeline/agents/scout.md)) maps the field. It produces a search log, a literature map, a synthesis, and three things the later phases feed on: a gap analysis, an inventory of assumptions the field shares but never tests, and a list of methods from adjacent fields that have never been applied to this one. Those last two sections exist because they are where the most original hypotheses come from. The cricket paper's headline contribution (importing the Miller–Sanjurjo correction) came straight out of the scout's transfer-candidates list.

**Ideator** ([ideator.md](../.claude/skills/research-pipeline/agents/ideator.md)) turns the scout's gaps into 3 to 5 specific, falsifiable hypotheses, each with an experiment sketch. The distinctive step is mandatory novelty verification: for every hypothesis, the ideator runs targeted searches, lists the nearest published papers, and states the exact delta from each. You see that evidence at the checkpoint before committing. If the novelty check kills every candidate, the orchestrator loops back to the scout with a focus on adjacent fields instead of pushing a near-duplicate through.

**Architect** ([architect.md](../.claude/skills/research-pipeline/agents/architect.md)) turns the chosen hypothesis into an experiment spec: variables, baselines, metrics, datasets, controls, and a statistical analysis plan. Crucially, it writes a pre-registration block before any code exists: directional predictions and decision rules for each claim. Once you approve the design, that block is locked. Later deviations are allowed but must be logged and disclosed in the paper.

**Experimenter** ([experimenter.md](../.claude/skills/research-pipeline/agents/experimenter.md)) implements and runs everything. Its instructions forbid placeholder functions and mock data; everything must execute. It produces the code, pinned dependencies, an environment snapshot, result CSVs, figures, a deviation log, and a `verify_repro.py` script that re-runs the primary result from scratch and checks it matches. It also runs negative and positive controls, and is required to stop and debug if a control fails, because results produced past a failed control are not results.

**Writer** ([writer.md](../.claude/skills/research-pipeline/agents/writer.md)) writes the paper from the actual result files, never from memory of what the results "should" be. Alongside the paper it produces a claims audit: a table mapping every quantitative claim in the text to the specific file and number that supports it. It also assembles the preprint package (LaTeX source, compiled PDF when LaTeX is available, standalone abstract).

**Reviewer** ([reviewer.md](../.claude/skills/research-pipeline/agents/reviewer.md)) runs in two modes. In design-review mode it attacks the experiment spec before any code runs: does the design actually test the hypothesis, what confounds the headline comparison, is the statistical plan sound. In paper-review mode it checks the finished paper's numbers against the raw result files, attacks the statistics, hunts for overclaiming, and verifies related-work coverage. Findings are tiered (must-fix, should-fix, consider) and the pipeline does not finish while must-fix items remain.

## The checkpoints

The orchestrator stops and waits for explicit approval after the scout, after hypothesis selection, after the design review, after the experiments, and after the final review. Two of these matter most:

- **Hypothesis selection.** You pick the hypothesis, with the nearest-neighbor papers in front of you. The pipeline never decides on its own what the paper will claim.
- **Design approval.** This is the highest-leverage moment in the whole run. A flawed design produces worthless results no matter how good the later phases are, which is also why the reviewer attacks the design at this point, when fixing it costs nothing.

## What keeps it honest

Several mechanisms exist specifically to prevent the failure modes you would expect from an agent writing papers:

- **Pre-registration before code.** Predictions and decision rules are recorded and locked at design time, so a surprising result can be distinguished from a fished-for one. A clean null on a pre-registered prediction is treated as publishable.
- **Controls as gates.** A failed negative or positive control halts the experiment phase rather than being papered over.
- **A deviation log.** Any departure from the locked spec is recorded and must be disclosed in the paper.
- **Claims audit plus adversarial number-checking.** The writer maps every claim to its evidence file, and the reviewer independently re-checks the paper's numbers against the raw CSVs.
- **An explicit fabrication ban.** The orchestrator's failure-handling rules end with: never fabricate results or citations; if something can't be found or run, say so.

None of this makes the output trustworthy without you. It makes the output *checkable*, which is the point: every claim traces back to a file you can open.

## Context passing

Between phases the orchestrator assembles a fixed-format packet (intake constraints, scout output, chosen hypothesis with its novelty evidence, design and pre-registration, results and deviations) so each agent knows exactly what it has been given and what stage the project is at. The format is specified at the bottom of [SKILL.md](../.claude/skills/research-pipeline/SKILL.md).

## Failure handling

The orchestrator has explicit rules for the common breakdowns: re-spawn a misbehaving agent with a tighter prompt rather than retrying the same one, simplify the experiment if the code won't run after two attempts, loop scout and ideator if novelty checks fail, and surface writer-reviewer deadlocks to you after three revision rounds instead of looping forever.

## Research tracks

At intake, the orchestrator classifies the idea into one of seven tracks, which shapes what the architect designs and what the experimenter builds: empirical (the default), theory, simulation, benchmark or dataset, replication, methods transfer, and meta-science. Methods transfer and replication are underused in practice and often yield the most original papers, so the orchestrator suggests them when an idea hints that way. The cricket paper is a methods-transfer result wrapped in an empirical study.
