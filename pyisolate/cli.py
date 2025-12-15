try:
    from pyisolate_cli.main import app as cli_app

except ImportError:  # pragma: no cover
    cli_app = None  # type: ignore


def main() -> None:
    if not cli_app:  # type: ignore[truthy-function]
        message = 'To use the pyisolate command, please install "pyisolate[cli]":\n\n\tpip install "pyisolate[cli]"\n'
        print(message)
        raise RuntimeError(message)  # noqa: B904
    cli_app()
