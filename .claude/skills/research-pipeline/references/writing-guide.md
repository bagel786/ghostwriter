# Academic Writing Guide

## Section-by-Section Advice

### Abstract

The abstract is a self-contained summary. Readers decide whether to read the paper based
on the abstract alone. It must answer four questions:

1. **What problem does this paper address?** (1-2 sentences of context)
2. **What is your approach?** (1-2 sentences — high level, no jargon if possible)
3. **What did you find?** (the actual result, with numbers if you have them)
4. **Why does it matter?** (1 sentence — not "this opens exciting new directions" — something specific)

**Hard rules:**
- Never end with vague significance ("This work paves the way for future research")
- Include at least one concrete result (accuracy, speedup, effect size, etc.) if the paper has experiments
- No citations in the abstract
- 150–250 words for most conferences; check venue guidelines

**Bad abstract:**
> In this paper, we propose a novel method for improving the efficiency of graph neural
> networks. We evaluate our approach on several benchmark datasets. Our results demonstrate
> that our method achieves competitive performance. This work has implications for the
> broader field of machine learning.

**Good abstract:**
> Training graph neural networks (GNNs) on large graphs is expensive because message
> passing requires materializing all neighbor embeddings at each layer. We propose SparseAgg,
> a method that replaces full neighborhood aggregation with a learned sparse attention mask,
> reducing memory usage by 3.2× with less than 1% accuracy loss on OGB-Papers100M.
> SparseAgg is architecture-agnostic and adds fewer than 200 lines of code to any existing
> GNN implementation. Code is available at [URL].

---

### Introduction

Structure:
1. Open with the problem — not "In recent years, X has become increasingly important"
2. Identify the specific gap or challenge
3. State what you do ("In this paper, we...")
4. State what you find (brief — the abstract already did this, but repeat the headline)
5. List contributions explicitly:
   > We make the following contributions:
   > - We propose [X], a method that [does Y]
   > - We prove [Z]
   > - We demonstrate [W] on [benchmarks], achieving [results]
6. (Optional) Roadmap: "Section 2 reviews related work..."

Reviewers read contributions lists carefully. Make them specific and falsifiable.
"We propose a novel approach" is not a contribution. "We propose SparseAgg, which reduces
memory by 3.2× on OGB-Papers100M" is.

---

### Related Work

**Goal:** Show you know the field and explain precisely where your work fits.

**Structure by theme, not chronology.** Bad related work:
> Smith et al. [1] proposed X. Jones et al. [2] improved X. Lee et al. [3] extended X
> to Y. Wang et al. [4] applied X to Z.

Good related work groups papers by approach or problem:
> **Sparse attention in transformers.** Several works have explored...
> **GNN scalability.** The challenge of scaling GNNs to large graphs has been addressed
> through sampling [X, Y], graph partitioning [Z], and simplified architectures [W].
> Our work differs from all of these in that...

End each thematic paragraph (or the entire section) by explaining what your work does
that the cited works do not.

**Length:** 0.5–1 page for a 8-10 page paper. Surveys can run much longer.

---

### Methodology / Approach

**Goal:** Complete reproducibility. A competent researcher in your field should be able
to reimplement your approach from this section alone.

Include:
- Problem formulation (define notation, variables, what you're optimizing)
- Design decisions and why you made them (not just what you did)
- Pseudocode or algorithm block if the approach is algorithmic
- Architecture diagrams for systems papers
- Dataset/environment description for empirical papers

What to avoid:
- Describing what you implemented without explaining why you made those choices
- Omitting hyperparameters and configuration details (put them in appendix if too long)
- Overclaiming what the method does before showing evidence

---

### Results / Evaluation

Lead with the headline result. Don't make the reader scan a table to find your point.

**For tables:**
- Bold the best result in each column
- Include standard deviations if you ran multiple trials
- Caption should state the takeaway: "Table 1: SparseAgg matches full GNN accuracy while
  using 3.2× less memory" not "Table 1: Results"

**For plots:**
- Label axes clearly, with units
- Include error bars for experimental results
- Use a colorblind-friendly palette (viridis, colorbrewer)
- Don't use pie charts for comparisons

**Ablation studies** (ML papers): Test each component of your method independently.
This tells reviewers your method's components are all pulling weight.

---

### Discussion

Interpret results — don't just report them again.

- Why did the method work? (or fail on certain inputs?)
- What surprised you about the results?
- What are the limitations of this work? (state them honestly — reviewers trust this)
- What would a follow-on study need to address?

Limitations section is not optional for good work. Reviewers who find a limitation you
didn't mention will mark it against you. Reviewers who find a limitation you already
acknowledged will not.

---

### Conclusion

No new information. Three parts:
1. Brief restatement of what you did and found (2-3 sentences)
2. Significance — more specific than "future directions"
3. 1-3 concrete future work directions (specific enough to be actionable)

Do not: "In conclusion, we have presented a novel approach... We hope this work will
inspire future researchers to..."

---

## AI Writing Pattern Checklist

Before finalizing any section, scan for these patterns and remove them.

**Significance inflation** — remove or replace with specific claim:
- "marks a pivotal moment", "represents a significant shift", "underscores the importance"
- "is a testament to", "highlights the transformative potential"

**Trailing -ing phrases** (fake depth tacked onto sentences):
- "...contributing to better outcomes", "...ensuring scalability", "...highlighting the need for"
- Fix: either cut the phrase or make it a new sentence with a real subject

**Vague attributions**:
- "researchers have shown", "studies indicate", "experts believe"
- Fix: cite the actual paper, or say "we hypothesize"

**Promotional language**:
- "groundbreaking", "revolutionary", "state-of-the-art" (unless citing a benchmark result)
- "seamless", "robust", "powerful" (without evidence)

**Copula avoidance** (sounds stiff):
- "serves as", "functions as", "stands as", "acts as"
- Fix: usually just use "is"

**Rule of three / synonym cycling**:
- "fast, efficient, and scalable", "accurate, reliable, and robust"
- Fix: pick one and support it with evidence

**Filler openers**:
- "It is worth noting that", "It is important to mention", "Needless to say"
- "In this paper, we", "In this work, we" (cut — the reader knows)

**Hedge stacking**:
- "could potentially be argued to suggest that it might"
- Fix: commit to what you actually believe, or cite evidence

**Generic conclusions**:
- "opens exciting new directions", "paves the way for future research"
- "has broad implications for the field"
- Fix: name the specific direction or implication

**Signposting announcements**:
- "Let's dive into", "In this section, we will explore"
- Fix: just start the section

---

## Passive vs. Active Voice

Academic writing has shifted toward active voice. Use it when natural.

Avoid: "An experiment was conducted to evaluate..."
Better: "We evaluated..."

Avoid: "It was found that..."
Better: "We found that..." or "The results show that..."

Passive voice is fine when the actor is unknown or irrelevant:
- "The dataset was collected between 2018 and 2022" (fine — the actor doesn't matter)
- "Participants were recruited from..." (fine for methods)

---

## Numbers and Statistics

- Report effect sizes, not just p-values
- Standard deviations > standard errors for most ML/systems work
- Significant digits: 3 is almost always enough (not 87.234%, just 87.2%)
- Always state N (sample size) alongside any statistical claim
- Comparison baselines should be as strong as possible — using a weak baseline makes results untrustworthy
