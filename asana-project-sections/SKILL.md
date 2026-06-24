---
name: asana-project-sections
description: List the sections of an Asana project, or create a new section, through the direct Asana REST API using a local ASANA_ACCESS_TOKEN. Use only as a narrow fallback when the normal Asana connector is unavailable or cannot return or create project sections.
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

# Asana Project Sections

Use this skill when the normal Asana connector cannot list a project's sections
or create a new section and a narrow REST fallback is needed.

Prefer the official Asana connector for normal section work. This skill is not a
general Asana client.

## Preconditions

- `ASANA_ACCESS_TOKEN` is available in the shell, `ASANA_ENV_FILE`, `--env-file`, or a local `.env.local`.
- The token belongs to an Asana user with access to the target project.
- Network access to `https://app.asana.com/api/1.0` is allowed.

## Non-Negotiable Rules

- Use `scripts/project_sections.py`.
- Never print the access token.
- Do not store the token in the skill directory.
- The default action only lists sections. A write happens only with `--create`.
- Use `--dry-run` with `--create` to preview a section before writing.
- Always pass a numeric project gid via `--project`.

## Recommended Commands

```bash
python3 scripts/project_sections.py --project 1200000000000000 --env-file /path/to/.env.local
python3 scripts/project_sections.py --project 1200000000000000 --json
python3 scripts/project_sections.py --project 1200000000000000 --create "Example Section" --dry-run --json
python3 scripts/project_sections.py --project 1200000000000000 --create "Example Section" --json
```

## Output Shape

- List text output: `action=list count=<n>`, then one line per section with its gid and name.
- Create text output: `action=created` (or `action=dry_run`) with the section gid and name.
- `--json` output: `schema_version`, `fetched_at`, and the action result (`action`, `count`, `sections` for list; `action`, `gid`, `name` for create).
- Failure categories are `missing_token`, `not_found`, `permission_denied`, `rate_limited`, and `network`.
