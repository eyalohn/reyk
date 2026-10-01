# Reyk

[![GitHub Stars](https://shieldcn.dev/github/eyalohn/reyk/stars.svg?variant=secondary&size=xs)](https://github.com/eyalohn/reyk)
[![Latest Version](https://shieldcn.dev/pypi/v/reyk.svg?variant=secondary&size=xs)](https://pypi.python.org/pypi/reyk/)
![Python Version](https://shieldcn.dev/pypi/python/reyk.svg?variant=secondary&size=xs)
[![CI](https://shieldcn.dev/github/eyalohn/reyk/ci.svg?variant=secondary&size=xs)](https://github.com/eyalohn/reyk/actions)
[![Coverage](https://shieldcn.dev/codecov/github/eyalohn/reyk.svg?variant=secondary&size=xs)](https://app.codecov.io/gh/eyalohn/reyk)
![License](https://shieldcn.dev/github/eyalohn/reyk/license.svg?variant=secondary&size=xs)
[![llms.txt](https://shieldcn.dev/badge/llms.txt.svg?variant=secondary&size=xs&logo=ri%3AFiFileText)](https://reyk.dev/llms-full.txt)

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
