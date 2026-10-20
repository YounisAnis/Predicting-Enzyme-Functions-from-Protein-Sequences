"""Reader regression tests; no GPU, model downloads, or original-data writes."""

import hashlib
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("ecpaths_under_test", ROOT / "src" / "ecpaths.py")
P = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(P)


class PathsTest(unittest.TestCase):
    def test_paths_match_the_archived_names(self):
        self.assertEqual(P.train_csv(50, 2), P.ROOT / "data/splits/split50/split50_train_split_2.csv")
        self.assertEqual(P.emb_file(70, 0, "train").name, "esm2_650M_split70_fold0_train.npy")
        self.assertEqual(P.ids_file(70, 0, "test").name, "esm2_650M_split70_fold0_test.ids.txt")
        self.assertEqual(P.clean_weight("gmm").name, "gmm_ensumble.pkl")

    def test_root_discovery_is_independent_of_working_directory(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(P.find_project_root(ROOT / "notebooks"), ROOT)

    def test_explicit_root_requires_a_marker(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(os.environ, {"ECPRED_ROOT": directory}):
                with self.assertRaisesRegex(FileNotFoundError, "marker"):
                    P.find_project_root()
                Path(directory, ".ecpred_root").touch()
                self.assertEqual(P.find_project_root(), Path(directory).resolve())

    def test_invalid_paths_fail(self):
        for call in (lambda: P.train_csv(20), lambda: P.test_csv(10, 5),
                     lambda: P.emb_file(10, 0, "validation"), lambda: P.result_file("../metrics.json")):
            with self.assertRaises(ValueError):
                call()


class ReaderTest(unittest.TestCase):
    def read_bytes(self, payload):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "fixture.csv")
            path.write_bytes(payload)
            before = hashlib.sha256(path.read_bytes()).digest()
            frame = P.read_split_csv(path)
            self.assertEqual(hashlib.sha256(path.read_bytes()).digest(), before)
            return frame

    def test_normal_crlf_and_multilabel_fields_are_preserved(self):
        frame = self.read_bytes(b"Entry\tEC number\tSequence\r\nQ1\t1.1.1.1;2.2.2.2\tACDX\r\n")
        self.assertEqual(list(frame.columns), ["Entry", "EC number", "Sequence"])
        self.assertEqual(frame.iloc[0].tolist(), ["Q1", "1.1.1.1;2.2.2.2", "ACDX"])

    def test_whole_line_quotes(self):
        frame = self.read_bytes(b'"ID\tEC\tSequences"\r\n"Q2\t3.5.4.9\tMALL"\r\n')
        self.assertEqual(frame.iloc[0].tolist(), ["Q2", "3.5.4.9", "MALL"])

    def test_literal_tab_export_with_whole_line_quotes(self):
        frame = self.read_bytes(b'"ID\\tEC\\tSequences"\n"Q3\\t1.5.1.5\\tACD"\n')
        self.assertEqual(frame.iloc[0].tolist(), ["Q3", "1.5.1.5", "ACD"])

    def test_standard_individually_quoted_fields(self):
        frame = self.read_bytes(b'"ID"\t"EC"\t"Sequences"\n"Q4"\t"1.1.1.1"\t"AAA"\n')
        self.assertEqual(frame.iloc[0].tolist(), ["Q4", "1.1.1.1", "AAA"])

    def test_split50_extra_header_field_is_repaired_only_in_memory(self):
        frame = self.read_bytes(b"Entry\tEC\tnumber\tSequence\r\nQ5\t2.7.11.1\tACD\r\n")
        self.assertEqual(list(frame.columns), ["Entry", "EC number", "Sequence"])
        self.assertEqual(frame.iloc[0].tolist(), ["Q5", "2.7.11.1", "ACD"])

    def test_missing_value_is_not_converted_into_nan(self):
        frame = self.read_bytes(b"ID\tEC\tSequences\nNA\t\tAAA\n")
        self.assertEqual(frame.iloc[0].tolist(), ["NA", "", "AAA"])

    def test_unexpected_column_counts_fail_with_line_number(self):
        for payload, expected in ((b"ID\tEC\nQ\t1.1.1.1\n", ":1:"),
                                  (b"ID\tEC\tSequences\nQ\t1.1.1.1\tAAA\textra\n", ":2:")):
            with self.assertRaisesRegex(ValueError, expected):
                self.read_bytes(payload)


if __name__ == "__main__":
    unittest.main()
