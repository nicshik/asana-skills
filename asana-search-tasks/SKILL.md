---
name: asana-search-tasks
description: Search Asana tasks within a workspace by full-text query through the direct Asana REST API using a local ASANA_ACCESS_TOKEN. Use only as a read-only fallback when the normal Asana connector is unavailable or cannot run a task search.
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

# Asana Search Tasks

Use this skill when the normal Asana connector cannot run a workspace task
search and a narrow read-only REST fallback is needed.

Prefer the official Asana connector for normal searches. This skill is not a
general Asana client and must not be used for updates.

## Preconditions

- `ASANA_ACCESS_TOKEN` is available in the shell, `ASANA_ENV_FILE`, `--env-file`, or a local `.env.local`.
- The token belongs to an Asana user with access to the target workspace.
- Network access to `https://app.asana.com/api/1.0` is allowed.
- Task search is an Asana premium feature. On non-premium workspaces the API returns HTTP 402, which surfaces as `error_category=premium_required`.

## Non-Negotiable Rules

- Use `scripts/search_tasks.py`.
- Never print the access token.
- Do not store the token in the skill directory.
- Keep this helper read-only. It must not send writes.
- Pass a numeric workspace gid via `--workspace` and a query via `--text`.
- Use `--project` to scope results to one project (sets `projects.any`).

## Recommended Commands

```bash
python3 scripts/search_tasks.py --workspace 1200000000000000 --text "billing" --env-file /path/to/.env.local
python3 scripts/search_tasks.py --workspace 1200000000000000 --text "release" --project 1200000000000001 --json
python3 scripts/search_tasks.py --workspace 1200000000000000 --text "review" --limit 50 --json
```

## Output Shape

- Text output: a `count` line, then one line per task with gid, completed flag, section, and name.
- `--json` output: `schema_version`, `fetched_at`, `count`, and the `tasks` array.
- Failure categories are `missing_token`, `premium_required`, `permission_denied`, `not_found`, `rate_limited`, and `network`.
- `premium_required` means the search endpoint requires an Asana premium plan. Do not report it as a missing token.
