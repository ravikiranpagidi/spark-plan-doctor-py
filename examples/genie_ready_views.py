from spark_plan_doctor import SparkPlanDoctor


doctor = SparkPlanDoctor(
    spark=spark,
    findings_table="ops.spark_plan_doctor_findings",
    runs_table="ops.spark_plan_doctor_runs",
)

doctor.install_ai_assets(schema="ops")
