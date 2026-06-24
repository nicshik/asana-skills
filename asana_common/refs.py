"""Shared Asana task reference parsing utilities.

Asana objects are addressed by numeric gids. Task references may arrive as a
bare gid or as a permalink URL such as
``https://app.asana.com/0/<project_gid>/<task_gid>`` or
``https://app.asana.com/1/<workspace>/project/<project>/task/<task_gid>``.
"""

from __future__ import annotations

import re
import urllib.parse
from dataclasses import dataclass


GID_RE = re.compile(r"^\d{6,}$")


@dataclass(frozen=True)
class TaskReference:
    raw: str
    lookup: str
    input_kind: str
    hint: str


def parse_task_reference(value: str) -> TaskReference:
    raw = value.strip()
    if not raw:
        return TaskReference(
            raw=value,
            lookup="",
            input_kind="empty",
            hint="Task reference is empty. Pass a numeric task gid or an Asana task URL.",
        )

    if GID_RE.match(raw):
        return TaskReference(
            raw=value,
            lookup=raw,
            input_kind="gid",
            hint="Verify that the task gid belongs to the expected workspace and is visible to the token.",
        )

    parsed = urllib.parse.urlparse(raw)
    is_url = bool(parsed.scheme and parsed.netloc)
    if is_url:
        text = urllib.parse.unquote(parsed.path)
        digit_parts = [part for part in text.split("/") if part.isdigit() and len(part) >= 6]
        if digit_parts:
            return TaskReference(
                raw=value,
                lookup=digit_parts[-1],
                input_kind="url_with_gid",
                hint="Verify that the task gid belongs to the expected workspace and is visible to the token.",
            )
        return TaskReference(
            raw=value,
            lookup=raw,
            input_kind="url_without_gid",
            hint="The URL does not contain a numeric task gid. Retry with an Asana task URL or a bare gid.",
        )

    return TaskReference(
        raw=value,
        lookup=raw,
        input_kind="raw",
        hint="The value is not a numeric task gid. Retry with a numeric gid or a full Asana task URL.",
    )


def task_not_found_details(reference: TaskReference) -> dict[str, str]:
    return {
        "error_code": "task_not_found",
        "lookup": reference.lookup,
        "input_kind": reference.input_kind,
        "hint": reference.hint,
    }


def is_task_entity_not_found_message(value: str) -> bool:
    normalized = value.casefold()
    return "not found" in normalized and ("task" in normalized or "object" in normalized)
