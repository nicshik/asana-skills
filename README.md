# Asana Skills

[Русский](README.ru.md)

Agent skills and small Python scripts for direct Asana REST API workflows.

The scripts are plain Python over the Asana REST API, so they run from any agent runtime that can execute Python — Codex, Claude Code, Cursor, Antigravity, Windsurf — or from a plain shell. `SKILL.md` carries the cross-runtime skill metadata; `agents/openai.yaml` is the Codex/OpenAI adapter.

This repository is useful when the standard Asana connector is read-only, unavailable, or blocked by a tool guard, but you still need a narrow, auditable way to automate Asana actions with your own personal access token.

The repository is intentionally generic. Project-specific workspaces, projects, tags, assignees, and "done" policies should live in a separate wrapper skill or project repository, not here.

## Included Skills

| Skill | Purpose |
| --- | --- |
| `asana-preflight` | Check the token and report the authenticated user and workspaces. |
| `asana-read-task` | Read one task, with optional stories, as a read-only fallback. |
| `asana-list-tasks` | List tasks by project, section, tag, or assignee, with pagination. |
| `asana-search-tasks` | Search tasks in a workspace (Asana premium feature). |
| `asana-create-task` | Create one task after resolving container, section, parent, assignee, and tags. |
| `asana-update-task` | Update one task's fields, completion, tags, or section after a checked change set. |
| `asana-delete-task` | Delete one task after reading it, with dry-run and exact confirmation. |
| `asana-comment-task` | Add one story (comment) to a task. |
| `asana-list-projects` | List projects in a workspace or team. |
| `asana-project-sections` | List a project's sections, or create one section. |
| `asana-list-tags` | List a workspace's tags. |
| `asana-api` | Generic passthrough to any Asana REST endpoint for actions not covered above. |

## Repository Layout

```text
asana-read-task/
  SKILL.md
  agents/openai.yaml
  scripts/read_task.py
asana-create-task/
  SKILL.md
  agents/openai.yaml
  scripts/create_task.py
... one directory per skill ...
asana_common/
  rest.py
  refs.py
docs/
  codex-approvals.md
  release.md
examples/
  default.env.snippet
scripts/
  validate.sh
  secret_scan.sh
  release_check.sh
  validate_skill_files.py
tests/
```

## Requirements

- Python 3.10 or newer.
- An Asana personal access token with access to the target workspace.
- Optional but recommended: `certifi` for reliable TLS certificate handling on macOS Python installs.

Install the optional Python dependency:

```bash
python3 -m pip install -r requirements.txt
```

## Token Setup

Create a token at `https://app.asana.com/0/my-apps` under "Personal access tokens", then set it in your shell:

```bash
export ASANA_ACCESS_TOKEN=<asana-personal-access-token>
```

Or pass a local env file:

```bash
python3 asana-read-task/scripts/read_task.py 1200000000000000 --env-file /path/to/.env.local
```

The env file should contain:

```text
ASANA_ACCESS_TOKEN=<asana-personal-access-token>
```

Do not commit real tokens. `.env` and `.env.*` are ignored by this repository. A personal access token grants broad account access, so keep operations scoped to the intended workspace and project.

## Usage

All gids below are placeholders. Global flags (`--env-file`, `--json`) go after the subcommand-style positionals.

Check the token:

```bash
python3 asana-preflight/scripts/preflight.py --env-file /path/to/.env.local --json
```

Read one task without writing:

```bash
python3 asana-read-task/scripts/read_task.py 1200000000000000 \
  --env-file /path/to/.env.local \
  --include-stories
```

List tasks in a project:

```bash
python3 asana-list-tasks/scripts/list_tasks.py \
  --project 1200000000000001 \
  --all \
  --env-file /path/to/.env.local \
  --json
```

Create one task after a dry-run:

