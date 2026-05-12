from __future__ import annotations

import unittest

from spark_plan_doctor.models import PlanSnapshot
from spark_plan_doctor.plan import hash_plan
from spark_plan_doctor.rules import analyze_plan

from sample_plans import CARTESIAN_PLAN, SAMPLE_PLAN


class RuleTests(unittest.TestCase):
    def test_sample_plan_findings(self) -> None:
        snapshot = PlanSnapshot(
            run_id="1",
            plan_name="orders",
            plan_text=SAMPLE_PLAN,
            plan_hash=hash_plan(SAMPLE_PLAN),
        )

        findings = analyze_plan(snapshot)
        rule_ids = {finding.rule_id for finding in findings}

        self.assertIn("SPD001", rule_ids)
        self.assertIn("SPD003", rule_ids)
        self.assertIn("SPD004", rule_ids)
        self.assertIn("SPD005", rule_ids)

    def test_cartesian_is_critical(self) -> None:
        snapshot = PlanSnapshot(
            run_id="1",
            plan_name="cartesian",
            plan_text=CARTESIAN_PLAN,
            plan_hash=hash_plan(CARTESIAN_PLAN),
        )

        findings = analyze_plan(snapshot)

        self.assertEqual("critical", next(f.severity for f in findings if f.rule_id == "SPD002"))

    def test_aqe_disabled(self) -> None:
        snapshot = PlanSnapshot(run_id="1", plan_name="p", plan_text="== Physical Plan ==", plan_hash="abc")

        findings = analyze_plan(snapshot, spark_conf={"spark.sql.adaptive.enabled": "false"})

        self.assertIn("SPD009", {finding.rule_id for finding in findings})

    def test_baseline_hash_change(self) -> None:
        snapshot = PlanSnapshot(run_id="1", plan_name="p", plan_text="plan", plan_hash="current")

        findings = analyze_plan(snapshot, baseline_hash="old")

        self.assertIn("SPD010", {finding.rule_id for finding in findings})


if __name__ == "__main__":
    unittest.main()
