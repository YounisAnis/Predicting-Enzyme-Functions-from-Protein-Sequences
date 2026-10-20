"""Portable paths and read-only parsing for the supplied EC benchmark files.

By default the project root is the directory above ``src``. Set ECPRED_ROOT
to use a separately stored dataset/output tree carrying the .ecpred_root marker.
"""

from __future__ import annotations

import csv
import os
from pathlib import Path

CSV_SEP = "\t"
SPLIT_VALUES = (10, 30, 50, 70, 100)
FOLDS = tuple(range(5))

# Counts of data records in the original supplied train/test files.
EXPECTED_ROWS = {
    (10, 0): (6444, 1313),
    (10, 1): (6543, 1238),
    (10, 2): (6538, 1217),
    (10, 3): (6534, 1196),
    (10, 4): (6545, 1202),
    (30, 0): (8115, 1648),
    (30, 1): (8138, 1614),
    (30, 2): (8170, 1574),
    (30, 3): (8173, 1600),
    (30, 4): (8212, 1534),
    (50, 0): (23953, 5477),
    (50, 1): (23953, 5492),
    (50, 2): (23954, 5500),
    (50, 3): (23954, 5501),
    (50, 4): (23954, 5531),
    (70, 0): (59546, 14507),
    (70, 1): (59564, 14493),
    (70, 2): (59608, 14397),
    (70, 3): (59681, 14385),
    (70, 4): (59549, 14497),
    (100, 0): (181889, 45150),
    (100, 1): (181889, 45131),
    (100, 2): (181890, 45142),
    (100, 3): (181890, 45157),
    (100, 4): (181890, 45152),
}

CLEAN_WEIGHTS = {
    "model_split100": "split100.pth",
    "model_split70": "split70.pth",
    "esm_split100": "100.pt",
    "esm_split70": "70.pt",
    "gmm": "gmm_ensumble.pkl",
}


def find_project_root(start: str | Path | None = None) -> Path:
    """Find a marker from a start directory, or honor an explicit root override."""
    override = os.environ.get("ECPRED_ROOT")
    if override:
        root = Path(override).expanduser().resolve()
        if not (root / ".ecpred_root").is_file():
            raise FileNotFoundError(f"ECPRED_ROOT has no .ecpred_root marker: {root}")
        return root
    origin = Path(start).expanduser().resolve() if start is not None else Path(__file__).resolve().parent
    if origin.is_file():
        origin = origin.parent
    for root in (origin, *origin.parents):
        if (root / ".ecpred_root").is_file():
            return root
    raise FileNotFoundError(
        f"No .ecpred_root marker above {origin}. Set ECPRED_ROOT to the project directory."
    )


ROOT = find_project_root()
DATA = ROOT / "data"
SPLITS = DATA / "splits"
CDHIT = DATA / "cdhit"
PRETRAINED = DATA / "pretrained" / "clean"
OUTPUTS = ROOT / "outputs"
EMBEDDINGS = OUTPUTS / "embeddings"
RESULTS = OUTPUTS / "results"
FIGURES = OUTPUTS / "figures"
LOGS = OUTPUTS / "logs"


def _split_fold(split: int, fold: int) -> tuple[int, int]:
    if split not in SPLIT_VALUES or fold not in FOLDS:
        raise ValueError(f"Expected split in {SPLIT_VALUES} and fold in {FOLDS}; got {split}, {fold}")
    return split, fold


def _filename(value: str) -> str:
    if not value or value in (".", "..") or "/" in value or "\\" in value:
        raise ValueError(f"Expected a filename or model tag without directories: {value!r}")
    return value


def train_csv(split: int, fold: int = 0) -> Path:
    split, fold = _split_fold(split, fold)
    return SPLITS / f"split{split}" / f"split{split}_train_split_{fold}.csv"


def test_csv(split: int, fold: int = 0) -> Path:
    split, fold = _split_fold(split, fold)
    return SPLITS / f"split{split}" / f"split{split}_test_split_{fold}_curate.csv"


