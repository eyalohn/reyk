from pathlib import Path
from pyisolate_cli.configuration_reader import DEFAULT_LIBRARIES_TARGET_PATH


class ExampleProject:
    def __init__(self, project_path: Path) -> None:
        self._project_path = project_path
    
    def get_existing_libraries(self) -> set[str]:
        # TODO: Implement
        return {}
