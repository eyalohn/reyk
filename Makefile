# Can be installed on Windows with GNUWin32 or Chocolatey

specific_libraries_test := tests/blackbox/specific_libraries
specific_libraries_test_libs := $(specific_libraries_test)/test_libs

# Optional pytest retention override: all, failed, or none.
# Use `make test-debug` to retain all temporary test files.
retention_args = $(if $(RETENTION),-o tmp_path_retention_policy=$(RETENTION))

.PHONY: uv install-hooks install lint install-test-libs update-test-libs \
	test-library-fast test-real-libraries test-library test-library-memray test-cli test test-debug testcov update-dependencies

uv:
	@uv -V || echo 'uv is not installed. Install via: https://docs.astral.sh/uv/getting-started/installation/'

install-hooks: uv
	uv run pre-commit install --install-hooks

install: uv
	uv sync --frozen --all-groups --all-extras --all-packages

# Optionally select a hook with HOOK=pyright or files with FILES="path/to/file ...".
lint:
	uv run --frozen pre-commit run $(HOOK) $(if $(FILES),--files $(FILES),--all-files)

install-test-libs: $(specific_libraries_test_libs)

$(specific_libraries_test_libs):
	$(MAKE) update-test-libs

update-test-libs:
	CLI_PATH="$(abspath reyk-cli)"; \
	cd $(specific_libraries_test); \
	uvx "$$CLI_PATH" sync

# Assumes `make install` has already prepared the development environment.
test-library-fast:
	uv run --frozen pytest $(retention_args) -q tests/internals tests/blackbox/predefined_tests tests/blackbox/test_distributions_finder.py

test-real-libraries: install-test-libs
	uv run --frozen pytest $(retention_args) -v $(specific_libraries_test)

test-library: install install-test-libs
	uv run coverage run $(COVERAGE_FLAGS) -m pytest $(retention_args) -vv tests/

test-library-memray: install install-test-libs
	uv run pytest $(retention_args) -v tests/ --memray

test-cli: install install-test-libs
	uv run coverage run $(COVERAGE_FLAGS) -m pytest $(retention_args) -vv reyk-cli/tests/

# The --append flag is needed to combine the coverage data from both test-library and test-cli
test: install install-test-libs
	mkdir -p coverage
	rm -f coverage/.coverage.*
	"$(MAKE)" COVERAGE_FLAGS=--append test-library
	"$(MAKE)" COVERAGE_FLAGS=--append test-cli

test-debug:
	$(MAKE) RETENTION=all test

testcov: test
	uv run coverage report
	@echo "building coverage lcov"
	uv run coverage lcov
	@echo "building coverage html"
	uv run coverage html

update-dependencies: uv
	uv lock --upgrade
