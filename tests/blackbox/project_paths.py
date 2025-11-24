from pathlib import Path


PROJECT_PATH = Path(__file__).parent / "example_project"
LIBRARIES_DIRECTORY_RELATIVE_PATH = Path("libs")
LIBRARIES_PATH = PROJECT_PATH / LIBRARIES_DIRECTORY_RELATIVE_PATH
LOCKED_FILES_PENDING_DELETION_PATH = Path(__file__).parent / "locked_files_pending_deletion"
