from __future__ import annotations

import argparse
from pathlib import Path

from spark_plan_doctor.demo import sample_plan
from spark_plan_doctor.doctor import inspect_plan_text


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="spark-plan-doctor")
    subparsers = parser.add_subparsers(dest="command")

    demo_parser = subparsers.add_parser("demo", help="inspect a sample Spark plan")
    demo_parser.add_argument("--format", choices=["text", "json", "prompt"], default="text")

    file_parser = subparsers.add_parser("inspect-plan-file", help="inspect a saved Spark plan text file")
    file_parser.add_argument("path")
    file_parser.add_argument("--plan-name", default="spark_plan")
    file_parser.add_argument("--job-name", default="")
    file_parser.add_argument("--team", default="")
    file_parser.add_argument("--format", choices=["text", "json", "prompt"], default="text")
    file_parser.add_argument("--fail-on", choices=["info", "warning", "critical"], default="")
    file_parser.add_argument("--write-agent-bundle", default="")

    args = parser.parse_args(argv)
    if args.command == "demo":
        report = inspect_plan_text(sample_plan(), plan_name="demo_orders_plan", prompt_policy="never")
        _print_report(report, args.format)
        return 0
    if args.command == "inspect-plan-file":
        plan_text = Path(args.path).read_text(encoding="utf-8")
        report = inspect_plan_text(
            plan_text,
            plan_name=args.plan_name,
            job_name=args.job_name,
            team=args.team,
            prompt_policy="never",
        )
        if args.write_agent_bundle:
            from spark_plan_doctor.writers import write_agent_bundle

            write_agent_bundle(report, args.write_agent_bundle)
        _print_report(report, args.format)
        if args.fail_on and report.has_findings_at_or_above(args.fail_on):
            return 1
        return 0
    parser.print_help()
    return 2


def _print_report(report, fmt: str) -> None:
    if fmt == "json":
        print(report.to_json())
    elif fmt == "prompt":
        print(report.to_agent_prompt())
    else:
        print(report.summary())
