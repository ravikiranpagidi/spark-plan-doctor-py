from spark_plan_doctor import SparkPlanDoctor


doctor = SparkPlanDoctor(
    spark=spark,
    findings_table="ops.spark_plan_doctor_findings",
    runs_table="ops.spark_plan_doctor_runs",
    artifact_path="dbfs:/mnt/ops/spark-plan-doctor",
)

df = (
    spark.table("bronze.orders")
    .join(spark.table("silver.customers"), "customer_id")
    .groupBy("order_date")
    .count()
)

report = doctor.inspect(
    df,
    plan_name="daily_orders_aggregation",
    job_name="daily_orders_job",
    team="data-engineering",
    write_delta=True,
    write_agent_bundle=True,
    prompt_policy="auto",
)

report.print_summary()
