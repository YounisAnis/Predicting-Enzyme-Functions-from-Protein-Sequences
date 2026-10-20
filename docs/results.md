# Archived results

These are the saved **main run**, generated on 2026-09-04, using fold 0 and the supplied settings 10, 30, 50 and 70. They are not five-fold averages. Smoke-test artifacts are excluded. Setting 100 was audited for data overlap but has no trained-model comparison in this archive.

The configured representation is frozen `facebook/esm2_t33_650M_UR50D`: 1,280 features per protein. Centroid, linear and MLP heads are compared with amino-acid composition plus linear SVM, and DIAMOND top-hit EC transfer. The learned heads use unweighted binary cross-entropy; no new class-balancing treatment was implemented.

## Full EC prediction

Full EC means level 4. F1 is a score from 0 to 1, not accuracy.

| Method | Setting 10 | Setting 30 | Setting 50 | Setting 70 |
|---|---:|---:|---:|---:|
| Composition + SVM | 0.108446 | 0.102377 | 0.090141 | 0.127233 |
| ESM-2 centroid | 0.236884 | 0.258188 | 0.490703 | 0.653312 |
| ESM-2 linear | 0.184483 | 0.199830 | 0.478464 | 0.808963 |
| ESM-2 MLP | 0.023868 | 0.152210 | 0.573643 | 0.894583 |
| DIAMOND | 0.598708 | 0.622316 | 0.864739 | 0.949322 |

Values above are micro-F1. DIAMOND leads at every evaluated setting. Among embedding heads, centroid leads at 10 and 30; MLP leads at 50 and 70. Dataset sizes and label sets both change across settings, so this curve does not isolate the effect of sequence identity.

Setting 70 contains 14,507 test proteins:

| Method | Micro-F1 | Macro-F1 | Exact-set accuracy |
|---|---:|---:|---:|
| Composition + SVM | 0.127233 | 0.017006 | 0.068243 |
| ESM-2 centroid | 0.653312 | 0.558724 | 0.641208 |
| ESM-2 linear | 0.808963 | 0.336980 | 0.796374 |
| ESM-2 MLP | 0.894583 | 0.643744 | 0.880540 |
| DIAMOND | 0.949322 | 0.813419 | 0.930103 |

Micro-F1 pools label decisions. Macro-F1 gives equal weight to every EC label present in the test set. Exact-set accuracy requires the entire predicted EC set to match the true set for a protein.

## Rare labels remain difficult

Full-EC macro-F1 at setting 70, grouped by the number of examples in the complete supplied training set:

| Training proteins per EC | Test-present EC labels | MLP | DIAMOND |
|---|---:|---:|---:|
| 1–4 | 771 | 0.380063 | 0.648043 |
| 5–19 | 754 | 0.692205 | 0.856065 |
| 20–99 | 446 | 0.885399 | 0.955577 |
| 100+ | 181 | 0.969604 | 0.989923 |

This is an observed association, not a controlled causal test. Of all 4,693 training EC labels at setting 70, 3,126 (66.6%) have only 1–4 examples; the table counts only labels also present in the test set.

## Data integrity and historical evaluation

Independent exact-sequence checks found no identical train/test sequences in any of the 20 supplied fold pairs at settings 10–70. All test EC labels occur in their paired training data: this is a known-label task.

At setting 100, fold 0, 9,611 of 45,150 test rows (21.29%) match an original training sequence. Comparing those same test rows against the provided CD-HIT-90 training FASTA gives 4,417 matches (9.78%). These are overlap measurements, not model-performance improvements. No all-pairs alignment audit was performed to independently establish the named identity thresholds.

The historical composition/SVM experiment is retained separately in `stage4_legacy_forensic.json`. Its row-index exclusion bug left 26,161 of 47,979 test rows in training (54.53%). Its 27.78% accuracy is not a clean benchmark score. The corrected internal split changed the test population, so its 29.93% accuracy is not a fair before/after improvement either.

## Verification and practical limits

The publication audit checked the original data and archived outputs without training new models:

- All ten fold-0 input CSV hashes match the original run manifest.
- All 1,060 main metric CSV entries and label-count fields agree with their stage JSONs.
- Saved embedding matrices have the expected dimensions, finite nonzero values, and accession order matching the input rows.
- NumPy reconstruction from saved embeddings and explicitly decoded checkpoint tensors reproduces the full-EC linear/MLP micro-F1, macro-F1, exact-set and top-1 metrics at every evaluated setting.
- Re-scoring saved DIAMOND hits reproduces its metrics at all four EC levels and settings.

These checks are recorded in [audit_verification.json](../results/audit_verification.json). Centroid micro-F1, exact-set and top-1 values also match; tiny independently reconstructed macro-F1 differences at settings 50 and 70 are retained in that record. No new ESM embedding extraction was performed. The original notebook snapshot had a split-50 header failure and a missing path helper. Publication repairs restore the helper and handle the input quirks in memory; they do not constitute a fresh complete GPU experiment.

Only fold 0 was modeled. No external/temporal or unseen-EC evaluation, confidence interval, encoder fine-tuning, 150M second pass, deployment, or state-of-the-art comparison is established. Each EC level has its own threshold, so level scores need not be monotonic and final predicted sets are not guaranteed to be nested across levels. Cached run times do not measure the original cost of encoding or training.

## Inspect the evidence

From the repository root, using Python 3.10 or newer:

```console
python scripts/summarize_results.py --check
```

This standard-library command prints the main tables and checks the CSV/JSON values plus the preserved artifact hashes. It does not need data downloads, NumPy, PyTorch, a GPU, or model weights. `--split 10`, `30`, `50`, or `70` selects the detailed setting.

The small [results archive](../results/) contains:

- `stage3_data_audit.json`, `stage4_legacy_forensic.json`;
- four `stage5_aac_*.json`, twelve `stage10_*.json`, four `stage11_diamond_*.json`;
- four `thresholds_*.json`, `metrics_long_fold0.csv`, and the original `run_manifest.json`;
- `archive_index.json` with checksums and original repository-relative paths; `audit_verification.json` with independent check records.

`run_manifest.json` retains its historical notebook filename; it describes the archived run, not a newly executed publication notebook. Smoke outputs, weights, embedding arrays, raw hit rows, label-space lists, personal setup metadata and the unverified external CLEAN reproduction summary are not part of this publication evidence set. No upstream raw data or model binaries are duplicated here.
