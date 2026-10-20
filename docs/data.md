# Data setup and provenance

Raw sequences, pretrained weights and generated feature caches are local inputs, not part of the compact publication results. The metadata-only [input manifest](../data/manifest.json) records the expected path, byte count and SHA256 of all **60 original input files**: 50 split CSVs, five CD-HIT FASTA files and five CLEAN pretrained assets.

## Obtain the original sources

Use the [official CLEAN repository](https://github.com/tttianhao/CLEAN) and its [installation/data instructions](https://github.com/tttianhao/CLEAN#12-quickstart):

1. Download the [five-fold train/test archive](https://drive.google.com/file/d/1MzYQ--CRK253eAKOmZrD1nzF-mXHfXtq/view?usp=sharing) linked by the authors. It contains the cross-validation splits. The authors distinguish these from the full `split10.csv`–`split100.csv` files in their repository; those full files are not substitutes for this project's fold-specific inputs.
2. For the historical CLEAN assets, obtain the [pretrained archive](https://drive.google.com/file/d/1kwYd4VtzYuMvJMWXy6Vks91DSUAOcKpZ/view?usp=sharing) linked in the same instructions.
3. Extract outside the repository, inspect the archive contents, then place the required files in the layout below. Keep filenames and file contents unchanged. The links were checked against the official README on 2026-10-19; the archives were not downloaded again during publication preparation.

The supplied `output_90_split*.fasta` files are project-generated CD-HIT outputs, described in the historical project material as 90% clustering of each setting-100 training fold. Their exact command/version history is not available in the remaining artifacts. Preserve the existing local copies or recover them from the original project backup. The links above do not establish that these project-specific FASTAs are included upstream. A newly generated file is not guaranteed to have the same representatives or byte hash.

## Expected local layout

Here `S` is one of `10`, `30`, `50`, `70`, `100`, and `F` is one of `0`, `1`, `2`, `3`, `4`:

```text
data/
  manifest.json                         # tracked metadata only
  splits/
    splitS/
      splitS_train_split_F.csv
      splitS_test_split_F_curate.csv
  cdhit/
    output_90_split0.fasta
    output_90_split1.fasta
    output_90_split2.fasta
    output_90_split3.fasta
    output_90_split4.fasta
  pretrained/
    clean/
      100.pt
      70.pt
      split100.pth
      split70.pth
      gmm_ensumble.pkl
```

The `S`/`F` notation is a pattern, not a literal folder or filename. For example, setting 70 fold 0 uses `data/splits/split70/split70_train_split_0.csv` and `data/splits/split70/split70_test_split_0_curate.csv`. Preserve the upstream `gmm_ensumble.pkl` spelling. The original bytes are retained locally; any parser normalization should happen in memory.

The frozen ESM-2 pipeline uses the split CSVs. The legacy forensic stage additionally uses the corresponding CD-HIT FASTA. The CLEAN pretrained assets belong to the historical reference material and are not the ESM-2 head checkpoints. Current main experiments cover fold 0 at settings 10–70; all five folds and setting 100 are present for data inspection.

Fold-0 profiles independently parsed from the original files:

| Setting | Training proteins | Test proteins | Training EC labels |
|---|---:|---:|---:|
| 10 | 6,444 | 1,313 | 2,702 |
| 30 | 8,115 | 1,648 | 3,155 |
| 50 | 23,953 | 5,477 | 4,209 |
| 70 | 59,546 | 14,507 | 4,693 |
| 100 | 181,889 | 45,150 | 4,942 |

## Format details that matter

- These `.csv` files are **tab-separated**, with CRLF line endings. Training/test column names differ, but the body fields are accession, EC string and sequence in that order.
- All five setting-50 training headers contain four tab-separated fields (`Entry`, `EC`, `number`, `Sequence`), while their body rows contain three. The original notebook's shape assertion failed on this quirk. Do not insert a new column into the body or rewrite raw input files to make the header appear consistent.
- Every line in setting-30 fold-0 test is wrapped in an outer pair of quotes. A suitable reader removes this wrapper before parsing fields.
- Semicolons separate multiple EC labels on one protein. They do not create a single new combined class. Some EC identifiers use provisional `n` suffixes; do not silently discard them.
- All supplied sequences are at most 1,022 residues. No cropping is needed at that limit. Nonstandard amino-acid letters can occur.

The publication reader in `src/ecpaths.py` handles the header and quoting quirks in memory. The original files and their manifest hashes are preserved.

## Validate a recovered copy

With the local inputs in place, run:

```console
python scripts/summarize_results.py --check --check-data
```

This hashes all 60 input files and reports missing or changed files. It reads without rewriting inputs. On a clone without local data, omit `--check-data` to inspect the archived scalar results alone.

These hashes identify the **specific local project copy** audited on 2026-10-19. They do not certify upstream archive contents or promise byte-for-byte stability of future downloads. A mismatch can result from changed releases, newline conversion, renamed files or local edits; investigate it before treating the copy as the same archived dataset.

## Attribution and licensing

Cite the dataset/method source: Tianhao Yu, Haiyang Cui, Jianan Canal Li, Yunan Luo, Guangde Jiang and Huimin Zhao (2023), *Enzyme function prediction using contrastive learning*, Science 379, 1358–1363, [doi:10.1126/science.adf2465](https://doi.org/10.1126/science.adf2465).

CLEAN includes a [research-use software license document](https://github.com/tttianhao/CLEAN/blob/main/NON-EXCLUSIVE%20RESEARCH%20USE%20LICENSE%20FOR%20CLEAN%20SOFTWARE.pdf). Review the relevant upstream terms for code, datasets and model assets; no blanket redistribution license for these third-party inputs is asserted here. Obtain them from the authors' sources rather than adding the sequences or weights to a public copy of this project. A license for this project's own code does not replace third-party terms.
