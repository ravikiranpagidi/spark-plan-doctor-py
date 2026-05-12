from __future__ import annotations

import json
from pathlib import Path

from spark_plan_doctor.models import PlanReport


def write_delta_report(
    spark,
    report: PlanReport,
    *,
    findings_table: str | None = None,
    runs_table: str | None = None,
    mode: str = "append",
) -> None:
    findings_table = findings_table or report.findings_table
    runs_table = runs_table or report.runs_table
    if not findings_table and not runs_table:
        raise ValueError("findings_table or runs_table is required")

    if runs_table:
        spark.createDataFrame([report.to_run_row()]).write.format("delta").mode(mode).saveAsTable(runs_table)

    if findings_table and report.findings:
        spark.createDataFrame(report.to_finding_rows()).write.format("delta").mode(mode).saveAsTable(findings_table)


def resolve_artifact_path(path: str) -> Path:
    if path.startswith("dbfs:/"):
        local = Path("/dbfs") / path.removeprefix("dbfs:/").lstrip("/")
        if not local.parent.exists():
            raise RuntimeError(
                "dbfs:/ artifact paths require a Databricks filesystem mount at /dbfs. "
                "Use a local path in tests or write through Spark/DBFS utilities in a notebook."
            )
        return local
    return Path(path)


def write_agent_bundle(report: PlanReport, artifact_path: str) -> dict[str, str]:
    base_path = resolve_artifact_path(artifact_path)
    run_path = base_path / _safe_name(report.snapshot.plan_name) / report.snapshot.run_id
    run_path.mkdir(parents=True, exist_ok=True)

    files = {
        "summary.md": report.summary(),
        "prompt.md": report.to_agent_prompt(),
        "plan.txt": report.snapshot.plan_text,
        "findings.json": json.dumps([finding.to_dict() for finding in report.findings], indent=2, sort_keys=True),
        "report.json": report.to_json(include_plan_text=False),
        "agent_context.md": _agent_context(report),
    }
    written: dict[str, str] = {}
    for name, content in files.items():
        target = run_path / name
        target.write_text(content + "\n", encoding="utf-8")
        written[name] = str(target)
    return written


def _safe_name(value: str) -> str:
    keep = []
    for char in value.lower():
        if char.isalnum() or char in {"-", "_"}:
            keep.append(char)
        elif char in {" ", ".", "/"}:
            keep.append("-")
    cleaned = "".join(keep).strip("-")
    return cleaned or "spark-plan"


def _agent_context(report: PlanReport) -> str:
    return "\n\n".join(
        [
            "# Spark Plan Doctor Agent Context",
            "## Summary",
            report.summary(),
            "## Prompt",
            report.to_agent_prompt(),
            "## Plan Text",
            "```text\n" + report.snapshot.plan_text.strip() + "\n```",
        ]
    )
