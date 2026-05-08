# PyIsolate

[![Tests](https://github.com/OughtToPrevail/PyIsolate/actions/workflows/test.yml/badge.svg)](https://github.com/OughtToPrevail/PyIsolate/actions/workflows/test.yml)

**PyIsolate** enables code inside your package to import vendored libraries while code outside your package continues using the system/global versions.

We leverage Python's import system internals to achieve transparent dependency isolation.

## Features

- 🎯 **Zero Configuration**: Enable isolation with a single function call
- 🔒 **Dependency Isolation**: Avoid conflicts by shipping libraries with your package
- 🔄 **Version Flexibility**: Run multiple versions of the same library in one process
- 📦 **Transparent Imports**: Keep your public imports unchanged (`import requests` still works)
- 🚀 **Lightweight**: Minimal overhead with a tiny import hook

## Documentation

For detailed documentation, examples, and API reference, visit the [documentation site](https://pyisolate.vercel.app).

## Limitations

- Multi-threaded applications are not supported.
