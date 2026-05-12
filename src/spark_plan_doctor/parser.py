from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass


@dataclass(frozen=True)
class PlanFeatures:
    exchange_count: int
    sort_count: int
    cartesian_count: int
    python_eval_count: int
    sort_merge_join_count: int
    broadcast_hash_join_count: int
    scan_count: int
    repeated_scans: tuple[tuple[str, int], ...]
    no_partition_pruning_signal: bool
    full_scan_signal: bool
    max_project_columns: int
    adaptive_plan_present: bool


def _count(pattern: str, text: str, flags: int = re.IGNORECASE) -> int:
    return len(re.findall(pattern, text, flags))


def _scan_names(plan_text: str) -> list[str]:
    names: list[str] = []
    for line in plan_text.splitlines():
        if "Scan" not in line:
            continue
        cleaned = line.strip()
        match = re.search(r"(?:FileScan|BatchScan|Scan)\s+([^\[\n]+)", cleaned)
        if match:
            names.append(" ".join(match.group(1).split()))
            continue
        relation_match = re.search(r"Relation\s+\[[^\]]+\]\s+([^\s,]+)", cleaned)
        if relation_match:
            names.append(relation_match.group(1))
    return names


def _max_project_columns(plan_text: str) -> int:
    max_count = 0
    for match in re.finditer(r"Project\s+\[([^\]]+)\]", plan_text, re.IGNORECASE):
        columns = [item.strip() for item in match.group(1).split(",") if item.strip()]
        max_count = max(max_count, len(columns))
    return max_count


def parse_plan_features(plan_text: str) -> PlanFeatures:
    scan_names = _scan_names(plan_text)
    scan_counter = Counter(scan_names)
    repeated_scans = tuple(
        sorted(
            ((name, count) for name, count in scan_counter.items() if count > 1),
            key=lambda item: (-item[1], item[0]),
        )
    )
    partition_filters_empty = "PartitionFilters: []" in plan_text
    pushed_filters_empty = "PushedFilters: []" in plan_text
    has_scan = bool(scan_names) or _count(r"\b(?:FileScan|BatchScan|Scan)\b", plan_text) > 0
    return PlanFeatures(
        exchange_count=_count(r"\bExchange\b", plan_text),
        sort_count=_count(r"\bSort\b", plan_text),
        cartesian_count=_count(r"\bCartesianProduct\b|\bBroadcastNestedLoopJoin\b", plan_text),
        python_eval_count=_count(r"\bBatchEvalPython\b|\bArrowEvalPython\b|\bPythonUDF\b|pandas_udf", plan_text),
        sort_merge_join_count=_count(r"\bSortMergeJoin\b", plan_text),
        broadcast_hash_join_count=_count(r"\bBroadcastHashJoin\b", plan_text),
        scan_count=len(scan_names) or _count(r"\b(?:FileScan|BatchScan|Scan)\b", plan_text),
        repeated_scans=repeated_scans,
        no_partition_pruning_signal=has_scan and partition_filters_empty,
        full_scan_signal=has_scan and partition_filters_empty and pushed_filters_empty,
        max_project_columns=_max_project_columns(plan_text),
        adaptive_plan_present="AdaptiveSparkPlan" in plan_text,
    )
