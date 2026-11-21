# Working on Reyk

- Read [CONTRIBUTING.md](CONTRIBUTING.md) for setup and verification commands.
- Preserve existing behavior during refactors. Describe intended behavior changes and
  exclusions before substantial implementation; newly discovered cases do not automatically expand scope.
- Keep Python 3.9 compatibility. The core runtime has no dependencies; adding one is an explicit design decision.
- Follow nearby code and the configured Ruff/Pyright checks. Avoid unrelated formatting or abstractions.
- Keep actual import calls in the importer overrides: extra stack depth matters here.
  The communication interfaces in `reyk/isolator_definition.py` also require cross-version compatibility.
- Runtime code lives in `reyk/`; the CLI is a separate workspace package in `reyk-cli/`;
  the documentation site lives in `docs/`. Tests distinguish internal, generated black-box,
  real-library, and CLI behavior.
- Treat `tests/blackbox/specific_libraries/test_libs/` as installed test inputs.
  Exclude it from routine searches and never fix bugs by editing installed libraries.
- For behavioral fixes, reproduce the issue and add relevant regression coverage.
  Reuse existing coverage for mechanical changes; run broader checks at coherent milestones.
- Report commands, interpreter, tested scope, and any checks not run. Local focused tests
  do not establish that the Python/OS CI matrix passed. Preserve unrelated working-tree changes.
