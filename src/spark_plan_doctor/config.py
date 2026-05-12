from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PlanDoctorConfig:
    """Tunable thresholds for static Spark plan checks."""

    warning_exchange_count: int = 2
    critical_exchange_count: int = 5
    warning_sort_count: int = 3
    warning_project_columns: int = 80
    repeated_scan_threshold: int = 2
    default_prompt_policy: str = "auto"
    redact_output: bool = True

    def __post_init__(self) -> None:
        if self.warning_exchange_count < 1:
            raise ValueError("warning_exchange_count must be at least 1")
        if self.critical_exchange_count < self.warning_exchange_count:
            raise ValueError("critical_exchange_count must be >= warning_exchange_count")
        if self.warning_sort_count < 1:
            raise ValueError("warning_sort_count must be at least 1")
        if self.warning_project_columns < 1:
            raise ValueError("warning_project_columns must be at least 1")
        if self.repeated_scan_threshold < 2:
            raise ValueError("repeated_scan_threshold must be at least 2")
        if self.default_prompt_policy not in {"never", "always", "auto", "complex-only"}:
            raise ValueError("default_prompt_policy must be never, always, auto, or complex-only")
