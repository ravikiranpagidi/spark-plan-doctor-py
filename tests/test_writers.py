from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from spark_plan_doctor.models import Finding, PlanReport, PlanSnapshot
from spark_plan_doctor.writers import write_agent_bundle


class WriterTests(unittest.TestCase):
    def test_write_agent_bundle(self) -> None:
        snapshot = PlanSnapshot(run_id="abc", plan_name="orders", plan_text="plan", plan_hash="hash")
        report = PlanReport(
            snapshot=snapshot,
            findings=(Finding(rule_id="SPD001", severity="warning", title="Shuffle", message="Exchange"),),
        )

        with tempfile.TemporaryDirectory() as tmp:
            written = write_agent_bundle(report, tmp)

            self.assertTrue(Path(written["prompt.md"]).exists())
            self.assertIn("agent_context.md", written)


if __name__ == "__main__":
    unittest.main()
