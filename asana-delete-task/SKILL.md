---
name: asana-delete-task
description: Delete one Asana task through the direct Asana REST API using a local ASANA_ACCESS_TOKEN. Use only as a guarded fallback when the normal Asana connector cannot delete a target task. Live deletes require an explicit --confirm matching the resolved task gid.
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

# Asana Delete Task

Use this skill when the normal Asana connector cannot delete a target task and a
narrow, guarded REST fallback is needed.

Prefer the official Asana connector for normal task deletes. This skill is not a
general Asana client. Deleting a task is destructive: it removes the task and its
subtasks. Always read the task first and confirm the gid before deleting.

## Preconditions

- `ASANA_ACCESS_TOKEN` is available in the shell, `ASANA_ENV_FILE`, `--env-file`, or a local `.env.local`.
- The token belongs to an Asana user with permission to delete the target task.
- Network access to `https://app.asana.com/api/1.0` is allowed.

## Non-Negotiable Rules

- Use `scripts/delete_task.py`.
- Never print the access token.
- Do not store the token in the skill directory.
- Always run `--dry-run` first to read the task and confirm it is the intended one.
- A live delete requires `--confirm <gid>` where `<gid>` equals the resolved task gid; otherwise the script refuses with `not_confirmed`.
- Prefer a numeric task gid; an Asana URL is accepted and the gid is extracted from it.

## Recommended Commands

```bash
python3 scripts/delete_task.py 1200000000000000 --dry-run --env-file /path/to/.env.local
python3 scripts/delete_task.py "https://app.asana.com/0/1200000000000001/1200000000000000" --dry-run --json
python3 scripts/delete_task.py 1200000000000000 --confirm 1200000000000000 --json
```

## Output Shape

- Text output: action, verification status, task gid, completed flag, name, and permalink URL.
- `--json` output: `schema_version`, `fetched_at`, `action`, `before` (the task as read before delete), and `verification_status`.
- `action` is `dry_run` for a read-only preview or `deleted` for a live delete.
- `verification_status` is `dry_run` for a dry run, `not_found_after_delete` when the post-delete read confirms removal, or `read_back` when the task still reads back.
- Failure categories are `missing_token`, `not_found`, `not_confirmed`, `permission_denied`, `rate_limited`, and `network`.
- Task lookup failures use `error_category=not_found` and `error_code=task_not_found`, with safe `lookup`, `input_kind`, and `hint` fields.
- `not_confirmed` means the delete was refused because `--confirm` did not match the resolved gid. No delete was sent.
