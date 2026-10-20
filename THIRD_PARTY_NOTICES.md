# Third-party resources and attribution

The notebook uses third-party software, scientific datasets and pretrained models. Their terms remain with their respective owners; this project does not relicense them.

| Resource | Original source | Use in this project |
|---|---|---|
| CLEAN benchmark and supplied CLEAN artifacts | [Official CLEAN repository](https://github.com/tttianhao/CLEAN); [Yu et al. (2023)](https://doi.org/10.1126/science.adf2465) | Benchmark split inputs; upstream weights retained locally for provenance, not used by the project's ESM-2 prediction heads |
| ESM-2 | [Official ESM repository](https://github.com/facebookresearch/esm); [Hugging Face model card](https://huggingface.co/facebook/esm2_t33_650M_UR50D); [Lin et al. (2023)](https://doi.org/10.1126/science.ade2574) | Frozen protein sequence encoder |
| DIAMOND | [Official DIAMOND repository](https://github.com/bbuchfink/diamond); [Buchfink et al. (2021)](https://doi.org/10.1038/s41592-021-01101-x) | Separate executable for the top-hit sequence similarity baseline |
| Python scientific libraries | Packages listed in `requirements.txt` | Data processing, machine learning and figures |

The CLEAN repository includes a **NON-EXCLUSIVE RESEARCH USE LICENSE FOR CLEAN SOFTWARE** document. Do not assume permissive redistribution rights for its datasets or pretrained artifacts. Consult the upstream documentation and applicable terms before obtaining or redistributing them. Links and local input hashes are provided in [the data guide](docs/data.md) and [the manifest](data/manifest.json); the payloads are ignored by Git.

The supplied CD-HIT FASTA files are retained locally as historical project inputs. Their exact generation command and tool version were not recovered, so the repository does not claim a fully reproducible clustering step.

The compact results archive contains this project's scalar measurements and provenance records. The original PowerPoint presentation and poster remain local in `deliverables/` and are excluded from the public file set.

No licence for the original project code has been selected as part of repository preparation. Attribution and public availability alone do not grant an open-source licence. Choose a licence only when you have the authority to grant the relevant rights.
