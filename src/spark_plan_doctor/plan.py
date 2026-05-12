from __future__ import annotations

import contextlib
import hashlib
import io
import uuid
from typing import Any


def make_run_id() -> str:
    return uuid.uuid4().hex


def hash_plan(plan_text: str) -> str:
    normalized = "\n".join(line.rstrip() for line in plan_text.strip().splitlines())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]


def extract_plan_text(df: Any, mode: str = "formatted") -> str:
    """Extract a Spark plan without running a Spark action."""

    if isinstance(df, str):
        return df

    explain = getattr(df, "explain", None)
    if callable(explain):
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            result = explain(mode)
        text = buffer.getvalue().strip()
        if not text and isinstance(result, str):
            text = result.strip()
        if text:
            return text

    jdf = getattr(df, "_jdf", None)
    if jdf is not None:
        query_execution = jdf.queryExecution()
        return str(query_execution.toString())

    raise TypeError("df must be a PySpark DataFrame, a plan string, or an object with explain(mode)")


def get_spark_version(spark: Any | None) -> str:
    if spark is None:
        return ""
    version = getattr(spark, "version", "")
    if version:
        return str(version)
    spark_context = getattr(spark, "sparkContext", None)
    return str(getattr(spark_context, "version", "") or "")


def get_spark_conf(spark: Any | None) -> dict[str, str]:
    if spark is None:
        return {}
    conf = getattr(spark, "conf", None)
    if conf is None:
        return {}
    keys = [
        "spark.sql.adaptive.enabled",
        "spark.sql.shuffle.partitions",
        "spark.sql.autoBroadcastJoinThreshold",
    ]
    values: dict[str, str] = {}
    for key in keys:
        try:
            value = conf.get(key)
        except Exception:
            continue
        if value is not None:
            values[key] = str(value)
    return values
