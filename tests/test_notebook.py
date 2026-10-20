"""Lightweight notebook checks that do not run training or download models."""

import ast
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = json.loads((ROOT / "notebooks" / "EC_pipeline.ipynb").read_text(encoding="utf-8"))


class NotebookTest(unittest.TestCase):
    def test_code_cells_compile_and_saved_execution_is_cleared(self):
        self.assertNotIn("colab", NOTEBOOK["metadata"])
        for index, cell in enumerate(NOTEBOOK["cells"]):
            self.assertEqual(cell["metadata"], {})
            if cell["cell_type"] == "code":
                ast.parse("".join(cell["source"]), filename=f"cell-{index}")
                self.assertIsNone(cell["execution_count"])
                self.assertEqual(cell["outputs"], [])

    def test_frequency_and_level_filters_select_actual_head_rows(self):
        import pandas as pd

        rows = []
        for head, value in (("head_a", 0.4), ("head_b", 0.7)):
            for level in range(1, 5):
                for metric in ("micro_f1", "macro_f1"):
                    rows.append(dict(head=head, value=value, metric=metric, level=level,
                                     split=70, test_variant="official"))
            for name in ("N>=100", "20-99", "5-19", "1-4"):
                rows.append(dict(head=head, value=value, metric=f"macro_f1[{name}]", level=4,
                                 split=70, test_variant="official"))
        tree = ast.parse("".join(NOTEBOOK["cells"][47]["source"]))
        expressions = {}
        for node in ast.walk(tree):
            if not isinstance(node, ast.Assign):
                continue
            names = {name.id for name in ast.walk(node.value) if isinstance(name, ast.Name)}
            if "d3s" in names and any(isinstance(t, ast.Name) and t.id == "v" for t in node.targets):
                expressions["frequency"] = compile(ast.Expression(node.value), "figure-3-filter", "eval")
            if "d4s" in names and any(isinstance(t, ast.Name) and t.id == "g" for t in node.targets):
                expressions["levels"] = compile(ast.Expression(node.value), "figure-4-filter", "eval")
        self.assertEqual(set(expressions), {"frequency", "levels"})
        frame = pd.DataFrame(rows)
        for head, expected in (("head_a", 0.4), ("head_b", 0.7)):
            namespace = {"d3s": frame, "d4s": frame, "h": head, "b": "1-4", "met": "micro_f1"}
            frequency = eval(expressions["frequency"], {}, namespace)
            levels = eval(expressions["levels"], {}, namespace)
            self.assertEqual(frequency.tolist(), [expected])
            self.assertEqual(levels["level"].tolist(), [1, 2, 3, 4])
            self.assertEqual(levels["value"].tolist(), [expected] * 4)


if __name__ == "__main__":
    unittest.main()
