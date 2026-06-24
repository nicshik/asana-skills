---
name: asana-list-tags
description: List the tags in an Asana workspace through the direct Asana REST API using a local ASANA_ACCESS_TOKEN. Use only as a read-only fallback when the normal Asana connector is unavailable or cannot enumerate workspace tags.
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

# Asana List Tags

Use this skill when the normal Asana connector cannot enumerate the tags in a
workspace and a narrow read-only REST fallback is needed.

Prefer the official Asana connector for normal tag listing. This skill is not a
general Asana client and must not be used for updates.

## Preconditions

- `ASANA_ACCESS_TOKEN` is available in the shell, `ASANA_ENV_FILE`, `--env-file`, or a local `.env.local`.
- The token belongs to an Asana user with access to the target workspace.
- Network access to `https://app.asana.com/api/1.0` is allowed.

## Non-Negotiable Rules

- Use `scripts/list_tags.py`.
- Never print the access token.
- Do not store the token in the skill directory.
- Keep this helper read-only. It must not send writes.
- Pass the workspace gid via `--workspace`.

## Recommended Commands

```bash
python3 scripts/list_tags.py --workspace 1200000000000000 --env-file /path/to/.env.local
python3 scripts/list_tags.py --workspace 1200000000000000 --json
python3 scripts/list_tags.py --workspace 1200000000000000 --fields name,color,notes --json
```

## Output Shape

- Text output: a `tags=<count>` header line, then one line per tag with its gid, name, and color.
- `--json` output: `schema_version`, `fetched_at`, `count`, and the `tags` array.
- Failure categories are `missing_token`, `not_found`, `permission_denied`, `rate_limited`, and `network`.
