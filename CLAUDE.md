# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project state

This is a brand-new PyCharm project ("AI_HR", under "HR AI化" — an HR AI-transformation project). It currently contains no real application code, no dependency manifest, no test framework, and no lint/build configuration. The only source file is `main.py`, which is the default PyCharm starter script (`print_hi`). Treat any commands or structure not yet present as yet-to-be-created, and introduce them incrementally as the project takes shape.

## Running

- Run the entry script: `python main.py` (or use the PyCharm "main" run configuration / Shift+F10).
- There is no test runner or linter configured yet; a single-test command does not exist until tests are added.

## Environment

- Windows 10, shell is PowerShell (the Bash tool is also available and uses Git Bash/POSIX syntax).
- The PyCharm `.idea` config uses a bundled Python SDK (`IS_MODULE_SDK`, no fixed interpreter path). The `main.py` starter is Python 3 style.
- `.claude/settings.json` enables the `superpowers` plugin, so its skills are available in this session.
