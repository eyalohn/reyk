# Can be installed on Windows with GNUWin32 or Chocolatey

specific_libraries_test := tests/blackbox/specific_libraries
specific_libraries_test_libs := $(specific_libraries_test)/test_libs

uv:
	@uv -V || echo 'uv is not installed. Install via: https://docs.astral.sh/uv/getting-started/installation/'

install: uv
	uv sync --frozen --all-groups --all-extras --all-packages
	uv run pre-commit install --install-hooks

install-test-libs: $(specific_libraries_test_libs)

$(specific_libraries_test_libs):
	uv pip install -r $(specific_libraries_test)/requirements.txt --target $(specific_libraries_test_libs)

test-library: install install-test-libs
	uv run coverage run -m pytest -v tests/

test-library-memray: install install-test-libs
	uv run pytest -v tests/ --memray

test-cli: install install-test-libs
	uv run coverage run -m pytest -v pyisolate-cli/tests/

# The --append flag is needed to combine the coverage data from both test-library and test-cli
test: install install-test-libs
	mkdir -p coverage
	rm -f coverage/.coverage.*
	$(MAKE) COVERAGE_FLAGS=--append test-library
	$(MAKE) COVERAGE_FLAGS=--append test-cli

testcov: test
	@echo "building coverage html"
	@uv run coverage html

update-dependencies: uv
	uv lock --upgrade
