# Repository Guidelines

## Project Overview

CleanSweep TUI is a Linux-only Python CLI/TUI for cleaning development caches, user cache/data, system caches, and app-specific preset paths. It uses Textual for the terminal UI and Rich for terminal output.

The tool deletes real files. Preserve the existing safety model:

- Cache items may be selected by default.
- User data, app config, system, and custom items must stay destructive and unselected by default.
- Every cleanup action must be visible in the preview as the exact shell command that will run.
- Missing tools or paths should disable the item instead of failing at startup.
- Avoid broadening deletion scope unless the user explicitly asks and the README is updated.

## Common Commands

- Sync dependencies: `uv sync`
- Run from source: `uv run main.py`
- Import/compile smoke test: `uv run python -m compileall clean_sweep_tui main.py`
- Inspect generated steps:

```bash
uv run python - <<'PY'
from clean_sweep_tui.cleaners.registry import all_steps
for step in all_steps():
    print(step.key, step.available, step.category.name, step.plugin)
PY
```

There is currently no dedicated test suite in the repository. For behavior changes, add focused tests if a test framework is introduced; otherwise run the smoke checks above and manually reason through the generated `Step` objects.

## Architecture

- `main.py` is a development entrypoint that calls `clean_sweep_tui.cli:main`.
- `clean_sweep_tui/cli.py` loads all steps, runs the TUI, then executes selected commands after the TUI exits.
- `clean_sweep_tui/tui.py` owns the Textual UI, selection state, preview rendering, and final confirmation modal.
- `clean_sweep_tui/cleaners/spec.py` defines `Category` and `Step`, the shared data contract.
- `clean_sweep_tui/cleaners/registry.py` controls built-in ordering and inserts preset plugins before `custom`.
- `clean_sweep_tui/cleaners/dev.py`, `system.py`, `user.py`, `logs.py`, and `custom.py` define built-in cleanup steps.
- `clean_sweep_tui/cleaners/presets.py` converts bundled and user JSON presets into plugin `Step` objects.
- `clean_sweep_tui/presets/*.json` are bundled app presets.

## Adding Or Changing Cleanup Items

When adding a built-in item:

1. Put the logic in the closest cleaner module.
2. Return a `Step` with a stable key, accurate `Category`, command list, availability check, unavailable reason, and short note.
3. Add the key to `ORDER` in `cleaners/registry.py`.
4. Update the README cleanup table and any related notes.

When adding an app-specific cleanup preset, prefer a JSON file under `clean_sweep_tui/presets/` instead of Python code. Presets support only path deletion via `rm -rf`; use `category` to control default selection and destructive marking.

## Coding Conventions

- Prefer small, explicit helper functions that return command lists.
- Quote filesystem paths with `shlex.quote` before embedding them in shell commands.
- Use structured parsing where available, but keep shell command previews literal and understandable.
- Keep comments concise and focused on safety or non-obvious shell behavior.
- Do not replace the shared selected set in TUI lists; mutate it in place so both list panes stay synchronized.
- Keep UI text in Chinese unless there is an existing reason to use English.

## Safety Review Checklist

Before finishing a deletion-related change, verify:

- Dangerous paths such as `/` and the home directory itself are rejected where user-provided paths are accepted.
- Commands delete contents vs. directories intentionally, and the README says which behavior applies.
- `sudo` commands have `needs_sudo=True` and show `sudo` in the actual command preview.
- Destructive categories are not selected by default.
- Availability checks do not create paths or perform destructive work.
