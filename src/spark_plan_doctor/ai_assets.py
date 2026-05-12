from __future__ import annotations


def quote_identifier(name: str) -> str:
    return ".".join(f"`{part.replace('`', '``')}`" for part in name.split("."))


def default_ai_asset_sql(findings_table: str, runs_table: str | None = None, *, schema: str | None = None) -> list[str]:
    findings = quote_identifier(findings_table)
    schema_prefix = f"{quote_identifier(schema)}." if schema else ""
    statements = [
        f"""
CREATE OR REPLACE VIEW {schema_prefix}`v_spark_plan_findings_last_7_days` AS
SELECT
  created_at,
  job_name,
  plan_name,
  team,
  environment,
  rule_id,
  severity,
  title,
  recommendation,
  confidence,
  cost_impact
FROM {findings}
WHERE created_at >= current_timestamp() - INTERVAL 7 DAYS
""".strip(),
        f"""
CREATE OR REPLACE VIEW {schema_prefix}`v_spark_plan_top_risks` AS
SELECT
  job_name,
  plan_name,
  team,
  rule_id,
  title,
  severity,
  count(*) AS occurrences,
  max(created_at) AS last_seen_at
FROM {findings}
WHERE severity IN ('critical', 'warning')
GROUP BY job_name, plan_name, team, rule_id, title, severity
ORDER BY occurrences DESC, last_seen_at DESC
""".strip(),
    ]
    if runs_table:
        runs = quote_identifier(runs_table)
        statements.append(
            f"""
CREATE OR REPLACE VIEW {schema_prefix}`v_spark_plan_health_by_job` AS
SELECT
  job_name,
  team,
  count(*) AS inspected_runs,
  avg(score) AS avg_score,
  max(critical_count) AS max_critical_count,
  max(warning_count) AS max_warning_count,
  max(created_at) AS last_inspected_at
FROM {runs}
GROUP BY job_name, team
ORDER BY avg_score ASC, inspected_runs DESC
""".strip()
        )
    return statements


def install_ai_assets(spark, findings_table: str, runs_table: str | None = None, *, schema: str | None = None) -> list[str]:
    statements = default_ai_asset_sql(findings_table, runs_table, schema=schema)
    for statement in statements:
        spark.sql(statement)
    return statements
