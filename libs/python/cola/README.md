# cola — Generic Command Launcher Library

This package provides shared utilities for any Command Launcher (COLA) package.
It is **the same across all your packages** — don't add package-specific code here.

## Modules

- **settings** — Lazy accessors for `COLA_*` environment variables and OS-native directory helpers
- **config** — YAML-backed config store, registry validation, declarative `ConfigClient`
- **output** — `@output_format_options` decorator for standardized `--output-format`/`--json`/etc. flags
- **cli** — Click utilities including `add_cola_completion_command` for launcher integration

## Package-specific code

Put your package-specific Python code in the sibling `mypkg/` directory (renamed to your launcher name).
