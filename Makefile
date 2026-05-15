# Can be installed on Windows with GNUWin32 or Chocolatey

specific_libraries_test := tests/blackbox/specific_libraries
specific_libraries_test_libs := $(specific_libraries_test)/test_libs

uv:
	@uv -V || echo 'uv is not installed. Install via: https://docs.astral.sh/uv/getting-started/installation/'

install-hooks: uv
	uv run pre-commit install --install-hooks

install: uv
	uv sync --frozen --all-groups --all-extras --all-packages

install-test-libs: $(specific_libraries_test_libs)

$(specific_libraries_test_libs):
	CLI_PATH="$$(pwd)/pyisolate-cli"; \
	cd $(specific_libraries_test); \
	uvx "$$CLI_PATH" sync

test-library: install install-test-libs
	uv run coverage run $(COVERAGE_FLAGS) -m pytest -v tests/

test-library-memray: install install-test-libs
	uv run pytest -v tests/ --memray

test-cli: install install-test-libs
	uv run coverage run $(COVERAGE_FLAGS) -m pytest -v pyisolate-cli/tests/

# The --append flag is needed to combine the coverage data from both test-library and test-cli
test: install install-test-libs
	mkdir -p coverage
	rm -f coverage/.coverage.*
	"$(MAKE)" COVERAGE_FLAGS=--append test-library
	"$(MAKE)" COVERAGE_FLAGS=--append test-cli

testcov: test
	uv run coverage report
	@echo "building coverage lcov"
	uv run coverage lcov
	@echo "building coverage html"
	uv run coverage html

update-dependencies: uv
	uv lock --upgrade
