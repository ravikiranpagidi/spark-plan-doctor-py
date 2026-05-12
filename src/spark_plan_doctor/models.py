from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


SEVERITY_RANK = {"healthy": 0, "info": 1, "warning": 2, "critical": 3}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(frozen=True)
class Finding:
    rule_id: str
    severity: str
    title: str
    message: str
    evidence: str = ""
    recommendation: str = ""
    confidence: str = "medium"
    cost_impact: str = "unknown"
    agent_summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "severity": self.severity,
            "title": self.title,
            "message": self.message,
            "evidence": self.evidence,
            "recommendation": self.recommendation,
            "confidence": self.confidence,
            "cost_impact": self.cost_impact,
            "agent_summary": self.agent_summary,
        }


@dataclass(frozen=True)
class PlanSnapshot:
    run_id: str
    plan_name: str
    plan_text: str
    plan_hash: str
    job_name: str = ""
    team: str = ""
    environment: str = ""
    spark_version: str = ""
    source: str = "dataframe"
    created_at: str = field(default_factory=utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "plan_name": self.plan_name,
            "job_name": self.job_name,
            "team": self.team,
            "environment": self.environment,
            "spark_version": self.spark_version,
            "source": self.source,
            "created_at": self.created_at,
            "plan_hash": self.plan_hash,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class PlanReport:
    snapshot: PlanSnapshot
    findings: tuple[Finding, ...] = ()
    artifact_uri: str = ""
    findings_table: str = ""
    runs_table: str = ""

    @property
    def status(self) -> str:
        if any(finding.severity == "critical" for finding in self.findings):
            return "critical"
        if any(finding.severity == "warning" for finding in self.findings):
            return "warning"
        if any(finding.severity == "info" for finding in self.findings):
            return "info"
        return "healthy"

    @property
    def score(self) -> int:
        penalty = 0
        for finding in self.findings:
            if finding.severity == "critical":
                penalty += 35
            elif finding.severity == "warning":
                penalty += 12
            elif finding.severity == "info":
                penalty += 4
        return max(0, 100 - penalty)

    def finding_counts(self) -> dict[str, int]:
        counts = {"critical": 0, "warning": 0, "info": 0}
        for finding in self.findings:
            counts[finding.severity] = counts.get(finding.severity, 0) + 1
        return counts

    def has_findings_at_or_above(self, severity: str) -> bool:
        threshold = SEVERITY_RANK[severity]
        return any(SEVERITY_RANK.get(finding.severity, 0) >= threshold for finding in self.findings)

    def summary(self) -> str:
        name = self.snapshot.plan_name
        base = f"{name}: {self.status}, score {self.score}/100, {len(self.findings)} finding(s)"
        if not self.findings:
            return base
        lines = [base, ""]
        for finding in self.findings:
            lines.append(f"[{finding.severity}] {finding.rule_id} {finding.title}")
            lines.append(finding.message)
            if finding.recommendation:
                lines.append(f"Recommendation: {finding.recommendation}")
            lines.append("")
        return "\n".join(lines).rstrip()

    def print_summary(self) -> None:
        print(self.summary())

    def to_dict(self, include_plan_text: bool = False) -> dict[str, Any]:
        payload = {
            "snapshot": self.snapshot.to_dict(),
            "status": self.status,
            "score": self.score,
            "finding_counts": self.finding_counts(),
            "artifact_uri": self.artifact_uri,
            "findings_table": self.findings_table,
            "runs_table": self.runs_table,
            "findings": [finding.to_dict() for finding in self.findings],
        }
        if include_plan_text:
            payload["plan_text"] = self.snapshot.plan_text
        return payload

    def to_json(self, include_plan_text: bool = False) -> str:
        return json.dumps(self.to_dict(include_plan_text=include_plan_text), indent=2, sort_keys=True)

    def to_run_row(self) -> dict[str, Any]:
        counts = self.finding_counts()
        return {
            "run_id": self.snapshot.run_id,
            "plan_name": self.snapshot.plan_name,
            "job_name": self.snapshot.job_name,
            "team": self.snapshot.team,
            "environment": self.snapshot.environment,
            "created_at": self.snapshot.created_at,
            "spark_version": self.snapshot.spark_version,
            "source": self.snapshot.source,
            "status": self.status,
            "score": self.score,
            "finding_count": len(self.findings),
            "critical_count": counts.get("critical", 0),
            "warning_count": counts.get("warning", 0),
            "info_count": counts.get("info", 0),
            "plan_hash": self.snapshot.plan_hash,
            "artifact_uri": self.artifact_uri,
            "payload_json": self.to_json(include_plan_text=False),
        }

    def to_finding_rows(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for finding in self.findings:
            rows.append(
                {
                    "run_id": self.snapshot.run_id,
                    "plan_name": self.snapshot.plan_name,
                    "job_name": self.snapshot.job_name,
                    "team": self.snapshot.team,
                    "environment": self.snapshot.environment,
                    "created_at": self.snapshot.created_at,
                    "plan_hash": self.snapshot.plan_hash,
                    "rule_id": finding.rule_id,
                    "severity": finding.severity,
                    "title": finding.title,
                    "message": finding.message,
                    "evidence": finding.evidence,
                    "recommendation": finding.recommendation,
                    "confidence": finding.confidence,
                    "cost_impact": finding.cost_impact,
                    "agent_summary": finding.agent_summary,
                }
            )
        return rows

    def should_print_prompt(self, policy: str = "auto") -> bool:
        if policy == "never":
            return False
        if policy == "always":
            return bool(self.findings)
        complex_rule_ids = {"SPD001", "SPD002", "SPD005", "SPD010", "SPD011"}
        has_complex_rule = any(finding.rule_id in complex_rule_ids for finding in self.findings)
        has_critical = any(finding.severity == "critical" for finding in self.findings)
        warning_count = sum(1 for finding in self.findings if finding.severity == "warning")
        if policy == "complex-only":
            return has_critical or has_complex_rule
        if policy == "auto":
            return has_critical or warning_count >= 2 or has_complex_rule
        raise ValueError("policy must be never, always, auto, or complex-only")

    def to_agent_prompt(self) -> str:
        lines = [
            "I am optimizing a PySpark or Spark SQL query.",
            "",
            f"Plan name: {self.snapshot.plan_name}",
        ]
        if self.snapshot.job_name:
            lines.append(f"Job name: {self.snapshot.job_name}")
        if self.snapshot.team:
            lines.append(f"Team: {self.snapshot.team}")
        lines.extend(["", "Spark Plan Doctor found:"])
        if not self.findings:
            lines.append("- No findings were detected from static plan inspection.")
        for finding in self.findings:
            lines.append(f"- {finding.rule_id} {finding.severity}: {finding.title}")
            if finding.evidence:
                lines.append(f"  Evidence: {finding.evidence}")
            if finding.recommendation:
                lines.append(f"  Recommendation: {finding.recommendation}")
        lines.extend(
            [
                "",
                "Please suggest the smallest safe improvement.",
                "Do not change business logic.",
                "Call out any assumption before proposing code.",
            ]
        )
        return "\n".join(lines)

    def print_prompt(self, policy: str = "auto") -> None:
        if self.should_print_prompt(policy):
            print(self.to_agent_prompt())
