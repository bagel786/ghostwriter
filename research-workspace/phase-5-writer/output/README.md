# Preprint Package — T20 Death-Over Per-Ball Modeling & Miller–Sanjurjo Momentum

Submission-ready arXiv preprint package.

## Contents

- `paper.pdf` — compiled preprint (18 pages).
- `abstract.txt` — standalone abstract for the submission form.
- `paper.md` — full paper in Markdown with embedded figures.
- `arxiv-src/` — arXiv-ready LaTeX source. Self-contained; includes `main.bbl`
  so no BibTeX run is required on arXiv.
  - `main.tex`, `sections/*.tex`, `references.bib`, `main.bbl`, `figures/*.pdf`.

## Title

The Death-Over Momentum Illusion: A Miller–Sanjurjo Correction for T20 Cricket.

## Compiling from source

```bash
cd arxiv-src
pdflatex main.tex
bibtex main          # optional; main.bbl is already provided
pdflatex main.tex
pdflatex main.tex
```

## Data and figures

All numbers come from the Phase-4 experiment on 223,678 Cricsheet death-over
deliveries (men's IPL + T20I, 2005–2026, held-out 2026 test season). The seven
figures (including the identity placebo and six-season rolling-window robustness
studies) are reproduced from `phase-4-experimenter/results/figures/`. Result
tables, including `ablation_identity_placebo.csv` and `ablation_rolling_window.csv`,
are in `phase-4-experimenter/results/*.csv`.

## Suggested arXiv category

`stat.AP` (primary), with `cs.LG` as a cross-list.
