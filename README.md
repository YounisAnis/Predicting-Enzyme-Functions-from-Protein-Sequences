# Predicting Enzyme Functions from Protein Sequences

A notebook-based bioinformatics study of **multi-label Enzyme Commission (EC) prediction**. The project compares frozen ESM-2 protein features with a simple amino-acid-count baseline and DIAMOND sequence similarity search. It also checks dataset overlap and performance on activities with few training examples.

An EC number describes an enzyme activity. A protein may have several activities, so the task predicts a **set of EC labels**, rather than a single class.

## What was implemented

- Audit the supplied CLEAN benchmark splits, including exact train/test sequence overlap, label frequencies, sequence lengths and input integrity.
- Convert each sequence to a 1,280-value vector using frozen `facebook/esm2_t33_650M_UR50D`, with mean pooling over residue representations.
- Cache vectors and sequence IDs, with checkpoint/resume support during encoding.
- Compare three predictors on those vectors: cosine centroids, a linear layer and a small multilayer perceptron (MLP).
- Compare against amino-acid composition plus one-vs-rest LinearSVC, and DIAMOND top-hit label transfer.
- Select thresholds on a training-derived validation slice and report micro-F1, macro-F1 and exact label-set match at four EC levels.

The encoder is not fine-tuned. There is no special class-balancing loss, contrastive training, deployed prediction service or web interface in this implementation.

## Recorded findings

These are **archived main-run results**, not a new run performed during repository preparation. The main experiment uses fold 0 at split settings 10, 30, 50 and 70.

Full EC label (level 4), micro-F1, rounded to four decimal places:

| Method | split10 | split30 | split50 | split70 |
|---|---:|---:|---:|---:|
| Amino-acid composition + SVM | 0.1084 | 0.1024 | 0.0901 | 0.1272 |
| ESM-2 + centroid | 0.2369 | 0.2582 | 0.4907 | 0.6533 |
| ESM-2 + linear | 0.1845 | 0.1998 | 0.4785 | 0.8090 |
| ESM-2 + MLP | 0.0239 | 0.1522 | 0.5736 | 0.8946 |
| DIAMOND top-hit transfer | 0.5987 | 0.6223 | 0.8647 | 0.9493 |

DIAMOND leads all four comparisons. The centroid is the strongest embedding predictor at settings 10/30; the MLP leads the embedding predictors at 50/70. Rare activities remain difficult. The settings also differ in training size and label composition, so this curve does not isolate sequence identity alone.

See [verified results and limitations](docs/results.md) for provenance, additional metrics and audit details.

## Repository structure

```text
EC_No_prediction/
├── .ecpred_root                  # Marker used to locate this project
├── notebooks/EC_pipeline.ipynb    # Full research workflow
├── src/ecpaths.py                # Portable paths and read-only input parser
├── scripts/summarize_results.py  # Inspect/check archived results without ML dependencies
├── tests/                       # Input-reader and notebook setup checks
├── requirements.txt             # Scientific Python dependencies
├── data/manifest.json            # Input filenames, sizes, SHA-256 and source information
├── results/                     # Compact archived main-run metrics and audit evidence
├── docs/data.md                  # Data acquisition, layout and upstream terms
├── docs/results.md               # Results, verification and limits
├── docs/linkedin-video-script.md # Timed script for the 31-slide presentation
├── data/                        # Raw inputs and upstream weights: local, ignored by Git
├── outputs/                     # Generated caches, models and figures: local, ignored by Git
└── deliverables/                # Existing PowerPoint presentation/poster: local, ignored by Git
```

Large inputs and generated artifacts are intentionally outside the public file set. In the prepared working folder they remain available locally; a fresh clone contains the manifest and acquisition instructions instead. The existing presentation is `deliverables/Enzyme_Function_Prediction_Presentation.pptx`.

## Quick start: inspect the saved results

Python 3.10 or newer is sufficient for the following commands. They need no dataset, GPU or third-party Python packages:

```bash
python scripts/summarize_results.py
python scripts/summarize_results.py --check
```

`--check` checks archived CSV/JSON consistency and the published artifact hashes. It does not retrain a model or regenerate predictions.

## Set up the notebook

1. Use Python 3.10 or newer and create a virtual environment.

   ```bash
   python -m venv .venv
   ```

   Activate it with `.venv\Scripts\Activate.ps1` in Windows PowerShell, or `source .venv/bin/activate` on Linux/macOS.