```bash
python3 asana-create-task/scripts/create_task.py \
  --project 1200000000000001 \
  --name "Example task" \
  --notes-file /path/to/body.txt \
  --assignee me \
  --tags 1200000000000010,1200000000000011 \
  --env-file /path/to/.env.local \
  --dry-run --json
```

Drop `--dry-run` to create the task; success returns the gid and `permalink_url`.

Update one task:

```bash
python3 asana-update-task/scripts/update_task.py 1200000000000000 \
  --name "Renamed task" \
  --completed \
  --add-tag 1200000000000010 \
  --env-file /path/to/.env.local \
  --dry-run --json
```

Comment on a task:

```bash
python3 asana-comment-task/scripts/comment_task.py 1200000000000000 \
  --text-file /path/to/comment.txt \
  --env-file /path/to/.env.local
```

Delete one task after verifying it:

```bash
python3 asana-delete-task/scripts/delete_task.py 1200000000000000 \
  --env-file /path/to/.env.local \
  --dry-run --json
```

For live deletion, repeat the command without `--dry-run` and add `--confirm 1200000000000000`.

Reach any other endpoint with the generic passthrough:

```bash
python3 asana-api/scripts/api.py GET /projects/1200000000000001/project_statuses \
  --opt-fields text,author.name \
  --env-file /path/to/.env.local --json
```

Use `--json` when another tool or agent should consume the output.

## Project-Specific Wrappers

These skills are low-level Asana helpers. They do not decide which task should be created, which workspace or project is correct, or whether a task is "done". Keep those decisions in a project-specific wrapper skill or process document. The wrapper can call these scripts through stable environment variables such as `ASANA_ACCESS_TOKEN`, `ASANA_ENV_FILE`, or `--env-file`, and pass concrete gids it owns.

## Agent Approvals

The scripts call the Asana API over the network, so an agent runtime may ask for approval. Approve only the specific script entrypoints listed in [`docs/codex-approvals.md`](docs/codex-approvals.md); do not approve broad prefixes such as `python3`. The document uses Codex as the worked example, but the same narrow-entrypoint rule applies to Claude Code, Cursor, Antigravity, Windsurf, or any runtime with a permission model.

## Safety Model

- The token is read from environment variables or local env files only.
- The scripts never print the token and redact it from error output.
- A hard request timeout prevents calls from hanging.
- Read-only skills (`preflight`, `read-task`, `list-tasks`, `search-tasks`, `list-projects`, `list-tags`, and `project-sections` in list mode) never send writes.
- `--dry-run` on `create-task`, `update-task`, `delete-task`, `comment-task`, and `project-sections --create` resolves the payload without mutating Asana.
- `asana-delete-task` reads the task first, requires exact `--confirm`, and verifies deletion afterward.
- All scripts share one REST client, token resolution, TLS setup through `certifi` when available, pagination, and token sanitization for error output.

## Development

CI runs on pull requests, pushes to `main`, and manual GitHub Actions dispatches. It does not call the live Asana API and does not require `ASANA_ACCESS_TOKEN`; tests must use local mocks or fixtures.

Run the local CI equivalent:

```bash
scripts/validate.sh
```

Run fixture tests only:

```bash
python3 -m unittest discover -s tests
```

Run a secret sanity check before pushing:

```bash
scripts/secret_scan.sh
```

`scripts/validate.sh` also blocks accidental project-specific, account, or local-machine strings so this public repository stays portable.

Run the local release gate after committing and pushing:

```bash
scripts/release_check.sh
```

Release steps are documented in [`docs/release.md`](docs/release.md). Dependency updates are handled by Dependabot for GitHub Actions and Python requirements.

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md).

## Changelog

See [`CHANGELOG.md`](CHANGELOG.md).

## Security

See [`SECURITY.md`](SECURITY.md).

## License

MIT. See [`LICENSE`](LICENSE).

## Disclaimer

This project is not affiliated with Asana. It uses Asana's public REST API with a user-provided personal access token.
