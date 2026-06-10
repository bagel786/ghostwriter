# Citation Styles

## Which Style to Use

| Venue type | Style |
|-----------|-------|
| ACM (CHI, CSCW, SIGMOD, etc.) | ACM Reference Format |
| IEEE conferences and journals | IEEE |
| Nature, Science, most life sciences | Vancouver (numbered) |
| Social sciences, psychology | APA 7th |
| Humanities | Chicago / MLA |
| arXiv preprint (no venue) | Whatever matches your field above |

---

## BibTeX Format (use for all LaTeX output)

Always write a `.bib` file. Use these entry types:

### Conference paper
```bibtex
@inproceedings{smith2023method,
  author    = {Smith, John and Doe, Jane},
  title     = {A Novel Method for Graph Learning},
  booktitle = {Proceedings of the 37th International Conference on Machine Learning},
  series    = {ICML '23},
  pages     = {1234--1245},
  year      = {2023},
  publisher = {PMLR},
  address   = {Honolulu, Hawaii},
  doi       = {10.xxxx/xxxxx},
}
```

### Journal article
```bibtex
@article{lee2022survey,
  author  = {Lee, Alice and Park, Bob},
  title   = {A Survey of Efficient Attention Mechanisms},
  journal = {Journal of Machine Learning Research},
  volume  = {23},
  number  = {1},
  pages   = {1--45},
  year    = {2022},
  doi     = {10.xxxx/xxxxx},
}
```

### arXiv preprint
```bibtex
@misc{wang2024preprint,
  author        = {Wang, Chris and Liu, Dana},
  title         = {Scaling Laws for Sparse Models},
  year          = {2024},
  eprint        = {2401.12345},
  archivePrefix = {arXiv},
  primaryClass  = {cs.LG},
  url           = {https://arxiv.org/abs/2401.12345},
}
```

### Book
```bibtex
@book{goodfellow2016deep,
  author    = {Goodfellow, Ian and Bengio, Yoshua and Courville, Aaron},
  title     = {Deep Learning},
  year      = {2016},
  publisher = {MIT Press},
  address   = {Cambridge, MA},
  url       = {https://www.deeplearningbook.org},
}
```

### Book chapter
```bibtex
@incollection{lecun1998gradient,
  author    = {LeCun, Yann and Bottou, Leon and Bengio, Yoshua and Haffner, Patrick},
  title     = {Gradient-Based Learning Applied to Document Recognition},
  booktitle = {Intelligent Signal Processing},
  editor    = {Haykin, Simon and Kosko, Bernard},
  pages     = {306--351},
  year      = {2001},
  publisher = {IEEE Press},
}
```

### Thesis
```bibtex
@phdthesis{vaswani2017thesis,
  author = {Vaswani, Ashish},
  title  = {Attention-Based Sequence to Sequence Learning},
  school = {University of Southern California},
  year   = {2017},
}
```

### Software / Dataset
```bibtex
@software{pytorch2019,
  author  = {Paszke, Adam and others},
  title   = {{PyTorch}: An Imperative Style, High-Performance Deep Learning Library},
  url     = {https://pytorch.org},
  version = {1.x},
  year    = {2019},
}
```

---

## In-Text Citation Formats

### ACM Reference Format (author-year)
- Single author: (Smith, 2023)
- Two authors: (Smith and Doe, 2023)
- Three or more: (Smith et al., 2023)
- Multiple citations: (Smith, 2023; Lee and Park, 2022)
- LaTeX: `\cite{smith2023}` with `\bibliographystyle{ACM-Reference-Format}`

### IEEE (numbered)
- Single: [1]
- Multiple: [1], [2], [3] or [1]–[3]
- LaTeX: `\cite{smith2023}` with `\bibliographystyle{IEEEtran}`
- IEEE style: never use author names in-text, just numbers

### APA 7th
- Single: (Smith, 2023)
- Two authors: (Smith & Doe, 2023)  ← note the ampersand
- Three or more: (Smith et al., 2023)
- Direct quote: (Smith, 2023, p. 45)
- LaTeX: use `natbib` with `\bibliographystyle{apalike}`

### Vancouver (numbered, life sciences)
- Cite by number in order of first appearance: [1], [2], [3]
- Same source cited again uses the same number
- Reference list is ordered by number, not alphabetically

---

## LaTeX Bibliography Setup

### For ACM papers
```latex
% In preamble — ACM template handles this automatically
\bibliographystyle{ACM-Reference-Format}
% At end of document
\bibliography{references}
```

### For IEEE papers
```latex
\bibliographystyle{IEEEtran}
\bibliography{references}
```

### For author-year (natbib)
```latex
\usepackage{natbib}
\bibliographystyle{apalike}  % or plainnat, abbrvnat
% In text: \citet{smith2023} → "Smith et al. (2023)"
%          \citep{smith2023} → "(Smith et al., 2023)"
\bibliography{references}
```

### For numbered (biblatex)
```latex
\usepackage[style=numeric, sorting=none]{biblatex}
\addbibresource{references.bib}
% At end: \printbibliography
```

---

## Common Citation Mistakes

- **Don't cite Wikipedia** in academic papers. Find the primary source.
- **Don't cite "et al."** in BibTeX — list all authors and let the style handle abbreviation.
- **Preprints need a note** if the work has since been published: "arXiv preprint arXiv:xxxx (published at ICML 2024 as...)"
- **Consistency**: pick one style and use it throughout. Don't mix [1] and (Smith, 2023).
- **DOIs**: include them when available. They're permanent; URLs are not.
- **Accessed dates**: required for web pages, not for papers.