def cdhit_fasta(fold: int = 0) -> Path:
    _split_fold(100, fold)
    return CDHIT / f"output_90_split{fold}.fasta"


def clean_weight(name: str) -> Path:
    try:
        return PRETRAINED / CLEAN_WEIGHTS[name]
    except KeyError:
        raise ValueError(f"Unknown CLEAN weight name {name!r}; choose from {tuple(CLEAN_WEIGHTS)}") from None


def emb_file(split: int, fold: int, part: str, model: str = "esm2_650M") -> Path:
    split, fold = _split_fold(split, fold)
    if part not in ("train", "test"):
        raise ValueError(f"Expected part 'train' or 'test'; got {part!r}")
    return EMBEDDINGS / f"{_filename(model)}_split{split}_fold{fold}_{part}.npy"


def ids_file(split: int, fold: int, part: str, model: str = "esm2_650M") -> Path:
    return emb_file(split, fold, part, model).with_suffix(".ids.txt")


def result_file(name: str) -> Path:
    return RESULTS / _filename(name)


def ensure_output_dirs() -> None:
    for directory in (EMBEDDINGS, RESULTS, FIGURES, LOGS):
        directory.mkdir(parents=True, exist_ok=True)


def _tsv_fields(line: str, source: Path, line_number: int) -> list[str]:
    # Some exported records wrap the complete TSV line in one CSV quote pair.
    # Literal backslash-t exports are also accepted; protein fields cannot contain
    # tabs or backslashes, so their intended field boundary is unambiguous.
    if "\t" not in line and "\\t" in line:
        line = line.replace("\\t", "\t")
    try:
        fields = next(csv.reader([line], delimiter=CSV_SEP, strict=True))
        if len(fields) == 1 and "\t" in fields[0]:
            fields = next(csv.reader(fields, delimiter=CSV_SEP, strict=True))
    except csv.Error as exc:
        raise ValueError(f"{source.name}:{line_number}: invalid TSV quoting: {exc}") from exc
    return fields


def read_split_csv(path: str | Path):
    """Read three biological fields without modifying the input file.

    Handles CRLF, ordinary field quoting, a quoted whole TSV line, and the
    split50 header ``Entry<TAB>EC<TAB>number<TAB>Sequence`` over three-field
    data rows. Only that known header is repaired. Other column-count errors
    fail with the source line, rather than shifting biological values silently.
    Columns retain their source names; the notebook normalizes them by position.
    """
    import pandas as pd

    source = Path(path)
    records = []
    header = None
    with source.open("r", encoding="utf-8-sig", newline="") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            fields = _tsv_fields(line.rstrip("\r\n"), source, line_number)
            if header is None:
                if fields == ["Entry", "EC", "number", "Sequence"]:
                    fields = ["Entry", "EC number", "Sequence"]
                if len(fields) != 3:
                    raise ValueError(f"{source.name}:{line_number}: expected 3 header fields, got {len(fields)}")
                header = fields
            else:
                if len(fields) != 3:
                    raise ValueError(f"{source.name}:{line_number}: expected 3 data fields, got {len(fields)}")
                records.append(fields)
    if header is None:
        raise ValueError(f"{source.name}: empty split file")
    return pd.DataFrame(records, columns=header, dtype=str)


def verify(strict: bool = False) -> bool:
    """Report available data; optionally require the notebook's default inputs."""
    required = [path for split in SPLIT_VALUES for path in (train_csv(split), test_csv(split))]
    required.append(cdhit_fasta())
    missing = [path for path in required if not path.is_file()]
    print(f"ECPred root: {ROOT}")
    print(f"Default fold-0 inputs: {len(required) - len(missing)}/{len(required)} present")
    print(f"Output directory: {OUTPUTS}")
    if missing:
        for path in missing:
            print(f"  missing: {path.relative_to(ROOT)}")
        if strict:
            raise FileNotFoundError("Default benchmark inputs are missing. Restore data/ before running the pipeline.")
    return not missing
