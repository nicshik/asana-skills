# Contributing

Contributions are welcome if they keep the skills narrow, deterministic, and safe to run through Codex or another agent runtime.

## Guidelines

- Keep each skill focused on one Asana workflow.
- Prefer small scripts with explicit arguments over broad shell snippets.
- Never commit access tokens, `.env` files, workspace tokens, or command logs that contain secrets.
- Keep Codex approval guidance narrow. Do not recommend broad prefixes such as `python3`.
- Use `--dry-run` for examples that could otherwise mutate Asana state.
- Keep tests offline. Do not call the live Asana API from tests or CI; use mocks and fixtures.
- Keep `SKILL.md` concise and move longer setup guidance to `docs/`.

## Local Checks

```bash
scripts/validate.sh
```

```bash
scripts/secret_scan.sh
```

These checks mirror the GitHub Actions CI and do not require a real `ASANA_ACCESS_TOKEN`.
They also block accidental project-specific, account, or local-machine strings. Keep private workspace, project, user, and tag gids, real task titles, and private workspace names outside this public repository.

Before tagging a release, run:

```bash
scripts/release_check.sh
```

Release steps are documented in [`docs/release.md`](docs/release.md).

## Adding A New Skill

Follow the existing structure:

```text
asana-something/
  SKILL.md
  agents/openai.yaml
  scripts/something.py
```

The script should read `ASANA_ACCESS_TOKEN` from the environment or `--env-file`, avoid printing the token, and support `--json` when another agent may consume the output. Add an offline fixture test under `tests/`, and register the new skill in `scripts/validate.sh` and `scripts/validate_skill_files.py`.
