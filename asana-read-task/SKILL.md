---
name: asana-read-task
description: Read one Asana task through the direct Asana REST API using a local ASANA_ACCESS_TOKEN. Use only as a read-only fallback when the normal Asana connector is unavailable or cannot return required task fields or stories.
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

# Asana Read Task

Use this skill when the normal Asana connector cannot read a target task, its
fields, or its stories (comments/history) and a narrow read-only REST fallback
is needed.

Prefer the official Asana connector for normal task reads. This skill is not a
general Asana client and must not be used for updates.

## Preconditions

- `ASANA_ACCESS_TOKEN` is available in the shell, `ASANA_ENV_FILE`, `--env-file`, or a local `.env.local`.
- The token belongs to an Asana user with access to the target task.
- Network access to `https://app.asana.com/api/1.0` is allowed.

## Non-Negotiable Rules

- Use `scripts/read_task.py`.
- Never print the access token.
- Do not store the token in the skill directory.
- Keep this helper read-only. It must not send writes.
- Prefer a numeric task gid; an Asana URL is accepted and the gid is extracted from it.
- Use `--include-stories` only when comments/history are required.

## Recommended Commands

```bash
python3 scripts/read_task.py 1200000000000000 --env-file /path/to/.env.local
python3 scripts/read_task.py "https://app.asana.com/0/1200000000000001/1200000000000000" --json
python3 scripts/read_task.py 1200000000000000 --json --include-stories
```

## Output Shape

- Text output: task gid, name, project, section, assignee, due date, tags, and optional story count.
- `--json` output: `schema_version`, `fetched_at`, and the task payload.
- Failure categories are `missing_token`, `not_found`, `permission_denied`, `rate_limited`, and `network`.
- Task lookup failures use `error_category=not_found` and `error_code=task_not_found`, with safe `lookup`, `input_kind`, and `hint` fields.
- `task_not_found` means Asana was reached but the task was not found by the provided reference. Do not report it as a missing token unless the category is `missing_token`.
