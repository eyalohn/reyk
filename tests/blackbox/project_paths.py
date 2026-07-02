from pathlib import Path


EXAMPLE_PROJECT_NAME = "example_project"
EXAMPLE_PROJECT_PATH = Path(__file__).parent / EXAMPLE_PROJECT_NAME
EXAMPLE_PROJECT_LIBRARIES_DIRECTORY_RELATIVE_PATH = Path("libs")
EXAMPLE_PROJECT_LIBRARIES_PATH = EXAMPLE_PROJECT_PATH / EXAMPLE_PROJECT_LIBRARIES_DIRECTORY_RELATIVE_PATH

TEST_LIBRARIES_DIRECTORY_PATH = Path(__file__).parent / "test_libraries"
SPECIFIC_LIBRARIES_INSTALLATION_PATH = Path(__file__).parent / "specific_libraries" / "test_libs"

LOCKED_FILES_PENDING_DELETION_PATH = Path(__file__).parent / "locked_files_pending_deletion"
