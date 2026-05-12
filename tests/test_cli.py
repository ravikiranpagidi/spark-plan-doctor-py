from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from spark_plan_doctor.cli import main

from sample_plans import SAMPLE_PLAN


class CliTests(unittest.TestCase):
    def test_demo_command(self) -> None:
        output = io.StringIO()
        with redirect_stdout(output):
            code = main(["demo"])

        self.assertEqual(0, code)
        self.assertIn("demo_orders_plan", output.getvalue())

    def test_inspect_plan_file_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            plan_path = Path(tmp) / "plan.txt"
            plan_path.write_text(SAMPLE_PLAN, encoding="utf-8")
            output = io.StringIO()

            with redirect_stdout(output):
                code = main(["inspect-plan-file", str(plan_path), "--format", "json"])

        self.assertEqual(0, code)
        self.assertIn('"findings"', output.getvalue())


if __name__ == "__main__":
    unittest.main()
