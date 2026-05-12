from __future__ import annotations

import unittest

from spark_plan_doctor import SparkPlanDoctor, inspect_plan_text

from fakes import FakeDataFrame, FakeSpark
from sample_plans import SAMPLE_PLAN


class DoctorTests(unittest.TestCase):
    def test_inspect_plan_text(self) -> None:
        report = inspect_plan_text(SAMPLE_PLAN, plan_name="orders", prompt_policy="never")

        self.assertEqual("orders", report.snapshot.plan_name)
        self.assertTrue(report.findings)

    def test_inspect_dataframe_uses_explain(self) -> None:
        doctor = SparkPlanDoctor(spark=FakeSpark())

        report = doctor.inspect(FakeDataFrame(SAMPLE_PLAN), plan_name="df_plan", prompt_policy="never")

        self.assertEqual("df_plan", report.snapshot.plan_name)
        self.assertIn("Exchange", report.snapshot.plan_text)

    def test_write_delta_uses_both_tables(self) -> None:
        spark = FakeSpark()
        doctor = SparkPlanDoctor(
            spark=spark,
            findings_table="ops.spark_plan_doctor_findings",
            runs_table="ops.spark_plan_doctor_runs",
        )

        doctor.inspect(plan_text=SAMPLE_PLAN, plan_name="orders", write_delta=True, prompt_policy="never")

        self.assertEqual(2, len(spark.created))
        self.assertEqual("ops.spark_plan_doctor_runs", spark.created[0].write.saved_table)
        self.assertEqual("ops.spark_plan_doctor_findings", spark.created[1].write.saved_table)

    def test_install_ai_assets(self) -> None:
        spark = FakeSpark()
        doctor = SparkPlanDoctor(
            spark=spark,
            findings_table="ops.spark_plan_doctor_findings",
            runs_table="ops.spark_plan_doctor_runs",
        )

        statements = doctor.install_ai_assets(schema="ops")

        self.assertEqual(3, len(statements))
        self.assertEqual(3, len(spark.queries))


if __name__ == "__main__":
    unittest.main()
