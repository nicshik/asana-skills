#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if ! command -v rg >/dev/null 2>&1; then
  echo "ERROR: ripgrep is required for validation." >&2
  exit 2
fi

SKILLS=(
  asana-preflight
  asana-read-task
  asana-list-tasks
  asana-search-tasks
  asana-create-task
  asana-update-task
  asana-delete-task
  asana-comment-task
  asana-list-projects
  asana-project-sections
  asana-list-tags
  asana-api
)

echo "== Public repository guard =="
# Terms are split so this guard file never matches itself. They block any
# leak of private project, workspace, account, or task identifiers into this
# public repository.
blocked_terms=(
  "Factor""ix"
  "F""CT-"
  "/Users/""nick"
  "shikhi""rev"
  "Max""im"
  "694401""119437588"
  "121553""1968424616"
  "143962""864733743"
  "Тендер ""заказчика"
  "Штраф ""заказчику"
  ".env"".local:ASANA"
)
for term in "${blocked_terms[@]}"; do
  if rg -n -i --fixed-strings --hidden --glob '!.git/**' --glob '!__pycache__/**' --glob '!*.pyc' "$term" .; then
    echo "ERROR: project-specific, account, or local-machine term found: $term" >&2
    exit 1
  fi
done

echo "== Secret scan =="
scripts/secret_scan.sh

echo "== Compile Python sources =="
compile_targets=(asana_common tests)
for skill in "${SKILLS[@]}"; do
  compile_targets+=("$skill")
done
python3 -m compileall "${compile_targets[@]}"

echo "== Fixture tests =="
python3 -m unittest discover -s tests

echo "== Skill metadata =="
python3 scripts/validate_skill_files.py

echo "== CLI help smoke =="
python3 asana-preflight/scripts/preflight.py --help >/dev/null
python3 asana-read-task/scripts/read_task.py --help >/dev/null
python3 asana-list-tasks/scripts/list_tasks.py --help >/dev/null
python3 asana-search-tasks/scripts/search_tasks.py --help >/dev/null
python3 asana-create-task/scripts/create_task.py --help >/dev/null
python3 asana-update-task/scripts/update_task.py --help >/dev/null
python3 asana-delete-task/scripts/delete_task.py --help >/dev/null
python3 asana-comment-task/scripts/comment_task.py --help >/dev/null
python3 asana-list-projects/scripts/list_projects.py --help >/dev/null
python3 asana-project-sections/scripts/project_sections.py --help >/dev/null
python3 asana-list-tags/scripts/list_tags.py --help >/dev/null
python3 asana-api/scripts/api.py --help >/dev/null

echo "Validation passed."
