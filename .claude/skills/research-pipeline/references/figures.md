# Figures and Visualizations

## General Rules

- Every figure needs a caption that stands alone — a reader who only sees the figure and
  caption should understand what it shows and what the takeaway is
- Use vector formats (PDF, SVG) for diagrams and plots — not PNG/JPEG
- Keep a consistent visual style across all figures: same font family, same color palette,
  same line weights
- Number figures in order of appearance: Figure 1, Figure 2, etc.
- Reference every figure in the text before it appears: "Figure 2 shows..."

---

## Matplotlib Style Defaults

Use this style block at the top of every Python plotting script to ensure consistent,
publication-quality figures:

```python
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np

# Publication style
plt.rcParams.update({
    'font.family': 'serif',
    'font.serif': ['Computer Modern Roman', 'Times New Roman'],
    'font.size': 10,
    'axes.titlesize': 11,
    'axes.labelsize': 10,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'legend.fontsize': 9,
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.05,
    'axes.spines.top': False,
    'axes.spines.right': False,
    'axes.grid': True,
    'grid.alpha': 0.3,
    'grid.linewidth': 0.5,
    'lines.linewidth': 1.5,
    'lines.markersize': 5,
})

# Colorblind-friendly palette (from ColorBrewer)
COLORS = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
          '#8c564b', '#e377c2', '#7f7f7f']

# Single-column figure: 3.5 inches wide
# Double-column figure: 7 inches wide
FIG_SINGLE = (3.5, 2.5)
FIG_DOUBLE = (7.0, 2.8)
FIG_SQUARE = (3.5, 3.5)

def save_fig(name, fig=None):
    """Save figure as both PDF (for LaTeX) and PNG (for preview)."""
    if fig is None:
        fig = plt.gcf()
    fig.savefig(f'figures/{name}.pdf', format='pdf')
    fig.savefig(f'figures/{name}.png', format='png')
    print(f"Saved figures/{name}.pdf and figures/{name}.png")
```

### Bar chart template
```python
fig, ax = plt.subplots(figsize=FIG_SINGLE)
methods = ['Baseline', 'Ours', 'Method A', 'Method B']
values = [82.3, 87.1, 84.5, 83.9]
errors = [0.4, 0.3, 0.5, 0.6]

bars = ax.bar(methods, values, yerr=errors, color=COLORS[:len(methods)],
              capsize=3, width=0.6)
ax.set_ylabel('Accuracy (%)')
ax.set_ylim(78, 90)
ax.set_title('Comparison on Benchmark Dataset')
# Highlight your method
bars[1].set_edgecolor('black')
bars[1].set_linewidth(1.5)
save_fig('fig-comparison')
```

### Line plot template (training curves, ablations)
```python
fig, ax = plt.subplots(figsize=FIG_SINGLE)
epochs = np.arange(1, 51)
for i, (label, values) in enumerate(results.items()):
    ax.plot(epochs, values, color=COLORS[i], label=label, linewidth=1.5)
ax.set_xlabel('Epoch')
ax.set_ylabel('Validation Loss')
ax.legend(frameon=False)
save_fig('fig-training-curves')
```

### Scatter plot template
```python
fig, ax = plt.subplots(figsize=FIG_SQUARE)
ax.scatter(x_vals, y_vals, c=COLORS[0], alpha=0.6, s=20, edgecolors='none')
ax.set_xlabel('Memory Usage (GB)')
ax.set_ylabel('Accuracy (%)')
# Add regression line if needed
m, b = np.polyfit(x_vals, y_vals, 1)
ax.plot(x_vals, m * x_vals + b, color=COLORS[1], linewidth=1)
save_fig('fig-scatter')
```

---

## TikZ Templates (for LaTeX)

### System architecture / pipeline diagram
```latex
\usepackage{tikz}
\usetikzlibrary{shapes.geometric, arrows.meta, positioning, fit, backgrounds}

\tikzset{
  block/.style = {rectangle, draw, fill=blue!10, text width=5em,
                  text centered, rounded corners, minimum height=2.5em},
  arrow/.style = {-Stealth, thick},
  dashed_arrow/.style = {-Stealth, dashed, thick, gray},
}

\begin{figure}[t]
\centering
\begin{tikzpicture}[node distance=1.5cm and 2cm]
  \node[block] (input) {Input\\Data};
  \node[block, right=of input] (process) {Proposed\\Module};
  \node[block, right=of process] (output) {Output};

  \draw[arrow] (input) -- (process);
  \draw[arrow] (process) -- (output);

  % Optional: bounding box with label
  \begin{scope}[on background layer]
    \node[fill=gray!10, rounded corners, fit=(input)(output), inner sep=10pt,
          label=above:{\small System Overview}] {};
  \end{scope}
\end{tikzpicture}
\caption{Overview of our proposed system. [Describe what each block does.]}
\label{fig:system}
\end{figure}
```

