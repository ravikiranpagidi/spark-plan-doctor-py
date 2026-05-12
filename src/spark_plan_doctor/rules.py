from __future__ import annotations

from spark_plan_doctor.config import PlanDoctorConfig
from spark_plan_doctor.models import Finding, PlanSnapshot
from spark_plan_doctor.parser import parse_plan_features


def analyze_plan(
    snapshot: PlanSnapshot,
    config: PlanDoctorConfig | None = None,
    *,
    baseline_hash: str = "",
    spark_conf: dict[str, str] | None = None,
) -> tuple[Finding, ...]:
    config = config or PlanDoctorConfig()
    spark_conf = spark_conf or {}
    features = parse_plan_features(snapshot.plan_text)
    findings: list[Finding] = []

    if features.exchange_count >= config.warning_exchange_count:
        severity = "critical" if features.exchange_count >= config.critical_exchange_count else "warning"
        findings.append(
            Finding(
                rule_id="SPD001",
                severity=severity,
                title="Large shuffle detected",
                message=f"The plan contains {features.exchange_count} Exchange operator(s).",
                evidence=f"Exchange count: {features.exchange_count}",
                recommendation="Check filters, join keys, partitioning, and shuffle partition settings before running this at scale.",
                confidence="high",
                cost_impact="high" if severity == "critical" else "medium",
                agent_summary="The query may spend significant time and cost in shuffle.",
            )
        )

    if features.cartesian_count:
        findings.append(
            Finding(
                rule_id="SPD002",
                severity="critical",
                title="Cartesian or nested-loop join signal",
                message="The plan contains a CartesianProduct or BroadcastNestedLoopJoin operator.",
                evidence=f"Risky join operator count: {features.cartesian_count}",
                recommendation="Confirm the join condition is correct and intentional. A missing join predicate can explode row counts.",
                confidence="high",
                cost_impact="high",
                agent_summary="The join may multiply rows unexpectedly.",
            )
        )

    if features.sort_merge_join_count and not features.broadcast_hash_join_count:
        findings.append(
            Finding(
                rule_id="SPD003",
                severity="info",
                title="Sort-merge join worth reviewing",
                message=f"The plan uses {features.sort_merge_join_count} SortMergeJoin operator(s).",
                evidence="SortMergeJoin present, BroadcastHashJoin not present.",
                recommendation="If one side is small enough, check whether broadcast is possible and whether table statistics are current.",
                confidence="medium",
                cost_impact="medium",
                agent_summary="A broadcast join may be cheaper if one side is genuinely small.",
            )
        )

    if features.no_partition_pruning_signal:
        findings.append(
            Finding(
                rule_id="SPD004",
                severity="warning",
                title="No partition-pruning signal found",
                message="At least one scan shows empty PartitionFilters.",
                evidence="PartitionFilters: []",
                recommendation="If the source is partitioned, push selective filters before joins and aggregations.",
                confidence="medium",
                cost_impact="medium",
                agent_summary="The plan may read more partitions than needed.",
            )
        )

    if features.python_eval_count:
        findings.append(
            Finding(
                rule_id="SPD005",
                severity="warning",
                title="Python UDF in plan",
                message="The plan contains Python evaluation operators.",
                evidence=f"Python eval count: {features.python_eval_count}",
                recommendation="Use native Spark SQL functions where possible, especially before joins or aggregations.",
                confidence="high",
                cost_impact="medium",
                agent_summary="Python UDFs can block Catalyst optimization and slow execution.",
            )
        )

    for relation, count in features.repeated_scans:
        if count >= config.repeated_scan_threshold:
            findings.append(
                Finding(
                    rule_id="SPD006",
                    severity="warning",
                    title="Repeated scan of the same relation",
                    message=f"The plan scans {relation} {count} times.",
                    evidence=f"{relation}: {count} scans",
                    recommendation="Check whether a common intermediate should be reused, materialized, or cached intentionally.",
                    confidence="medium",
                    cost_impact="medium",
                    agent_summary="The same source may be read repeatedly in one plan.",
                )
            )

    if features.full_scan_signal:
        findings.append(
            Finding(
                rule_id="SPD007",
                severity="info",
                title="Full scan signal",
                message="A scan shows both empty partition filters and empty pushed filters.",
                evidence="PartitionFilters: [], PushedFilters: []",
                recommendation="Confirm the query really needs a broad read. Add selective filters early if possible.",
                confidence="medium",
                cost_impact="medium",
                agent_summary="The plan may be doing a broad read.",
            )
        )

    if features.sort_count >= config.warning_sort_count:
        findings.append(
            Finding(
                rule_id="SPD008",
                severity="warning",
                title="Many sort stages",
                message=f"The plan contains {features.sort_count} Sort operator(s).",
                evidence=f"Sort count: {features.sort_count}",
                recommendation="Review ordering, window functions, and join strategy. Sorts are often expensive at scale.",
                confidence="medium",
                cost_impact="medium",
                agent_summary="The query may spend extra time sorting data.",
            )
        )

    aqe_value = spark_conf.get("spark.sql.adaptive.enabled", "").lower()
    if aqe_value == "false":
        findings.append(
            Finding(
                rule_id="SPD009",
                severity="warning",
                title="Adaptive Query Execution disabled",
                message="spark.sql.adaptive.enabled is false.",
                evidence="spark.sql.adaptive.enabled=false",
                recommendation="Enable AQE for most modern Spark workloads unless the job has a known reason to disable it.",
                confidence="high",
                cost_impact="medium",
                agent_summary="AQE can reduce shuffle, skew, and poor join choices at runtime.",
            )
        )

    if baseline_hash and baseline_hash != snapshot.plan_hash:
        findings.append(
            Finding(
                rule_id="SPD010",
                severity="warning",
                title="Plan hash changed from baseline",
                message="The current plan hash differs from the provided baseline.",
                evidence=f"baseline={baseline_hash}, current={snapshot.plan_hash}",
                recommendation="Compare plan diffs before merging if this query is cost-sensitive.",
                confidence="high",
                cost_impact="unknown",
                agent_summary="The query plan changed and may need review.",
            )
        )

    if features.exchange_count >= config.critical_exchange_count:
        findings.append(
            Finding(
                rule_id="SPD011",
                severity="warning",
                title="Many shuffle exchanges in one plan",
                message="The plan has enough Exchange operators to deserve deeper review.",
                evidence=f"Exchange count: {features.exchange_count}",
                recommendation="Break the plan into stages and check whether any joins or aggregations can be filtered earlier.",
                confidence="high",
                cost_impact="high",
                agent_summary="Multiple shuffles may compound runtime and cost.",
            )
        )

    if features.max_project_columns >= config.warning_project_columns:
        findings.append(
            Finding(
                rule_id="SPD012",
                severity="info",
                title="Very wide projection",
                message=f"A Project node references about {features.max_project_columns} columns.",
                evidence=f"Project column count: {features.max_project_columns}",
                recommendation="Select only columns needed downstream, especially before joins and writes.",
                confidence="medium",
                cost_impact="low",
                agent_summary="A wide projection can increase memory pressure and network I/O.",
            )
        )

    return tuple(findings)
