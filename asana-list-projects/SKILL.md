---
name: asana-list-projects
description: List Asana projects in a workspace or team through the direct Asana REST API using a local ASANA_ACCESS_TOKEN. Use only as a read-only fallback when the normal Asana connector is unavailable or cannot enumerate the projects you need.
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
  distribution_scope: public
  invocation_strategy: explicit
  version: v0.1
  source_of_truth: https://github.com/nicshik/asana-skills
---

# Asana List Projects

Use this skill when the normal Asana connector cannot enumerate the projects in
a workspace or team and a narrow read-only REST fallback is needed.

Prefer the official Asana connector for normal project listings. This skill is
not a general Asana client and must not be used for writes.

## Preconditions

- `ASANA_ACCESS_TOKEN` is available in the shell, `ASANA_ENV_FILE`, `--env-file`, or a local `.env.local`.
- The token belongs to an Asana user with access to the target workspace or team.
- Network access to `https://app.asana.com/api/1.0` is allowed.

## Non-Negotiable Rules

- Use `scripts/list_projects.py`.
- Never print the access token.
- Do not store the token in the skill directory.
- Keep this helper read-only. It must not send writes.
- Pass exactly one scope: `--workspace` or `--team` (numeric gids).
- Results always paginate through every page.

## Recommended Commands

```bash
python3 scripts/list_projects.py --workspace 1200000000000000 --env-file /path/to/.env.local
python3 scripts/list_projects.py --team 1200000000000001 --json
python3 scripts/list_projects.py --workspace 1200000000000000 --archived false --json
```

## Output Shape

- Text output: a `count` line and one line per project with gid, archived state, and name.
- `--json` output: `schema_version`, `fetched_at`, `count`, and the `projects` array.
- Failure categories are `missing_token`, `not_found`, `permission_denied`, `rate_limited`, and `network`.
