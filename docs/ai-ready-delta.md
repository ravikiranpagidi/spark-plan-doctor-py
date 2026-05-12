# AI-Ready Delta Output

`spark-plan-doctor-py` is designed to write structured plan findings into Delta tables. The goal is not to store raw logs. The goal is to create a clean fact layer that Genie, dashboards, notebooks, and coding assistants can query.

## Recommended Tables

Use one runs table and one findings table:

```text
ops.spark_plan_doctor_runs
ops.spark_plan_doctor_findings
```

The runs table stores one row per inspected plan. The findings table stores one row per rule finding.

## Example Questions

```sql
SELECT job_name, rule_id, title, count(*) AS occurrences
FROM ops.spark_plan_doctor_findings
WHERE created_at >= current_date() - INTERVAL 7 DAYS
GROUP BY job_name, rule_id, title
ORDER BY occurrences DESC;
```

```sql
SELECT team, severity, count(*) AS findings
FROM ops.spark_plan_doctor_findings
WHERE created_at >= current_date() - INTERVAL 30 DAYS
GROUP BY team, severity;
```

```sql
SELECT job_name, avg(score) AS avg_score, max(warning_count) AS max_warnings
FROM ops.spark_plan_doctor_runs
GROUP BY job_name
ORDER BY avg_score ASC;
```

## Genie-Friendly Views

The helper creates a few simple views:

```python
doctor.install_ai_assets(schema="ops")
```

This does not create a Genie space for you. It prepares tables and views that are easier to add to a Genie space, SQL dashboard, notebook, or other assistant workflow.

Suggested Genie questions:

- Which Spark plans had critical or warning findings this week?
- Which jobs repeatedly show large shuffle warnings?
- Which teams have the most Spark plan risks?
- Which jobs should we review first to reduce cost?
- Show Spark plans where partition pruning is missing.

## Notes

Add table and column comments in Unity Catalog for best assistant behavior. Keep the findings table narrow and boring. AI assistants work better when the data model is obvious.
