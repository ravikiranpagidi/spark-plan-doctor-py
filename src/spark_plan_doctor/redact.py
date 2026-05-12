from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any


SECRET_KEY_RE = re.compile(
    r"(token|password|passwd|secret|client_secret|access[_-]?key|api[_-]?key)",
    re.IGNORECASE,
)
SECRET_VALUE_RE = re.compile(
    r"(?i)(token|password|passwd|secret|client_secret|access[_-]?key|api[_-]?key)\s*=\s*([^\s,;]+)"
)


def redact_text(value: str) -> str:
    return SECRET_VALUE_RE.sub(lambda match: f"{match.group(1)}=<redacted>", value)


def redact_mapping(payload: Mapping[str, Any]) -> dict[str, Any]:
    redacted: dict[str, Any] = {}
    for key, value in payload.items():
        if SECRET_KEY_RE.search(str(key)):
            redacted[str(key)] = "<redacted>"
        elif isinstance(value, Mapping):
            redacted[str(key)] = redact_mapping(value)
        elif isinstance(value, str):
            redacted[str(key)] = redact_text(value)
        else:
            redacted[str(key)] = value
    return redacted
