from pathlib import Path

from spark_plan_doctor import inspect_plan_text


plan_text = Path("plans/orders_plan.txt").read_text(encoding="utf-8")
report = inspect_plan_text(plan_text, plan_name="orders_plan", prompt_policy="never")

print(report.summary())

if report.has_findings_at_or_above("critical"):
    raise SystemExit(1)
