# research-workspace: an unedited pipeline run

This directory is the raw output of one complete Ghostwriter run, the one that produced the cricket momentum paper. Nothing here has been cleaned up after the fact; it is what the pipeline left behind, minus a few things excluded by .gitignore (the downloaded Cricsheet data, the Python venv, and compiled PDFs).

For a guided tour, read [docs/example-run.md](../docs/example-run.md). The short map:

| Directory | What's in it |
|---|---|
| [phase-1-scout/](phase-1-scout/) | Literature map, gap analysis, untested assumptions, transfer candidates |
| [phase-2-ideator/](phase-2-ideator/) | Candidate hypotheses with novelty checks against the literature |
| [phase-3-architect/](phase-3-architect/) | Experiment design and the locked, pre-registered spec |
| [phase-4-experimenter/](phase-4-experimenter/) | All analysis code, result CSVs, run logs, and figures |
| [phase-5-writer/](phase-5-writer/) | The paper ([paper.md](phase-5-writer/paper.md)), LaTeX source, and the arXiv package |

To reproduce the experiments, see [phase-4-experimenter/code/](phase-4-experimenter/code/). The entry point is `main.py`; `verify_repro.py` re-runs the primary result and checks it matches the saved numbers. Dependencies are numpy, pandas, scikit-learn, lightgbm, shap, and matplotlib. The raw data is two public Cricsheet bundles, `ipl_male_csv2.zip` and `t20s_male_csv2.zip` from [cricsheet.org](https://cricsheet.org/downloads/); extract them into `phase-4-experimenter/data/raw/ipl/` and `phase-4-experimenter/data/raw/t20s/` so the loader finds the per-match CSVs.

To rebuild the paper PDF:

```bash
cd phase-5-writer/output/arxiv-src
pdflatex main.tex && pdflatex main.tex
```
