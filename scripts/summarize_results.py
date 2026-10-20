#!/usr/bin/env python3
"""Summarize archived main results using only Python's standard library.

This reads saved numbers; it does not train models or run ESM/DIAMOND.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[1]
SPLITS = (10, 30, 50, 70)
METHODS = (
    ("AAC + SVM", "H0_AAC_LinearSVC", "stage5_aac"),
    ("ESM-2 centroid", "H1_centroid", "stage10_H1_centroid_esm2_650M"),
    ("ESM-2 linear", "H2_linear", "stage10_H2_linear_esm2_650M"),
    ("ESM-2 MLP", "H3_mlp", "stage10_H3_mlp_esm2_650M"),
    ("DIAMOND", "B1_DIAMOND", "stage11_diamond"),
)


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def table(headers, rows):
    rows = [[str(value) for value in row] for row in rows]
    widths = [max(len(str(h)), *(len(row[i]) for row in rows)) for i, h in enumerate(headers)]
    print("  ".join(str(h).ljust(widths[i]) for i, h in enumerate(headers)))
    print("  ".join("-" * width for width in widths))
    for row in rows:
        print("  ".join(value.ljust(widths[i]) for i, value in enumerate(row)))


def read_stages(folder: Path):
    return {
        (key, split): read_json(folder / f"{prefix}_split{split}_fold0.json")
        for _, key, prefix in METHODS
        for split in SPLITS
    }


def check_saved_metrics(folder: Path, stages):
    """Check CSV values, frequency-bin sizes, and preserved artifact hashes."""
    with (folder / "metrics_long_fold0.csv").open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    seen = set()
    for line, row in enumerate(rows, 2):
        metric = row["metric"]
        source = stages[(row["head"], int(row["split"]))]["variants"][row["test_variant"]][f"level{row['level']}"]
        if metric.startswith("macro_f1[") and metric.endswith("]"):
            frequency = source["frequency_bins"][metric[len("macro_f1[") : -1]]
            expected = frequency["macro_f1"]
            expected_n = frequency["n_labels"]
        else:
            expected = source[metric]
            expected_n = source["labels_in_test"]
        if not math.isclose(float(row["value"]), expected, rel_tol=1e-12, abs_tol=1e-12):
            raise ValueError(f"CSV/JSON mismatch on metrics line {line}")
        if int(row["n_labels"]) != expected_n:
            raise ValueError(f"CSV/JSON label-count mismatch on metrics line {line}")
        unique = tuple(row[k] for k in ("split", "head", "encoder", "test_variant", "level", "metric"))
        if unique in seen:
            raise ValueError(f"Duplicate metric on CSV line {line}")
        seen.add(unique)
    if len(rows) != 1060:
        raise ValueError(f"Expected 1060 archived main metric rows; found {len(rows)}")
    index = read_json(folder / "archive_index.json")
    for record in index["files"]:
        path = folder / Path(record["path"]).name
        if hashlib.sha256(path.read_bytes()).hexdigest() != record["sha256"]:
            raise ValueError(f"Archived evidence checksum changed: {path.name}")
    print(f"Verified {len(rows):,} CSV/JSON metrics and {len(index['files'])} preserved artifact hashes.\n")


def check_data(manifest_path: Path):
    manifest = read_json(manifest_path)
    root = manifest_path.resolve().parent.parent
    missing = []
    mismatched = []
    for record in manifest["files"]:
        path = root / record["path"]
        if not path.is_file():
            missing.append(record["path"])
            continue
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
        if path.stat().st_size != record["bytes"] or digest.hexdigest() != record["sha256"]:
            mismatched.append(record["path"])
    if missing or mismatched:
        details = [f"Missing: {path}" for path in missing] + [f"Changed: {path}" for path in mismatched]
        raise ValueError("Input manifest validation failed:\n" + "\n".join(details))
    print(f"Verified all {len(manifest['files'])} original local input files.\n")


def summarize(folder: Path, stages, split: int):
    print("Archived main results: fold 0; supplied settings 10, 30, 50, 70.")
    print("F1 is a 0-1 score, not accuracy. Smoke results are excluded.\n")
    print("Full-EC (level 4) micro-F1")
    table(["Method", *map(str, SPLITS)], [
        [name, *(f"{stages[(key, s)]['variants']['official']['level4']['micro_f1']:.6f}" for s in SPLITS)]
        for name, key, _ in METHODS
    ])
    print(f"\nFull-EC results, setting {split}")
    table(["Method", "Micro-F1", "Macro-F1", "Exact-set accuracy"], [
        [name, *(f"{stages[(key, split)]['variants']['official']['level4'][metric]:.6f}" for metric in ("micro_f1", "macro_f1", "subset_accuracy"))]
        for name, key, _ in METHODS
    ])
    print(f"\nEC-level scores, setting {split}")
    table(["Level", "MLP micro-F1", "MLP macro-F1", "DIAMOND micro-F1", "DIAMOND macro-F1"], [
        [level, *(f"{stages[(key, split)]['variants']['official'][f'level{level}'][metric]:.6f}" for key in ("H3_mlp", "B1_DIAMOND") for metric in ("micro_f1", "macro_f1"))]
        for level in (1, 2, 3, 4)
    ])
    print(f"\nFull-EC macro-F1 by training frequency, setting {split}")
    bins = stages[("H3_mlp", split)]["variants"]["official"]["level4"]["frequency_bins"]
    table(["Training proteins/EC", "Test-present ECs", "MLP macro-F1", "DIAMOND macro-F1"], [
        [label, bins[frequency]["n_labels"], *("n/a" if (value := stages[(key, split)]["variants"]["official"]["level4"]["frequency_bins"][frequency]["macro_f1"]) is None else f"{value:.6f}" for key in ("H3_mlp", "B1_DIAMOND"))]
        for label, frequency in (("1-4", "1-4"), ("5-19", "5-19"), ("20-99", "20-99"), ("100+", "N>=100"))
    ])
    audit = read_json(folder / "stage3_data_audit.json")
    print("\nFold-0 dataset and exact-duplicate audit")
    table(["Setting", "Train", "Test", "Test rows in train", "Overlap"], [
        [r["split"], r["train_rows"], r["test_rows"], r["leaked_rows"], f"{r['leaked_rows'] / r['test_rows']:.2%}"]
        for r in audit["per_split"]
    ])
    print("\nDIAMOND leads the saved full-EC comparisons. Rare labels remain harder.")
    print("Only fold 0 was modeled; all test EC labels occur in training.")
    print("Dataset sizes and label sets vary between settings. These are archived outputs;")
    print("this command does not reproduce model training or verify sequence-identity bounds.")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=Path, default=REPO / "results")
    parser.add_argument("--split", type=int, choices=SPLITS, default=70, help="Setting used for detailed tables (default: 70)")
    parser.add_argument("--check", action="store_true", help="Check all archived main CSV/JSON values and preserved artifact hashes")
    parser.add_argument("--check-data", action="store_true", help="Also hash-check the 60 original local inputs (requires local data)")
    parser.add_argument("--data-manifest", type=Path, default=REPO / "data/manifest.json")
    args = parser.parse_args(argv)
    try:
        stages = read_stages(args.results_dir)
        if args.check:
            check_saved_metrics(args.results_dir, stages)
        if args.check_data:
            check_data(args.data_manifest)
        summarize(args.results_dir, stages, args.split)
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
