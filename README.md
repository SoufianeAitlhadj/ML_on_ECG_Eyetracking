# Scanpath Modelling for ECG Reading with Hidden Markov Models

A feasibility study: **can machine learning complement the purely statistical analyses usually applied to eye-tracking data collected while people read ECGs?**

We took a corpus of eye-tracking recordings of ECG interpretation, turned it into discrete scanpaths, and trained a Hidden Markov Model (HMM) to *generate* synthetic scanpaths. We then asked how close the generated gaze behaviour is to real behaviour, using three complementary evaluation layers (probabilistic, statistical, behavioural).

> **TL;DR.** The pipeline works end to end and the headline numbers look excellent, but the trained model turned out to be **degenerate**: with 4 hidden states and 4 AOIs, each hidden state emits exactly one AOI, so the HMM collapses into a relabelled first-order Markov chain. The good scores are therefore *not* evidence that scanpath dynamics were captured. This negative result, and what it tells us about the next iteration, is the main outcome of the project. See [Key finding](#key-finding-the-model-collapsed) below.

The full write-up is in [`internship_report.pdf`](internship_report.pdf).

---

## Repository contents

| File | What it is |
|---|---|
| `merge_data_unprocessed.py` | Merges the raw per-participant / per-stimulus eye-tracking exports into a single unprocessed table. |
| `preprocessing.ipynb` | Filtering, cleaning, fixation aggregation, AOI mapping and scanpath reconstruction. |
| `fixation_level_dataset.csv` | Output of preprocessing: one row per fixation. |
| `scanpath_level_dataset.csv` | Fixations grouped and ordered into one AOI sequence per participant × stimulus. |
| `hmm_on_scanpaths_level_dataset.ipynb` | HMM training, scanpath generation and the full evaluation. |
| `evaluation_results.pkl` | Serialized evaluation results (all numbers quoted below are recomputed from it). |
| `preprocessing_ecg_data_figure.png` | Diagram of the preprocessing pipeline. |
| `HMM_Algorithm.png` / `.svg` | Diagram of the HMM training (Baum-Welch) and usage. |
| `hmm_evaluation_pipeline.png` | Diagram of the three-layer evaluation. |
| `internship_report.pdf` | The report. |

Intended run order: `merge_data_unprocessed.py` → `preprocessing.ipynb` → `hmm_on_scanpaths_level_dataset.ipynb`.

---

## Approach

### 1. Preprocessing

Raw eye-tracking samples are filtered, cleaned and aggregated into fixations. Each fixation's coordinates are then mapped to an Area of Interest (AOI) by spatial discretization, and fixations are put back in temporal order to reconstruct one scanpath per participant and stimulus. The result is a sequence of AOI labels, which is the only information the HMM sees.

![Preprocessing pipeline](preprocessing_ecg_data_figure.png)

### 2. Hidden Markov Model as the generative model

We chose an HMM because a scanpath is naturally a sequence: the eye moves between regions, and the *reason* it is where it is (reading a lead, comparing rhythms, scanning for an anomaly) is not directly observed. An HMM encodes exactly that split between latent intent and observable gaze.

- **Observations**: AOI labels (categorical symbols).
- **Hidden states**: latent "attentional modes", `K` chosen before training.
- **Learned parameters**: initial distribution `π`, hidden-state transition matrix `A`, emission matrix `B`.
- **Training**: Baum-Welch (EM), alternating an E-step (state posteriors given the current model) and an M-step (parameter updates) until convergence.
- **Uses**: score unseen scanpaths (log-likelihood), decode hidden-state sequences, and sample new synthetic scanpaths.

![HMM algorithm](HMM_Algorithm.png)

### 3. Evaluation

We evaluate on three layers so that no single metric can flatter the model:

1. **Probabilistic**: average held-out log-likelihood per fixation (`model.score`).
2. **Statistical**: compare the transition matrix of real test scanpaths (`T_real`) with that of generated ones (`T_gen`).
3. **Behavioural**: dynamic-programming (alignment) similarity between each generated scanpath and its closest real scanpath.

![Evaluation pipeline](hmm_evaluation_pipeline.png)

---

## Experimental setup

| Item | Value |
|---|---|
| Model | Categorical HMM |
| Hidden states `N` | 4 |
| Observation symbols `M` | 4 (AOIs = 2×2 quadrants of the stimulus, i.e. `k = 2`) |
| EM iterations / tolerance | 100 / 1e-4 |
| Random initializations | 10 (seed 42) |
| Split | 80/20 at the **scanpath** level: 504 train / 126 test |
| Fixations | 117,660 train / 29,975 test / 147,635 total |
| Stimuli | 10 ECGs, 30 s exposure each |
| Test participants | 57 distinct |
| Scanpath length | mean 233, σ 97, median 251, range 6–424 fixations |


---

## Results

| Metric | Value |
|---|---|
| Mean per-fixation held-out log-likelihood | −0.494 ± 0.209 |
| Perplexity per fixation | 1.638 |
| Uniform baseline, log(1/4) | −1.386 |
| Unigram baseline, Σ p log p | −1.350 |
| ‖T_real − T_gen‖_F | 0.0135 (0.77 % relative) |
| Max single-entry transition difference | 0.0076 |
| Mean self-transition, real / generated | 0.874 / 0.875 |
| Entropy rate, real / generated | 0.687 / 0.684 bits per fixation |
| DP similarity (10 repetitions) | 0.539 ± 0.005 |

All 126 held-out scanpaths score above both the uniform and unigram baselines (min −1.102, max −0.152). Taken at face value, the model reproduces real transition statistics almost perfectly. The next section explains why that face value is misleading.

---
## Is further work worthwhile?

We think yes, with conditions. The pipeline (preprocessing → HMM → three-layer evaluation) is reusable, and the evaluation design is what exposed the collapse. What is missing is richer data and a sharper question. Next steps, in priority order:

1. **Fix de-duplication** so one row is provably one fixation. Re-audit this first.
2. **Richer spatial representation**: sweep `k ∈ {3, 4, 6}`, or move to clinically meaningful AOIs (12 leads + rhythm strip) or data-driven regions (k-means / DBSCAN on fixation coordinates).
3. **Mandatory baselines**: a first-order Markov chain (probabilistic branch) and a human–human alignment ceiling (behavioural branch).
4. **Participant-disjoint split** before any expertise-classification claim. The current split is at scanpath level, so the same participant can appear in train and test.
5. **Better distances**: prefer Jensen–Shannon or Hellinger (distances between distributions) over Frobenius (distance between matrices of numbers).
6. **More modalities and saliency models**: pupil, ECG-content features, and image-based saliency models as a prior over where experts should look.
7. **Fix a concrete industrial question** (e.g. expertise assessment, training feedback, or decision-support) so that model choice and evaluation are driven by a use case rather than by what is easy to measure.

---


<!-- TODO: name, supervisor, institution, contact -->
