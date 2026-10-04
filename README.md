# AutoFormer

Generating exam questions from textbooks, and then aiming them at what an
individual student gets wrong.

Two problems, in order:

1. **From documents to questions.** Given a textbook section, produce exam
   questions in a marking system's format: parts, marks per part, a model
   answer and a marking scheme. The hard part is not producing questions;
   it is telling a good one from a bad one before a student sees it.
   Above all, catching a **wrong answer key**.
2. **From weaknesses to questions.** Given evidence of what a student gets
   wrong, generate questions that target it.

Every stage is measured. A result here is a number with a method behind it,
not a demo.

## Status

**Corpus built.** Three OpenStax algebra books, parsed into teaching text and
a held-out set of the books' own exercises.

| | |
|---|---|
| Books | Prealgebra 2e, Elementary Algebra 2e, Intermediate Algebra 2e |
| Sections | 234; the 201 that teach list learning objectives (the other 33 are chapter introductions) |
| Reference exercises | 23,415 (14,279 with answers) |
| Maths expressions converted | 64,029, **0 fail to render** in KaTeX |

Exercises by kind:

| Kind | Count | With answer | What it is |
|---|---:|---:|---|
| practice | 12,567 | 6,293 | drill, mostly checkable by computer |
| try | 4,608 | 4,608 | follows a worked example |
| review | 3,890 | 1,943 | end-of-chapter review |
| practice-test | 856 | 431 | **the authors' own chapter exam** |
| writing | 592 | 284 | "explain why", marked against a rubric |
| be-prepared | 539 | 539 | readiness check on earlier sections |
| everyday | 363 | 181 | word problems |

## Decisions worth knowing

**The generator never sees the exercises.** The teaching text and the
exercises are written to separate files. If the generator could see the
book's questions, comparing its questions with them would measure copying.

**Worked examples stay in the teaching text.** In the source they are
marked up like exercises, but they are how a maths book teaches the method.
An early version dropped them; a test now guards against it.

**Step-by-step working is drawn as images in the books.** Each image's alt
text describes the step in words and was checked against the image, so the
alt text stands in for it.

**Maths is converted for KaTeX, and every expression is rendered to prove
it.** KaTeX is what the marking system displays maths with, so that is the
bar, not "looks like valid LaTeX". The first pass failed on 403 of 64,029;
each failure had a specific cause, now fixed and tested.

## Running it

```bash
bash scripts/fetch_openstax.sh       # text of the three books, ~35 MB
python scripts/build_corpus.py       # -> data/corpus/{sections,exercises}.jsonl
python -m pytest tests/

# Render every converted expression with KaTeX:
python scripts/dump_latex.py
KATEX=/path/to/node_modules/katex node scripts/check_latex.mjs
```

No runtime dependencies beyond the Python standard library; `pytest` for
the tests.

## Data and licences

| Source | Licence | Used for |
|---|---|---|
| [OpenStax algebra books](https://github.com/openstax/osbooks-prealgebra-bundle) | CC BY-NC-SA 4.0 | teaching text and reference exercises |
| [Eedi NeurIPS 2020](https://eedi.com/projects/neurips-education-challenge) | see its terms | student answers, topic hierarchy (problem 2) |
| [Eedi: Mining Misconceptions](https://www.kaggle.com/competitions/eedi-mining-misconceptions-in-mathematics) | competition rules | misconception labels (problem 2) |
| [EduQG](https://arxiv.org/abs/2210.06104) | CC BY 4.0 | expert-written questions, a secondary benchmark |

The OpenStax text is **fetched, not committed**. Its licence is ShareAlike,
so anything derived from it stays local in `data/`, which git ignores. This
repository holds only the code that builds it.

## Next

1. **Baseline generator.** Questions per section, in the marking system's
   format.
2. **First measurement.** Check every generated answer key, by computer
   where the answer can be computed and by hand on a sample: *what fraction
   are wrong?*
