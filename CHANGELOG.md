# Changelog

## Unreleased

- Nothing yet.

## 2026-06-24 - v0.1.0

- Publish generic Asana skills for direct Asana REST API workflows with a personal access token.
- Add `asana-preflight` for an auth/identity check.
- Add `asana-read-task` as a read-only task fallback with optional stories.
- Add `asana-list-tasks` for listing tasks by project, section, tag, or assignee with pagination.
- Add `asana-search-tasks` for workspace task search (Asana premium feature).
- Add `asana-create-task` with project/section/parent/assignee/tags, dry-run, and verification.
- Add `asana-update-task` for checked field, completion, tag, and section updates.
- Add `asana-delete-task` for checked deletion with read-before-delete, dry-run, and exact confirmation.
- Add `asana-comment-task` for adding one story (comment) to a task.
- Add `asana-list-projects` and `asana-project-sections` for project and section metadata.
- Add `asana-list-tags` for workspace tag listing.
- Add `asana-api` generic passthrough for any Asana REST endpoint.
- Share Asana REST token loading, TLS setup through `certifi` when available, pagination, and token-safe errors across scripts.
- Add offline fixture tests, metadata validation, CI, secret-scan, and a public repository guard against project-specific, account, or local-machine strings.
