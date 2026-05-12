from __future__ import annotations

from dataclasses import replace
from typing import Any

from spark_plan_doctor.ai_assets import install_ai_assets
from spark_plan_doctor.config import PlanDoctorConfig
from spark_plan_doctor.models import PlanReport, PlanSnapshot
from spark_plan_doctor.plan import extract_plan_text, get_spark_conf, get_spark_version, hash_plan, make_run_id
from spark_plan_doctor.redact import redact_mapping, redact_text
from spark_plan_doctor.rules import analyze_plan
from spark_plan_doctor.writers import write_agent_bundle, write_delta_report


class SparkPlanDoctor:
    def __init__(
        self,
        *,
        spark: Any | None = None,
        findings_table: str = "",
        runs_table: str = "",
        artifact_path: str = "",
        config: PlanDoctorConfig | None = None,
    ) -> None:
        self.spark = spark
        self.findings_table = findings_table
        self.runs_table = runs_table
        self.artifact_path = artifact_path
        self.config = config or PlanDoctorConfig()

    def inspect(
        self,
        df: Any | None = None,
        *,
        plan_text: str | None = None,
        plan_name: str = "spark_plan",
        job_name: str = "",
        team: str = "",
        environment: str = "",
        source: str = "dataframe",
        baseline_hash: str = "",
        write_delta: bool = False,
        write_agent_bundle: bool = False,
        prompt_policy: str | None = None,
    ) -> PlanReport:
        if plan_text is None:
            if df is None:
                raise ValueError("df or plan_text is required")
            plan_text = extract_plan_text(df)
        if self.config.redact_output:
            plan_text = redact_text(plan_text)

        spark_conf = redact_mapping(get_spark_conf(self.spark)) if self.config.redact_output else get_spark_conf(self.spark)
        snapshot = PlanSnapshot(
            run_id=make_run_id(),
            plan_name=plan_name,
            job_name=job_name,
            team=team,
            environment=environment,
            spark_version=get_spark_version(self.spark),
            source=source,
            plan_text=plan_text,
            plan_hash=hash_plan(plan_text),
            metadata={"spark_conf": spark_conf},
        )
        findings = analyze_plan(snapshot, self.config, baseline_hash=baseline_hash, spark_conf=spark_conf)
        report = PlanReport(
            snapshot=snapshot,
            findings=findings,
            findings_table=self.findings_table,
            runs_table=self.runs_table,
        )

        if write_agent_bundle:
            if not self.artifact_path:
                raise ValueError("artifact_path is required when write_agent_bundle=True")
            written = write_agent_bundle(report, self.artifact_path)
            report = replace(report, artifact_uri=written.get("agent_context.md", ""))

        if write_delta:
            if self.spark is None:
                raise ValueError("spark is required when write_delta=True")
            write_delta_report(
                self.spark,
                report,
                findings_table=self.findings_table,
                runs_table=self.runs_table,
            )

        policy = prompt_policy or self.config.default_prompt_policy
        report.print_prompt(policy)
        return report

    def inspect_sql(self, sql: str, **kwargs: Any) -> PlanReport:
        if self.spark is None:
            raise ValueError("spark is required for inspect_sql")
        df = self.spark.sql(sql)
        return self.inspect(df, source="sql", **kwargs)

    def install_ai_assets(self, *, schema: str | None = None) -> list[str]:
        if self.spark is None:
            raise ValueError("spark is required to install AI assets")
        if not self.findings_table:
            raise ValueError("findings_table is required to install AI assets")
        return install_ai_assets(
            self.spark,
            findings_table=self.findings_table,
            runs_table=self.runs_table or None,
            schema=schema,
        )


def inspect_df(df: Any, **kwargs: Any) -> PlanReport:
    spark = kwargs.pop("spark", None)
    return SparkPlanDoctor(spark=spark).inspect(df, **kwargs)


def inspect_plan_text(plan_text: str, **kwargs: Any) -> PlanReport:
    return SparkPlanDoctor().inspect(plan_text=plan_text, source="plan_text", **kwargs)