### Flowchart / decision diagram
```latex
\tikzset{
  decision/.style = {diamond, draw, fill=orange!15, text width=5em,
                     text centered, inner sep=0pt, aspect=2},
  startstop/.style = {rectangle, draw, fill=green!15, rounded corners,
                      text centered, minimum height=2em},
  process/.style = {rectangle, draw, fill=blue!10, text centered,
                    minimum height=2em},
}
```

### Confusion matrix / heatmap in TikZ
For heatmaps and matrices, prefer Python/seaborn (easier) and include as PDF:
```python
import seaborn as sns
fig, ax = plt.subplots(figsize=FIG_SQUARE)
sns.heatmap(matrix, annot=True, fmt='.1f', cmap='Blues',
            xticklabels=classes, yticklabels=classes, ax=ax,
            linewidths=0.5, cbar_kws={'shrink': 0.8})
ax.set_xlabel('Predicted')
ax.set_ylabel('True')
save_fig('fig-confusion-matrix')
```

---

## Model Architecture Diagrams

For neural network architecture figures, use one of:

**Option 1: PlotNeuralNet** (for deep learning layer diagrams)
```bash
pip install plotneuralnet
```
Good for CNN/transformer layer visualizations. See https://github.com/HarisIqbal88/PlotNeuralNet

**Option 2: Graphviz** (for computational graphs, dependency trees)
```python
from graphviz import Digraph
dot = Digraph(comment='Model Architecture')
dot.attr(rankdir='LR', size='6,3')
dot.node('input', 'Input\n[B×L×D]', shape='box', style='filled', fillcolor='lightblue')
dot.node('encoder', 'Transformer\nEncoder', shape='box', style='filled', fillcolor='lightyellow')
dot.node('output', 'Output\n[B×C]', shape='box', style='filled', fillcolor='lightgreen')
dot.edge('input', 'encoder')
dot.edge('encoder', 'output')
dot.render('figures/fig-architecture', format='pdf', cleanup=True)
```

**Option 3: Manual TikZ** — best quality, most control, most work
Use the TikZ templates above and build from scratch.

---

## UI / Interface Mockups

For papers with a system or interface component (HCI, software engineering):

```python
# Simple wireframe mockup using matplotlib patches
import matplotlib.patches as patches

fig, ax = plt.subplots(figsize=(5, 4))
ax.set_xlim(0, 10)
ax.set_ylim(0, 8)
ax.set_aspect('equal')
ax.axis('off')

# Window frame
ax.add_patch(patches.FancyBboxPatch((0.2, 0.2), 9.6, 7.6,
    boxstyle='round,pad=0.1', facecolor='white', edgecolor='#333', linewidth=1.5))

# Title bar
ax.add_patch(patches.Rectangle((0.2, 7.0), 9.6, 0.8, facecolor='#4A90D9'))
ax.text(5, 7.4, 'System Name', ha='center', va='center', color='white', fontsize=11)

# Content areas — add boxes, text labels, etc.
ax.add_patch(patches.FancyBboxPatch((0.5, 4.5), 4, 2.2,
    boxstyle='round,pad=0.1', facecolor='#f5f5f5', edgecolor='#ccc'))
ax.text(2.5, 5.6, '[Panel A]', ha='center', va='center', color='#666', fontsize=9)

save_fig('fig-interface-mockup')
```

---

## Caption Writing

Good captions are self-contained and state the takeaway.

**Bad:** "Figure 3: Results."
**Bad:** "Figure 3: Comparison of methods on Dataset X."
**Good:** "Figure 3: SparseAgg matches full-neighborhood GNN accuracy (within 0.8%) while
          using 3.2× less memory across all three dataset sizes."

For diagrams:
**Bad:** "Figure 1: Our system architecture."
**Good:** "Figure 1: Overview of our system. User queries pass through the retrieval module
          (left), which selects relevant context before passing to the generator (right).
          The feedback loop (dashed) enables online adaptation."
