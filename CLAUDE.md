# python-slugify: notes for Claude Code

Project rules live in AGENTS.md. Read it first.

- Run the tests with: `.venv/Scripts/python -m pytest -q` (all of them, every time).
- New tests go in a new file under `tests/`, never in `tests/test_legacy.py` (frozen).
- The default output must never change. New behaviour needs an explicit option.
- Keep the CLI's parsed-arguments shape: `tests/test_release.py` checks it.
- This clone is our fork (sysdr/python-slugify). Pull requests go to the fork's `master`, never upstream.
