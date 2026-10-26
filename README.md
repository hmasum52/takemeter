# TakeMeter

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first** — setup, the
> notebook, the baseline, and what to do when something breaks.
>
> Once `python test.py` passes:
>
> ```bash
> head -5 data/practice_labels.csv     # the shape your labels.csv needs
> ```
>
> Then open `takemeter.ipynb` **in this folder** — in VS Code, or with
> `jupyter notebook` if you prefer. Pick the kernel: the `.venv` inside this
> project. Run section 1, which reports the hardware you'll be training on.
> Everything else waits until you have data.
>
> Nothing to upload, nothing to connect, no accounts and no keys. The notebook
> runs on your machine and writes next to your code.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     HOW TO USE THIS FILE

     Unit 5 asks for the first five sections. Unit 6 adds the five below them.

     Everything is pasted as TEXT. No screenshots, no images.

     ⚠️ The confusion matrix especially. The notebook prints one as a markdown
     table, ready to copy. A screenshot of a matrix earns nothing. Paste the
     table.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 5 — THE BUILD ═══════════════════════ -->

## What This Does

<!-- Your community, and what your classifier sorts posts into. Three or four
     sentences. -->

My community is r/technology. Most of its posts are news headlines about tech
companies, AI, security, and the people and governments around them. TakeMeter
reads a headline and asks one question: what is its main point? It sorts each
post into one of five labels: `business` (a deliberate move), `incident`
(something went wrong), `legal` (government, courts, regulators, or police
acting), `claim` (an opinion, warning, or prediction), or `analysis`
(something measured). It is DistilBERT fine-tuned on 280 headlines I labelled.

---

## Label Taxonomy

<!-- Each label: a one-sentence definition and two real examples from your
     reading. Then your decision rule for the hardest boundary.

     The decision rule is worth a point on its own and it's the thing most
     people leave out. Every taxonomy has a hardest boundary. Name yours. -->

### `business`

**Definition:** The headline's point is a deliberate move by a company or
person: a launch, layoff, deal, product, or plan.

**Example 1:**
> Netflix cuts 1,000 jobs as streaming giant seeks to boost engagement

**Example 2:**
> Uber begins self-driving robotaxi trial in Manchester

### `incident`

**Definition:** The headline's point is something that went wrong: a hack,
attack, breach, outage, accident, or AI misbehaving.

**Example 1:**
> '123456' password linked to Denmark data breach affecting 8.8M people

**Example 2:**
> Hackers heat French supermarket fridges to 50C in large-scale cyber attack

### `legal`

**Definition:** The headline's point is government, courts, regulators, or
police acting: a lawsuit, ruling, ban, fine, arrest, or bill.

**Example 1:**
> Florida can enforce state law barring young kids from social media, appeals court rules

**Example 2:**
> Eight states accuse OpenAI of coaching children to harm themselves in lawsuit

### `claim`

**Definition:** The headline's point is an opinion, warning, prediction, or
demand, from a named person, an organization, or the writer.

**Example 1:**
> BlackRock's Larry Fink warns a data center moratorium could trigger a recession

**Example 2:**
> AI will make Americans dumber and poorer

### `analysis`

**Definition:** The headline's point is something measured: a number, study,
or data result.

**Example 1:**
> Mobile phone sales plunge to lowest level in 14 years

**Example 2:**
> China chip exports jump 136% to US$45b as AI frenzy jacks up prices

### The hardest boundary

**Which two labels:** `incident` and `legal`

**The decision rule I used every time:**
<!-- e.g. "If the post names a specific checkable fact, it's `analysis`, even
     if the tone is heated." -->
