---
name: asana-comment-task
description: Add a comment story to one Asana task through the direct Asana REST API using a local ASANA_ACCESS_TOKEN. Use only as a narrow fallback when the normal Asana connector cannot post a comment to a target task.
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

# Asana Comment Task

Use this skill when the normal Asana connector cannot post a comment to a target
task and a narrow REST fallback is needed.

Prefer the official Asana connector for normal commenting. This skill is not a
general Asana client and only posts a single comment story per call.

## Preconditions

- `ASANA_ACCESS_TOKEN` is available in the shell, `ASANA_ENV_FILE`, `--env-file`, or a local `.env.local`.
- The token belongs to an Asana user with access to the target task.
- Network access to `https://app.asana.com/api/1.0` is allowed.

## Non-Negotiable Rules

- Use `scripts/comment_task.py`.
- Never print the access token.
- Do not store the token in the skill directory.
- This helper posts exactly one comment story; it performs no other writes.
- Provide exactly one of `--text` or `--text-file`.
- Prefer a numeric task gid; an Asana URL is accepted and the gid is extracted from it.
- Use `--dry-run` first to validate the target and the comment length without posting.

## Recommended Commands

```bash
python3 scripts/comment_task.py 1200000000000000 --text "Status update." --dry-run
python3 scripts/comment_task.py 1200000000000000 --text "Status update." --env-file /path/to/.env.local
python3 scripts/comment_task.py "https://app.asana.com/0/1200000000000001/1200000000000000" --text-file ./note.txt --json
```

## Output Shape

- Text output: `action`, `task`, and either `text_length` (dry run) or `story_gid`.
- `--json` output: `schema_version`, `fetched_at`, `action`, `task`, and `story_gid` when a comment was posted.
- `action` is `dry_run` when `--dry-run` is set and `commented` otherwise.
- Failure categories are `missing_token`, `not_found`, `permission_denied`, `rate_limited`, and `network`.
- Task lookup failures use `error_category=not_found` and `error_code=task_not_found`, with safe `lookup`, `input_kind`, and `hint` fields.
- `task_not_found` means Asana was reached but the task was not found by the provided reference. Do not report it as a missing token unless the category is `missing_token`.
