## Testing & Coverage

- Always use `./test.sh` to run tests and check code coverage.
- The coverage report is generated at `coverage/coverage.json`.
- Review the coverage report to ensure your changes maintain or improve test coverage.
- For details on coverage tracking and pre-commit hooks, see the notes below.

## Pre-commit & Coverage Notes

- If a **pre-commit** hook modifies `.coverage_total`, you **must add it to the commit** before retrying:
  ```bash
  git add .coverage_total
  git commit -m "<your message>"
  ```
  If the commit was aborted with "files were modified by this hook", staging the file and re-running the commit is enough.
- Do **not** skip hooks; only use `--no-verify` in emergencies. The goal is to keep the tracked coverage summary in sync with the code.
