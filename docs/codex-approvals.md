# Codex Approvals

The scripts call the Asana REST API over the network, so Codex may ask for approval. To avoid repeated prompts while keeping the permission narrow, approve only the specific script entrypoints rather than a broad `python3` prefix.

## Approved Command Prefixes

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

## Rules

- Do not approve broad prefixes such as `python3`.
- Run scripts from the repository root so the command prefix stays stable.
- Pass the token only through the environment or `--env-file`; never as a command argument.
- Prefer read-only skills (`preflight`, `read-task`, `list-tasks`, `search-tasks`, `list-projects`, `project-sections`, `list-tags`) and `--dry-run` on write skills while seeding approvals.
