# Contributing to Reyk

## Development setup

Use Python 3.9 or newer, `uv`, and Make. `.python-version` selects Python 3.12 for local development.
On Windows, Make is available through GNUWin32 or Chocolatey.

From the repository root:

```bash
make install
make install-hooks
```

`make install` runs `uv sync --frozen --all-groups --all-extras --all-packages`.
It installs the development environment for both `reyk` and `reyk-cli`, including all dependency groups
and extras, using the existing `uv.lock` without updating it. It can download packages and Python.
`--frozen` does not check whether the lockfile matches the project metadata; use `uv lock --check`
to check that separately. `make install-hooks` installs Git hooks and can download their environments.

## Implementation and style

Agree on intended behavior and exclusions before substantial implementation. Preserve behavior during
refactors and identify behavioral changes separately. Follow nearby code and existing helpers before
introducing abstractions or dependencies. Keep the runtime compatible with Python 3.9 and preserve its
dependency-free design unless the task explicitly changes it.

Ruff controls formatting and lint rules, with a 120-character line limit. Pyright checks Python types.
The pre-commit configuration also checks spelling, YAML/TOML, and merge conflicts. For example:

```bash
make lint
make lint FILES="reyk/import_resolution.py reyk/vendor_importer.py"
make lint HOOK=pyright
```

Some hooks rewrite files, including Ruff's lint fixes and formatting. Review the resulting diff.
`make lint` runs all configured checks on all tracked files; its branch-protection hook may
reject the current branch. CI skips that hook and runs the remaining checks.

## Choosing tests

Run these commands from the repository root after `make install`:

| Command | Scope and setup |
| --- | --- |
| `make test-library-fast` | Internal tests, generated black-box import tests, and distribution-finder tests. No real-library installation prerequisite. |
| `make test-real-libraries` | Real-library compatibility tests; installs test libraries if their directory is absent. |
| `make test-cli` | CLI tests; includes environment and real-library setup through existing prerequisites. CLI commands invoke `uv` and may download packages. |
| `make test` | Runtime and CLI suites with combined coverage; includes setup. |
| `make testcov` | Full tests followed by coverage reports. |
| `make test-library-memray` | Runtime tests with Memray on supported platforms; includes setup. |

The focused targets use `uv run --frozen`; they can still download missing environment dependencies.
Use a direct pytest invocation for a particular file or case:

```bash
uv run --frozen pytest tests/blackbox/predefined_tests/test_isolator_blackbox.py -q
```

Internal tests cover helpers and configuration. Generated black-box tests create small example packages
through shared fixtures and exercise real import behavior. Reuse their file managers and import-form
parameterization for routing regressions. Real-library tests cover compatibility with installed dependencies,
including native extensions; their inputs live in the ignored `tests/blackbox/specific_libraries/test_libs/`.
`make update-test-libs` explicitly refreshes that installation and may download dependencies.

Behavioral fixes should include a reproducer and regression case. For import changes, cover the affected
import forms and observable behavior, including errors and module identity where relevant. Mechanical
refactors can rely on existing coverage. Run focused checks while iterating and broader checks when the
change is coherent. CI tests Python 3.9–3.14 across Linux, macOS, and Windows, with separate Memray checks.
Report the command, interpreter, scope, and any unrun checks; one local run does not cover that matrix.

## Debugging test files

Pytest temporary directories are not retained by default, including those from failed tests.
Cleanup is best effort at normal process exit; it does not reduce peak usage within a large run.
Real-library tests copy installed dependencies into temporary example projects for each test.

To retain files for inspection after the full suite:

```bash
make test-debug
```

For an individual Make target, use `RETENTION=all` or `RETENTION=failed`:

```bash
make test-library-fast RETENTION=all
make test-real-libraries RETENTION=failed
```

For direct pytest runs, use `-o tmp_path_retention_policy=all` (or `failed`).
Debug mode changes retention only; it does not start a debugger or change test selection.

## Documentation site

The Next.js/Fumadocs site is maintained separately from the Python workspace:

```bash
cd docs
npm ci
npm run dev
```

Edit user-facing documentation in `content/docs/`. For site changes, run `npm run types:check`
and `npm run build` from `docs/`. Installation and builds may require network access.
