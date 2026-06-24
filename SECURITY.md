# Security Policy

## Supported Versions

The `main` branch is the supported version.

## Reporting A Vulnerability

If you find a vulnerability, open a private report through GitHub's security advisory flow if available, or contact the repository owner directly.

Do not open a public issue containing:

- Asana personal access tokens;
- workspace tokens;
- private task or project data;
- command logs with secrets.

## Token Handling

These skills require an Asana personal access token. Store it outside the repository:

```bash
export ASANA_ACCESS_TOKEN=<asana-personal-access-token>
```

or in a local ignored env file:

```text
ASANA_ACCESS_TOKEN=<asana-personal-access-token>
```

A personal access token grants broad access to the issuing user's Asana account. Keep all operations scoped to the intended workspace and project. If a token is exposed in chat, logs, or git history, deauthorize it in Asana (Profile settings -> Apps -> Personal access tokens) and create a new one.

## Permission Scope

For Codex, approve only the script entrypoints:

```text
python3 asana-preflight/scripts/preflight.py
python3 asana-read-task/scripts/read_task.py
python3 asana-list-tasks/scripts/list_tasks.py
python3 asana-search-tasks/scripts/search_tasks.py
python3 asana-create-task/scripts/create_task.py
python3 asana-update-task/scripts/update_task.py
python3 asana-delete-task/scripts/delete_task.py
python3 asana-comment-task/scripts/comment_task.py
python3 asana-list-projects/scripts/list_projects.py
python3 asana-project-sections/scripts/project_sections.py
python3 asana-list-tags/scripts/list_tags.py
python3 asana-api/scripts/api.py
```

Do not approve broad command prefixes such as `python3`.
