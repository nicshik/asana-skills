---
name: asana-preflight
description: Verify direct Asana REST access using a local ASANA_ACCESS_TOKEN by reading the token's own user and workspaces from GET /users/me. Use only as a read-only fallback to confirm credentials and workspace visibility when the normal Asana connector is unavailable.
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

# Asana Preflight

Use this skill to confirm that a local `ASANA_ACCESS_TOKEN` is valid and to see
which user it authenticates as and which workspaces it can reach, before running
other direct Asana REST helpers.

Prefer the official Asana connector for normal work. This skill is a narrow
read-only check and is not a general Asana client.

## Preconditions

- `ASANA_ACCESS_TOKEN` is available in the shell, `ASANA_ENV_FILE`, `--env-file`, or a local `.env.local`.
- Network access to `https://app.asana.com/api/1.0` is allowed.

## Non-Negotiable Rules

- Use `scripts/preflight.py`.
- Never print the access token.
- Do not store the token in the skill directory.
- Keep this helper read-only. It must not send writes.

## Recommended Commands

```bash
python3 scripts/preflight.py --env-file /path/to/.env.local
python3 scripts/preflight.py --json
```

## Output Shape

- Text output: the authenticated user, the email, the workspace count, and each workspace gid and name.
- `--json` output: `schema_version`, `fetched_at`, `user`, `email`, and `workspaces` as a list of `{gid, name}`.
- Failure categories are `missing_token`, `permission_denied`, `rate_limited`, and `network`.
- A `permission_denied` category means the token was rejected by Asana; a `missing_token` category means no token was found locally.
