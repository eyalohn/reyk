from abc import ABC, abstractmethod
import os


class InstallationMethod(ABC):
    def install_from_requirements_list(self, requirements: str, target_directory: str) -> None:
        ...
    
    def install_from_pyproject(self, requirements: str, target_directory: str) -> None:
        ...


class PipInstallationMethod(InstallationMethod):
    def install_from_requirements_list(self, requirements: str, target_directory: str) -> None:
        os.system("pip install ")
    
    def install_from_pyproject(self, requirements: str, target_directory: str) -> None:
        return super().install_from_pyproject(requirements, target_directory)


def install_requirements(requirements: str, target_directory: str, installation_method: InstallationMethod) -> None:
    ...


def build_installation_command(
    requirements: str,
    target_directory: str,
    installation_method: InstallationMethod,
) -> str:
    return f"{installation_method.value}"
