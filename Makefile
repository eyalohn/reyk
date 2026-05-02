# Can be installed on Windows with GNUWin32 or Chocolatey

specific_libraries_test := tests/blackbox/specific_libraries
specific_libraries_test_libs := $(specific_libraries_test)/test_libs

.PHONY: uv
uv:
	@uv -V || echo 'uv is not installed. Install via: https://docs.astral.sh/uv/getting-started/installation/'

.PHONY: install
install: uv
	uv sync --frozen --all-groups --all-extras --all-packages
	uv run pre-commit install --install-hooks

install-test-libs: $(specific_libraries_test_libs)

$(specific_libraries_test_libs):
	uv pip install -r $(specific_libraries_test)/requirements.txt --target $(specific_libraries_test_libs)

test-library: install install-test-libs
	mkdir -p coverage
	uv run coverage run -m pytest -v tests/

test-library-memray: install install-test-libs
	uv run pytest -v tests/ --memray

test-cli: install install-test-libs
	mkdir -p coverage
	uv run coverage run -m pytest -v pyisolate-cli/tests/

test: test-library test-cli

.PHONY: testcov  ## Run tests and generate a coverage report
testcov: test
	@echo "building coverage html"
	@uv run coverage html

.PHONY: update-dependencies
update-dependencies: uv
	uv lock --upgrade
