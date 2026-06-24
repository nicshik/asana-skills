---
name: asana-create-task
description: Create one Asana task through the direct Asana REST API using a local ASANA_ACCESS_TOKEN. Use only as a write fallback when the normal Asana connector is unavailable, and prefer --dry-run to confirm the payload before creating.
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

# Asana Create Task

Use this skill when the normal Asana connector cannot create a task and a narrow
REST fallback is needed.

Prefer the official Asana connector for normal task creation. This skill is not
a general Asana client.

## Preconditions

- `ASANA_ACCESS_TOKEN` is available in the shell, `ASANA_ENV_FILE`, `--env-file`, or a local `.env.local`.
- The token belongs to an Asana user who can create tasks in the target container.
- Network access to `https://app.asana.com/api/1.0` is allowed.

## Non-Negotiable Rules

- Use `scripts/create_task.py`.
- Never print the access token.
- Do not store the token in the skill directory.
- A container is required: pass `--project` (project gid) or `--workspace` (workspace gid).
- `--section` requires `--project`.
- `--notes`, `--notes-file`, and `--html-notes-file` are mutually exclusive.
- Prefer `--dry-run` first to confirm the payload before creating.

## Recommended Commands

```bash
python3 scripts/create_task.py --name "Example task" --project 1200000000000000 --dry-run --json
python3 scripts/create_task.py --name "Example task" --workspace 1200000000000001 --notes "Body text" --json
python3 scripts/create_task.py --name "Example task" --project 1200000000000000 --section 1200000000000001 \
  --tags "1200000000000000,1200000000000001" --assignee 1200000000000000 --due-on 2026-07-01 --json
```

## Output Shape

- Text output: `action`, plus payload summary on dry run, or gid, name, and permalink URL on create.
- `--json` output: `schema_version`, `fetched_at`, `action`, and either the redacted `payload` (dry run) or `gid`, `name`, `permalink_url` (created).
- On `--dry-run` no API call is made; `notes` and `html_notes` are redacted to `<N chars>` in the payload.
- Failure categories are `missing_token`, `not_found`, `permission_denied`, `rate_limited`, and `network`.
