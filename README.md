# spark-plan-doctor-py

AI-ready Spark execution plan diagnostics for PySpark, Delta tables, and assistant workflows.

`spark-plan-doctor-py` inspects Spark query plans before expensive work runs. It turns `explain("formatted")` output into structured findings, safe recommendations, Delta rows for ad hoc querying, and a clean agent prompt that can be pasted into Genie, Codex, Copilot, Claude, or another assistant.

It is not a logger and it does not execute the DataFrame. The default path is static plan inspection: no `count`, no `collect`, no write, and no table scan.

## Why This Is Different

Most Spark tools either profile a completed job or visualize a plan. This project focuses on plan hygiene and AI handoff:

- cheap static inspection by default
- rule-based findings with evidence and recommendations
- optional Delta output table for trend analysis
- compact prompt for quick AI assistant copy/paste
- agent bundle with `summary.md`, `prompt.md`, `plan.txt`, and `findings.json`
- Genie-friendly SQL views for repeated questions
- pure Python models, with PySpark used only when you inspect a real DataFrame

## Install

From GitHub while the project is young:

```bash
pip install git+https://github.com/ravikiranpagidi/spark-plan-doctor-py.git
```

From a clone:

```bash
git clone https://github.com/ravikiranpagidi/spark-plan-doctor-py.git
cd spark-plan-doctor-py
PYTHONPATH=src python -m unittest discover -s tests
```

## Quick Start

In Databricks or any PySpark environment:

```python
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
```

## Inspect A Saved Plan

Use this for CI, examples, or plans copied from Spark UI:

```python
from spark_plan_doctor import inspect_plan_text


report = inspect_plan_text(
    plan_text=open("plans/orders_plan.txt", encoding="utf-8").read(),
    plan_name="orders_plan",
)

print(report.summary())
print(report.to_agent_prompt())
```

## Delta Tables For Ad Hoc Queries

The library can write two narrow Delta tables:

- `ops.spark_plan_doctor_runs`
- `ops.spark_plan_doctor_findings`

Example question:

```sql
SELECT job_name, rule_id, title, count(*) AS occurrences
FROM ops.spark_plan_doctor_findings
WHERE created_at >= current_date() - INTERVAL 7 DAYS
GROUP BY job_name, rule_id, title
ORDER BY occurrences DESC;
```

This is the main design goal: the output becomes a clean source for Genie, SQL dashboards, notebooks, or any AI assistant that can query Delta tables.

## Agent Prompt

For non-trivial findings, print a compact prompt directly in notebook or job logs:

```python
report.print_prompt(policy="auto")
```

Example:

```text
I am optimizing a PySpark query.

Plan name: daily_orders_aggregation
Job name: daily_orders_job

Spark Plan Doctor found:
- SPD001 warning: Large shuffle detected
- SPD004 warning: No partition pruning signal found

Please suggest the smallest safe PySpark improvement.
Do not change business logic. Explain risk before suggesting code.
```

## Genie-Ready Assets

Install optional SQL views that make questions easier for Genie or any SQL-aware assistant:

```python
doctor.install_ai_assets(schema="ops")
```

It creates views such as:

- `ops.v_spark_plan_findings_last_7_days`
- `ops.v_spark_plan_top_risks`
- `ops.v_spark_plan_health_by_job`

See [docs/ai-ready-delta.md](docs/ai-ready-delta.md).

## Rules

| Rule | What it checks |
| --- | --- |
| `SPD001` | Large shuffle / many `Exchange` operators |
| `SPD002` | Cartesian product or risky nested-loop join |
| `SPD003` | Sort-merge join where broadcast may be worth checking |
| `SPD004` | Missing partition-pruning signal |
| `SPD005` | Python UDF / Python evaluation in the plan |
| `SPD006` | Repeated scan of the same relation |
| `SPD007` | Full table scan signal |
| `SPD008` | Many sort stages |
| `SPD009` | Adaptive Query Execution disabled |
| `SPD010` | Plan hash changed from a baseline |
| `SPD011` | Many shuffle exchanges in one plan |
| `SPD012` | Very wide projection |

Rules are intentionally explainable. The project should suggest checks and safe next steps, not rewrite production queries behind your back.

## CLI

```bash
spark-plan-doctor demo
spark-plan-doctor inspect-plan-file plans/orders_plan.txt --format text
spark-plan-doctor inspect-plan-file plans/orders_plan.txt --format json
```

Fail a CI step if a saved plan has critical findings:

```bash
spark-plan-doctor inspect-plan-file plans/orders_plan.txt --fail-on critical
```

## Contributor-Friendly Areas

- add new rules for common Spark plan smells
- improve plan parsing across Spark versions
- add SARIF output for GitHub code scanning
- add Databricks Asset Bundle examples
- add more Genie-friendly SQL views
- add plan baseline diff examples for pull requests

## Compatibility Note

This project works with Apache Spark, PySpark, Delta Lake, and Databricks environments. It is independent and is not affiliated with, endorsed by, or sponsored by Databricks.

## License

MIT
