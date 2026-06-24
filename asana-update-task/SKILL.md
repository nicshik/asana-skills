---
name: asana-update-task
description: Update one Asana task through the direct Asana REST API using a local ASANA_ACCESS_TOKEN. Use only as a write fallback when the normal Asana connector is unavailable or cannot apply the required field, tag, or section changes.
metadata:
  category: productivity
  capability_taxonomy_ids:
    - cap.productivity.task_tracking
    - cap.tools.api_automation
  compatibility:
    runtimes:
      - codex
      - claude_code
      - cursor
      - antigravity
      - windsurf
  distribution_scope: public
  invocation_strategy: explicit
  version: v0.1
  source_of_truth: https://github.com/nicshik/asana-skills
---

# Asana Update Task

Use this skill when the normal Asana connector cannot update a target task and a
narrow REST fallback is needed to change fields, add or remove tags, or move the
task into a section.

Prefer the official Asana connector for normal task updates. This skill is not a
general Asana client and changes only the task you target.

## Preconditions

- `ASANA_ACCESS_TOKEN` is available in the shell, `ASANA_ENV_FILE`, `--env-file`, or a local `.env.local`.
- The token belongs to an Asana user with permission to edit the target task.
- Network access to `https://app.asana.com/api/1.0` is allowed.

## Non-Negotiable Rules

- Use `scripts/update_task.py`.
- Never print the access token.
- Do not store the token in the skill directory.
- Target exactly one task. Prefer a numeric task gid; an Asana URL is accepted and the gid is extracted from it.
- At least one change is required (a field flag, a tag operation, or `--to-section`).
- Use `--dry-run` first to confirm the planned payload before writing.

## Recommended Commands

```bash
python3 scripts/update_task.py 1200000000000000 --name "New title" --dry-run --json
python3 scripts/update_task.py 1200000000000000 --completed --env-file /path/to/.env.local
python3 scripts/update_task.py "https://app.asana.com/0/1200000000000001/1200000000000000" \
  --add-tag 1200000000000002 --to-section 1200000000000003 --json
```

## Inputs

- `--name`, `--notes` | `--notes-file` | `--html-notes-file` (mutually exclusive), `--due-on`, `--due-at`, `--assignee`.
- `--completed` / `--incomplete` set the completion flag.
- `--add-tag GID` and `--remove-tag GID` are repeatable.
- `--to-section GID` moves the task into a section.
- `--data-file` merges a JSON object into the field payload for fields without a dedicated flag.

## Output Shape

- Text output: action, gid, name, changed field keys, added/removed tags, and target section.
- `--json` output: `schema_version`, `fetched_at`, `action`, `gid`, `name`, and `applied` (`fields`, `add_tags`, `remove_tags`, `to_section`).
- `action` is `dry_run` when `--dry-run` is set (no API calls) and `updated` after a live write.
- Failure categories are `missing_token`, `bad_argument`, `not_found`, `permission_denied`, `rate_limited`, and `network`.
- Task lookup failures use `error_category=not_found` and `error_code=task_not_found`, with safe `lookup`, `input_kind`, and `hint` fields.
- `task_not_found` means Asana was reached but the task was not found by the provided reference. Do not report it as a missing token unless the category is `missing_token`.
