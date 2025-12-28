from pathlib import Path
import shutil


class ExampleProjectFileManager:
    def __init__(self, project_path: Path, libraries_dir_relative_path: Path) -> None:
        self._project_path = project_path
        self._libraries_dir_relative_path = libraries_dir_relative_path
        self._created_files = set[Path]()
        self._created_directories = set[Path]()

    def create_library_module(
        self,
        library_name: str,
        module_name: str,
        content: str,
    ) -> Path:
        return self.create_library_file(
            file_name=self._convert_module_name_to_file_name(module_name),
            content=content,
            library_name=library_name,
        )

    def create_library_file(
        self,
        library_name: str,
        file_name: str,
        content: str,
    ) -> Path:
        return self.create_project_file(
            file_name=str(self._libraries_dir_relative_path / library_name / file_name),
            content=content,
        )

    def create_project_module(self, module_name: str, content: str) -> Path:
        return self.create_project_file(
            file_name=self._convert_module_name_to_file_name(module_name),
            content=content,
        )

    def create_project_file(self, file_name: str, content: str) -> Path:
        project_file = self._project_path / file_name
        if not project_file.parent.exists():
            project_file.parent.mkdir()
            self._created_directories.add(project_file.parent)

        project_file.write_text(content)
        self._created_files.add(project_file)
        return project_file

    def _convert_module_name_to_file_name(self, module_name: str) -> str:
        return module_name.replace(".", "/") + ".py"

    def remove_pycache_directories(self) -> None:
        for pycache_directory in self._project_path.rglob("__pycache__"):
            if pycache_directory.is_dir():
                shutil.rmtree(pycache_directory)

    def cleanup_files(self) -> None:
        self.remove_pycache_directories()

        for file in self._created_files:
            file.unlink()

        for directory in self._created_directories:
            shutil.rmtree(directory, ignore_errors=True)

        self._created_files.clear()
        self._created_directories.clear()
