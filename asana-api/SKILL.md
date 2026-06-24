---
name: asana-api
description: Call an arbitrary Asana REST API endpoint by HTTP method and path through the direct Asana API using a local ASANA_ACCESS_TOKEN. Use only as a low-level fallback when the normal Asana connector cannot reach the endpoint you need; you control the method, path, query, and body.
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

# Asana API

Use this skill as a generic passthrough to the Asana REST API when the normal
Asana connector or a higher-level skill cannot reach the endpoint or shape you
need. You choose the HTTP method, the path, the query parameters, and the
request body.

Prefer the official Asana connector and the focused skills for normal work.
This skill is a low-level tool: it can send writes, so use it deliberately.

## Preconditions

- `ASANA_ACCESS_TOKEN` is available in the shell, `ASANA_ENV_FILE`, `--env-file`, or a local `.env.local`.
- The token belongs to an Asana user with access to the target resource.
- Network access to `https://app.asana.com/api/1.0` is allowed.

## Non-Negotiable Rules

- Use `scripts/api.py`.
- Never print the access token.
- Do not store the token in the skill directory.
- The method and path are sent verbatim; double-check before sending writes (`POST`, `PUT`, `DELETE`).
- Pass query parameters with `--query k=v` and body fields with `--field k=v` (both repeatable).
- `--field` values are always sent as strings; for richer bodies use `--data-file`.
- `--data-file` wins over `--field` when both are given.
- A `--data-file` whose top-level JSON object already contains a `data` key is sent as-is; otherwise the loaded JSON is wrapped as the inner `data` object.
- `--all` is honored only for `GET` and follows pagination via the shared client.

## Recommended Commands

```bash
python3 scripts/api.py GET /tasks/1200000000000000 --opt-fields name,completed --json
python3 scripts/api.py GET /projects/1200000000000001/tasks --all --json
python3 scripts/api.py POST /tasks --field name=Example --field workspace=1200000000000000 --json
python3 scripts/api.py PUT /tasks/1200000000000000 --data-file ./body.json --json
```

## Output Shape

- Text output: `rows=<n>` for a list, `gid=` (and `name=` when present) for an object, or `data=` otherwise.
- `--json` output: `schema_version`, `fetched_at`, and the `data` payload returned by the API.
- Failure categories are `missing_token`, `bad_argument`, `not_found`, `permission_denied`, `premium_required`, `rate_limited`, `http_error`, `network`, `timeout`, and `api_error`.
- `bad_argument` means a `--query`, `--field`, or `--data-file` value was malformed; it is a local input problem, not a missing token.
