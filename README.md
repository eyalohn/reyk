# Reyk

[![Tests](https://github.com/OughtToPrevail/reyk/actions/workflows/test.yml/badge.svg)](https://github.com/OughtToPrevail/reyk/actions/workflows/test.yml)
[![Coverage](https://coverage-badge.samuelcolvin.workers.dev/OughtToPrevail/reyk.svg)](https://coverage-badge.samuelcolvin.workers.dev/redirect/OughtToPrevail/reyk)
[![Latest Version](https://img.shields.io/pypi/v/reyk.svg)](https://pypi.python.org/pypi/reyk/)
[![Python Versions](https://img.shields.io/pypi/pyversions/reyk.svg)](https://pypi.python.org/pypi/reyk/)
[![llms.txt](https://img.shields.io/badge/llms.txt-green)](https://reyk.dev/llms-full.txt)

Run conflicting Python dependencies in one process — with vendored isolation.

[Reyk](https://reyk.dev) lets you **vendor Python dependencies into your project and isolate them by design**, without changing how you write imports. We leverage Python's import system internals to achieve transparent dependency isolation.

## Features

- **Zero Configuration**: Enable isolation with a single function call
- **Dependency Isolation**: Avoid conflicts by shipping libraries with your package
- **Version Flexibility**: Run multiple versions of the same library in one process
- **Transparent Imports**: Keep your public imports unchanged (`import requests` still works)
- **Lightweight**: Minimal overhead with a tiny import hook

# Installation

You can install Reyk from PyPI:

```bash
uv add reyk
```

Enable isolation from your package's `__init__.py`:

```python
from reyk.isolator import isolate_package

isolate_package()
```

Then, vendor your dependencies with Reyk's CLI:

```bash
uvx reyk-cli add requests==2.25.1
```

**That's it!** Inside `your_package`, `import requests` resolves to `your_package.libs.requests`. Outside `your_package`, `import requests` continues to resolve to the global installation.

## Documentation

For detailed documentation, examples, and API reference, visit the documentation site at https://reyk.dev.

## Limitations

- Multi-threaded applications are not supported.
