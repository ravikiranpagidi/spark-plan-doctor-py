from __future__ import annotations

import json
import unittest

from spark_plan_doctor.models import Finding, PlanReport, PlanSnapshot


class ModelTests(unittest.TestCase):
    def test_report_rows_and_prompt(self) -> None:
        snapshot = PlanSnapshot(run_id="abc", plan_name="orders", plan_text="plan", plan_hash="hash")
        report = PlanReport(
            snapshot=snapshot,
            findings=(
                Finding(
                    rule_id="SPD001",
                    severity="warning",
                    title="Large shuffle",
                    message="Exchange count: 2",
                    recommendation="Review joins.",
                ),
            ),
        )

        self.assertEqual("warning", report.status)
        self.assertLess(report.score, 100)
        self.assertTrue(report.should_print_prompt("auto"))
        self.assertIn("SPD001", report.to_agent_prompt())
        self.assertEqual(1, len(report.to_finding_rows()))
        self.assertTrue(json.loads(report.to_run_row()["payload_json"]))

    def test_healthy_report(self) -> None:
        snapshot = PlanSnapshot(run_id="abc", plan_name="orders", plan_text="plan", plan_hash="hash")
        report = PlanReport(snapshot=snapshot)

        self.assertEqual("healthy", report.status)
        self.assertEqual(100, report.score)
        self.assertFalse(report.should_print_prompt("auto"))


if __name__ == "__main__":
    unittest.main()
