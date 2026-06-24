---
name: asana-list-tasks
description: List Asana tasks for a project, section, tag, or assignee through the direct Asana REST API using a local ASANA_ACCESS_TOKEN. Use only as a read-only fallback when the normal Asana connector is unavailable or cannot enumerate the required tasks.
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

# Asana List Tasks

Use this skill when the normal Asana connector cannot enumerate the tasks of a
project, section, tag, or assignee and a narrow read-only REST fallback is
needed.

Prefer the official Asana connector for normal task listing. This skill is not a
general Asana client and must not be used for updates.

## Preconditions

- `ASANA_ACCESS_TOKEN` is available in the shell, `ASANA_ENV_FILE`, `--env-file`, or a local `.env.local`.
- The token belongs to an Asana user with access to the target tasks.
- Network access to `https://app.asana.com/api/1.0` is allowed.

## Non-Negotiable Rules

- Use `scripts/list_tasks.py`.
- Never print the access token.
- Do not store the token in the skill directory.
- Keep this helper read-only. It must not send writes.
- Pass exactly one selector: `--project`, `--section`, `--tag`, or `--assignee`.
- `--assignee` requires `--workspace`; `--completed-since` is optional and only applies to the assignee route.
- Use `--all` only when every page is required; otherwise `--limit` caps a single page (default 50).

## Recommended Commands

```bash
python3 scripts/list_tasks.py --project 1200000000000000 --env-file /path/to/.env.local
python3 scripts/list_tasks.py --section 1200000000000001 --json
python3 scripts/list_tasks.py --tag 1200000000000000 --all --json
python3 scripts/list_tasks.py --assignee me --workspace 1200000000000001 --completed-since 2026-06-01T00:00:00Z --json
```

## Output Shape

- Text output: a `count` line followed by one line per task with gid, completed flag, section, assignee, due date, and name.
- `--json` output: `schema_version`, `fetched_at`, `count`, and the `tasks` array.
- Failure categories are `missing_token`, `bad_argument`, `permission_denied`, `not_found`, `rate_limited`, and `network`.
- `bad_argument` means the selector flags were missing, ambiguous, or `--assignee` was used without `--workspace`. Do not report it as a missing token unless the category is `missing_token`.