2. Install a PyTorch build suitable for your CPU/CUDA environment, following the [official PyTorch instructions](https://pytorch.org/get-started/locally/). Then install the remaining requirements and a notebook interface:

   ```bash
   python -m pip install -r requirements.txt
   python -m pip install jupyterlab
   ```

   The requirements list supported minimums; it is not an exact environment lock. The original recorded library versions and device are in [the run manifest](results/run_manifest.json).

3. Restore the benchmark inputs using [the data instructions](docs/data.md). The default notebook checks fold-0 train/test files for all five settings, including split100 for the audit, and the fold-0 CD-HIT FASTA. Upstream pretrained CLEAN weights are retained in the original local data tree but are not used to train the project's ESM-2 heads.

4. For the DIAMOND comparison, install the separate `diamond` executable and ensure `diamond --version` works. See the [official installation guide](https://github.com/bbuchfink/diamond/wiki/1.-Installation). The notebook can attempt `apt-get` installation on compatible Linux/Colab systems; if DIAMOND is unavailable, it reports that Stage 11 is skipped. A run without it does not reproduce the complete comparison table.

5. Start JupyterLab from the project root and open `notebooks/EC_pipeline.ipynb`. Select the environment where the requirements were installed.

   ```bash
   jupyter lab
   ```

The `.ecpred_root` marker and `src/ecpaths.py` must stay in place. Local discovery works from the project root or `notebooks/`. To use a different location, set the `ECPRED_ROOT` environment variable to the project root before running Stage 1. In Colab, when local discovery fails, the notebook can mount Drive and look for a single marker-bearing project folder directly under `MyDrive`; ambiguous locations require an explicit `ECPRED_ROOT`.

**Fresh-clone limitation:** the default notebook also requires the project's `data/cdhit/output_90_split0.fasta` for historical audit stages. Its availability in the public CLEAN downloads is not established, and its exact generation command was not recovered. Keep the supplied local copy or restore it from the original project backup. The saved-results inspection commands work without this file or any other dataset.

## Run the workflow

The configuration cell near the beginning of the notebook controls the run.

| Setting | Default | Meaning |
|---|---|---|
| `SMOKE_TEST` | `True` | Small pipeline check: 300 train / 100 test rows per setting, 3 head-training epochs |
| `SPLITS_TO_RUN` | `(10, 30, 50, 70)` | Main comparison settings |
| `FOLD` | `0` | Recorded experiment fold |
| `RUN_SPLIT100` | `False` | Split100 model experiment is disabled; its audit still runs |
| `SECOND_PASS_150M` | `False` | Optional second encoder is disabled |
| `FORCE_RECOMPUTE` | `False` | Reuse available cached stage results |

Run the cells in order. Smoke outputs go to `outputs/smoke/`; main outputs go to `outputs/`. Set `SMOKE_TEST = False` for the main experiment. Model weights are downloaded on first use, and the 650-million-parameter encoder is expensive on a CPU. The archived run used an NVIDIA Tesla T4; runtime depends on hardware, input size and cache reuse.

The local folder may already contain cached main results. With `FORCE_RECOMPUTE = False`, a run may reuse them. Use `FORCE_RECOMPUTE = True` when intentionally regenerating the experiment; this can replace local generated artifacts and requires substantial compute. Keep your saved copy if you need the original run unchanged. The published `results/` archive is separate from notebook-generated `outputs/`.

The input reader handles the malformed split50 header and quoted split30 export in memory. It never rewrites the raw files.

## Checks and reproduction status

```bash
python -m unittest discover -s tests -v
python scripts/summarize_results.py --check
```

Repository preparation restored the missing path helper, made notebook discovery portable, repaired the input reader and corrected two figure filters. Saved notebook outputs and private execution metadata were cleared. The existing model architectures, training losses and evaluation logic were preserved.

The archived inputs and results were audited, and selected saved head/DIAMOND metrics were independently reconstructed from local artifacts. A fresh end-to-end GPU rerun after these setup repairs has **not** been completed. Unit tests check setup and parsing; they do not validate a new training run.

## Interpreting the experiment

- Exact sequence overlap was zero in all supplied train/test fold pairs at settings 10–70. This is an exact-overlap check, not an independent verification of every sequence-identity bound.
- Test activities are present in the paired full training data. These experiments do not establish prediction of unseen EC labels.
- Only fold 0 was modelled. There are no five-fold uncertainty estimates, external validation or temporal validation results.
- Neural heads use 90% of training rows for fitting and 10% for validation. DIAMOND searches the complete paired training set.
- Prefix scores are rolled up for EC-level reporting, with independently selected thresholds. Final binary calls are not guaranteed to form a consistent EC hierarchy.
- Micro-F1, macro-F1 and exact label-set match measure different things. F1 values should not be called accuracy. Macro-F1 here averages activities present in the test set.
- This is a research baseline comparison. It does not establish superiority over CLEAN or other published systems, and predictions are not experimental confirmation of enzyme activity.

## Scientific sources

- [IUBMB enzyme nomenclature](https://iubmb.qmul.ac.uk/enzyme/) — EC definitions and classification.
- [Lin et al., Science (2023)](https://doi.org/10.1126/science.ade2574) — ESM-2 protein language models.
- [Yu et al., Science (2023)](https://doi.org/10.1126/science.adf2465) — CLEAN enzyme function prediction; [official repository](https://github.com/tttianhao/CLEAN).
- [Buchfink et al., Nature Methods (2021)](https://doi.org/10.1038/s41592-021-01101-x) — DIAMOND protein alignment.
- [Capela et al., BMC Bioinformatics (2025)](https://doi.org/10.1186/s12859-025-06081-9) — related enzyme annotation research.
- [Ma et al., Bioinformatics (2026)](https://doi.org/10.1093/bioinformatics/btag215) — EnzPlacer and a different unseen-label evaluation question.

## Attribution and reuse

See [third-party notices](THIRD_PARTY_NOTICES.md). This repository does not include a blanket redistribution licence for the upstream datasets or pretrained weights. Obtain those resources from their original sources and follow their terms. No open-source licence for the project's original code has been selected in this preparation step.