Ask what the headline's main point is. If government, courts, regulators, or
police are the ones acting, it's `legal`, even when the story started as an
incident ("Grandmother falsely accused… sues" is `legal`, the lawsuit is the
point). If something went wrong and nobody official has acted yet, it's
`incident`. Any other deliberate move is `business`. An opinion, warning, or
prediction, from a named person or the writer, is `claim`, unless it's an
official action (sues, rules, bans), which is `legal`. A writer's verdict on a
specific lawsuit, hack, or company move goes with that subject ("Lyft's
settlement ignores the future" is `legal`); a general verdict ("AI will make
Americans dumber") is `claim`. A number that is the finding ("sales plunge to
lowest in 14 years") is `analysis`; a number that describes an action ("cuts
1,000 jobs") goes with the action.



---

## The Dataset

<!-- Where you collected from, how you labelled, your counts, and three hard
     cases. -->

**Where the posts came from:** Public r/technology posts, pulled from
Reddit's RSS/Atom feeds (no login needed) by `scripts/scrape_reddit.py`. After
cleaning and de-duplicating, that gave 530 headlines in `data/raw_posts.json`.

**How I labelled them:** <!-- Cold first? Pre-labelled with AI and corrected?
Say so plainly — the disclosure is required, not penalised. -->
Pre-labelled with AI, then corrected. I labelled 30 headlines by hand first.
Then I gave Claude my definitions and those 30 as the pattern, and had it label
the rest of the pool. I read every label it gave and fixed the ones that broke
my rules. Then I picked 280 so the five labels came out roughly even.
`data/prelabels.csv` is the full corrected pool, and `labels.csv` is the 280.

**Counts per label:**

| Label | Count | Share |
|---|---|---|
| `analysis` | 60 | 21.4% |
| `business` | 57 | 20.4% |
| `claim` | 56 | 20.0% |
| `incident` | 54 | 19.3% |
| `legal` | 53 | 18.9% |
| **Total** | 280 | 100% |

**Three hard cases**

<!-- Any post that made you pause: what it was, which two labels it could have
     been, and what you chose. These are worth more than the easy 190. -->

**1.**
> *The post:* "Lyft’s historic wage theft settlement fixes the past but
> ignores the future | The $272 million settlement could compensate thousands
> of drivers for past grievances. But it does little to change the rules
> governing gig work today"
>
> *Could have been:* `claim` or `legal`
>
> *I chose, because:* `legal`. It's the writer's opinion, which pulls toward
> `claim`. But the opinion is about one specific lawsuit settlement, and my
> rule sends a verdict on a specific lawsuit to that lawsuit's label. `claim`
> is for general verdicts like "AI will make Americans dumber."

**2.**
> *The post:* "Microsoft docs warned its AI was starting a 'doom loop' that
> could gut the web"
>
> *Could have been:* `incident` or `claim`
>
> *I chose, because:* `claim`. "Doom loop" sounds like something going wrong,
> but nothing has broken yet. The point is a warning about what could happen,
> and warnings are `claim`.

**3.**
> *The post:* "Paying for AI’s Data Centers Would Take 250 Million Jobs.
> America Has 159 Million"
>
> *Could have been:* `claim` or `analysis`
>
> *I chose, because:* `analysis`. The headline clearly argues that AI spending
> doesn't add up, which reads like a `claim`. But the argument *is* the
> computed number (250 million vs 159 million). When the number is the
> finding, it's `analysis`.

---

## The Training Run

<!-- Your starting model, your settings, and anything you changed and why. -->

**Base model:** `distilbert-base-uncased`

**Settings:** <!-- epochs, learning rate, batch size, seed -->
3 epochs, learning rate 2e-5, batch size 16, max length 128, seed 42.

**Anything I changed from the defaults, and why:** No hyperparameters. The
one change is in `requirements.txt`: I pinned the CUDA build of torch
(`torch==2.14.1+cu130`) so training runs on my laptop GPU (RTX 5060) instead
of the CPU.

**Split sizes:** <!-- train / val / test, and per-label counts in the test
split. If a label had fewer than about 8 in test, say so — it explains a lot
of next unit's variance. -->
196 train / 42 validation / 42 test (70/15/15, stratified).

| Label | Test count |
|---|---|
| `business` | 9 |
| `incident` | 8 |
| `legal` | 8 |
| `claim` | 8 |
| `analysis` | 9 |

No label is below 8, but all of them are right at that floor. One post swings a
label's F1 by about 0.1, so expect per-label scores to move between seeds.


---

## How I Used AI

<!-- Two specific moments — what you asked, what came back, what you changed.

     ⚠️ Plus disclosure of any pre-labelling. If you had a model pre-label a
     batch and then read and corrected every one, say that. It's an allowed
     workflow and disclosing it costs you nothing. Not disclosing it is the
     problem. -->

**Moment 1**

- *What I asked for:* I had labelled 30 headlines by hand. I asked Claude to
  label the rest of the data the same way, using my five definitions and those
  30 as the pattern.
- *What came back:* A label for every remaining post, some with a short note
  explaining the call.
- *What I changed:* I read every label and corrected the ones that broke my
  rules. Then I picked the 280 for `labels.csv` so the classes stayed balanced.

**Moment 2**

- *What I asked for:* Help writing the decision rule for my hardest boundary
  (`incident` vs `legal`) and wording the acceptance criteria in
  `criteria.md`.
- *What came back:* A draft rule built around one question: who is acting? If
  officials are acting, it's `legal`. If something went wrong, it's
  `incident`.
- *What I changed:* I added the clauses I needed from cases I hit while
  labelling: a writer's verdict on a specific lawsuit goes with that lawsuit,
  and a number that describes an action goes with the action, not
  `analysis`. I also tied each criterion's reason to my own test counts.

**Pre-labelling disclosure:** Yes. I labelled 30 posts by hand. Claude
pre-labelled the rest following that pattern, and I read and corrected every
one before choosing the final 280.

<!-- ═══════════════════════ UNIT 6 — THE TEST ═══════════════════════

     Don't fill these in during unit 5.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Baseline vs. Trained

<!-- Both models on the same posts. `python baseline.py --trained results.json`
     prints this table for you. -->

Both columns are scored on the same 42 held-out posts (`test_split.csv`), seed
42. The baseline is `facebook/bart-large-mnli`, zero-shot, using my definitions
from `label_definitions.txt`, run on the GPU.

| Measure | Baseline | Trained | Difference |
|---|---|---|---|
| Overall accuracy | 0.476 | 0.548 | +0.071 |
| Macro F1 | 0.430 | 0.533 | +0.103 |
| F1 — `analysis` | 0.636 | 0.267 | -0.370 |
| F1 — `business` | 0.200 | 0.762 | +0.562 |
| F1 — `claim` | 0.519 | 0.435 | -0.084 |
| F1 — `incident` | 0.462 | 0.800 | +0.338 |
| F1 — `legal` | 0.333 | 0.400 | +0.067 |

**Definitions vs. bare label names:** I also ran the baseline with no
definitions, only the label names. Accuracy was 0.310 (macro F1 0.270) against
0.476 (0.430) with definitions, so my definitions were worth about 0.17 accuracy.
The table above uses the run with definitions.

**What I predicted before I looked:**
<!-- Milestone 1 asks you to write this BEFORE seeing the trained numbers. A
     prediction made afterwards isn't one. -->
I predict the trained model will beat the baseline on all five labels, because
it learned from my 196 labelled examples while the baseline only had the
definitions. (Written after I ran the baseline alone, before I compared it to
the trained results.)

**What the gap actually means:**
<!-- If the baseline matched your trained model, your fine-tuning added
     nothing — and that is a real finding, not a failure. Say it plainly. -->
My prediction was only partly right. The trained model beat the baseline on
three labels (`business`, `incident`, `legal`) and overall (+0.07 accuracy, +0.10
macro F1), but lost on `analysis` (-0.37) and `claim` (-0.08). With 42 test
posts and 8-9 per label, one post moves a label's F1 by about 0.1, so only the
big gaps (`business`, `incident`, `analysis`) are clearly more than noise. On
this seed, fine-tuning helped most where the label depends on my own rules, and
the baseline did better where the definition is close to plain English ("a
number, study, or data result").



---

## Run Log — Before

<!-- Five criteria across three seeds. The notebook's section 6 prints the
     spread table; the Target and Verdict columns are yours. -->

| Criterion | Target | Seed 42 | Seed 7 | Seed 2024 | Verdict |
|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |
| 2.  |  |  |  |  |  |
| 3.  |  |  |  |  |  |
| 4.  |  |  |  |  |  |
| 5.  |  |  |  |  |  |

### Confusion matrix

<!-- ⚠️ TYPED AS A MARKDOWN TABLE. The notebook prints one ready to paste.
     An image of a matrix earns nothing. -->

| true \ predicted |  |  |  |
|---|---|---|---|
| **** |  |  |  |
| **** |  |  |  |
| **** |  |  |  |

**My biggest off-diagonal number, and what it means:**
<!-- Not "the model made mistakes" — WHICH boundary it didn't learn, and which
     direction. "7 real analysis posts were called hot_take and only 3 went the
     other way" is a direction, not just an error rate. -->



---

## Verdicts and Diagnoses

<!-- MET or MISSED against LAST UNIT's target. The target has to hold across
     all three seeds, not turn up sometimes. -->

| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 |  |  |  |  |
| 2 |  |  |  |  |
| 3 |  |  |  |  |
| 4 |  |  |  |  |
| 5 |  |  |  |  |

**Diagnoses**

<!-- For each miss: the cause, and how you know. The four common causes are:
     too few examples for a label, a boundary you applied inconsistently, a
     genuinely hard label pair, and a task the model can't reach from this
     much data.

     ⚠️ Use your agreement report as evidence. It is the only instrument you
     have that can tell a LABELLING problem from a MODEL problem, and this
     section is graded on whether you used it that way. -->



---

## Agreement Report

<!-- Your rate against the staff set, and every disagreement adjudicated.

     Remember you labelled these 30 under the STAFF taxonomy in
     data/staff_taxonomy.md, not your own — so every argument below is made
     from those definitions and those decision rules. -->

**Agreement rate:** ___ / 30 = ___%

<!-- Nobody grades this number. A 60% who argues every disagreement from the
     stated rules beats a 95% who wrote "staff was right" nine times. Several
     of the 30 were chosen because they're genuinely ambiguous — you should be
     winning some of these. -->

**Disagreements**

<!-- Three lines each: the post, both labels, and who you think is right and
     why — grounded in the staff definitions you were both applying.

     Then sort each into one of three piles:
       (a) the rule covered it and I applied it loosely → a consistency problem
       (b) the rule genuinely doesn't say               → a gap in the definitions
       (c) the rule is ambiguous here and my reading is defensible → argue it.
           This is a legitimate win.

     Pile (a) is the one that matters most for your diagnosis: if you applied a
     written rule two different ways on 30 posts, that is direct evidence about
     what you did across your own 200. -->

**1.**
> *The post:*
>
> *Staff said / I said:*
>
> *My call, and why:*
>
> *Which pile:*

**2.**
> *The post:*
>
> *Staff said / I said:*
>
> *My call, and why:*
>
> *Which pile:*

**What the pattern in my disagreements tells me:**



---

## The Improvement

**What I changed:**

**Which diagnosis pointed at it:**

### Run Log — After

| Criterion | Target | Seed 42 | Seed 7 | Seed 2024 | Verdict |
|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |
| 2.  |  |  |  |  |  |
| 3.  |  |  |  |  |  |
| 4.  |  |  |  |  |  |
| 5.  |  |  |  |  |  |

**Did it help, and how do I know:**

<!-- If it didn't, say so. Relabelling that didn't help is a genuinely
     interesting result and earns full credit. -->



---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped. -->



**The gap between what I meant my labels to capture and what the model
learned:**
<!-- Two sentences. Your confusion matrix is the evidence. -->



<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 5

       [ ] criteria.md has five numbered criteria, each naming a NUMBER
       [ ] Each has a reason underneath tied to your data or taxonomy
       [ ] labels.csv: at least 150 rows, text/label/note, ONE file not split
       [ ] No label above 70%
       [ ] All five unit 5 sections have real content
       [ ] Label Taxonomy includes the decision rule for your hardest boundary
       [ ] The Dataset includes three hard cases
       [ ] results.json and test_split.csv committed (the notebook does this)
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN

     SUBMISSION CHECKLIST — unit 6

       [ ] Baseline vs. Trained table, with your prediction written beforehand
       [ ] Run Log — Before, five criteria across three seeds
       [ ] Confusion matrix TYPED AS A MARKDOWN TABLE
       [ ] A verdict on every criterion
       [ ] A diagnosis for every miss, using the agreement report as evidence
       [ ] Agreement Report with every disagreement adjudicated
       [ ] One improvement, with Run Log — After
       [ ] What's Still Broken
       [ ] results_three_seeds_before.json, results_three_seeds_after.json,
           baseline_results.json and
           agreement_results.json committed
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
