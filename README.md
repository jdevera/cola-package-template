# COLA Package Template

A starter template for building command packages for [Criteo's Command Launcher](https://github.com/criteo/command-launcher).

## Quick Start

1. **Copy the template:**

   ```bash
   cp -r cola-template my-new-pkg
   cd my-new-pkg
   ```

2. **Rename the placeholders** (search for `# RENAME:` comments and `mypkg`):

   - `libs/python/mypkg/` — rename the directory to your launcher name
   - `manifest.mf` — update `pkgName` to your package name
   - `pyproject.toml` — update `name` to your package name

3. **Set up the package:**

   ```bash
   # If using as a dropin for local development:
   ln -s "$(pwd)" ~/.your-launcher/dropins/your-pkg
   your-launcher package setup your-pkg

   # Or run the setup hook directly:
   COLA_PACKAGE_DIR="$(pwd)" ./_hooks/setup-hook.sh
   ```

   The setup hook downloads `jdvlib.sh` (pinned in `jdvlib.version`) and runs `uv sync`.

4. **Update `config_registry.yml`** with your own configuration keys (delete the example group).

5. **Delete `commands/examples/`** and its entries in `manifest.mf` when you no longer need them.

## What's Included

### Commands

- **`cfg`** — Manage package configuration (`get`, `set`, `del`, `registry`, `status`)
- **`examples hello`** — Sample bash command showing shell library usage
- **`examples greet`** — Sample Python/Click command showing output formats and config

### `cola` Python Library (`libs/python/cola/`)

Shared across all your COLA packages. Don't add package-specific code here.

| Module | What it provides |
|--------|-----------------|
| `settings` | Lazy accessors for `COLA_*` env vars + OS-native directory helpers via `platformdirs` |
| `config` | `Config` (YAML store with dot-notation), `ConfigRegistry` (key validation), `ConfigClient` (declarative config requests) |
| `output` | `@output_format_options` decorator, `OutputFormat` constants, `resolve_format_from_options` |
| `cli` | `add_cola_completion_command` for launcher shell completion |

### Shell Libraries (`libs/sh/`)

- **`lib.sh`** — Entry point. Source this in bash commands: `source "${COLA_PACKAGE_DIR}/libs/sh/lib.sh"`
- **`cola.sh`** — Generic COLA helpers: `cola::launcher_name`, `cola::has_command`, `cola::complete`
- **`jdvlib.sh`** — Vendored bash utility library (downloaded by setup hook, do not edit)

### Manifest

`manifest.mf` is validated by `manifest.schema.yaml`. Add the following to the top of the manifest to get editor autocomplete with the YAML language server:

```yaml
# yaml-language-server: $schema=./manifest.schema.yaml
```

## Adding a New Command

### Python command

1. Create `commands/your_group/your_command.py` (or `commands/_no_group/` for ungrouped)
2. Use Click, import from `cola.*` as needed
3. Add to `manifest.mf`:

   ```yaml
   - name: your-command
     type: executable
     group: your-group
     short: What it does
     executable: '{{.PackageDir}}/pyrun.sh'
     args:
       - commands/your_group/your_command.py
   ```

### Bash command

1. Create `commands/your_group/your_command.sh` (make it executable)
2. Source lib.sh: `source "${COLA_PACKAGE_DIR}/libs/sh/lib.sh"`
3. Add to `manifest.mf`:

   ```yaml
   - name: your-command
     type: executable
     group: your-group
     short: What it does
     executable: '{{.PackageDir}}/commands/your_group/your_command.sh'
     args: []
   ```

## Adding Output Format Support

```python
from cola.output import OutputFormat, output_format_options, resolve_format_from_options

@click.command()
@click.pass_context
@output_format_options(OutputFormat.JSON, OutputFormat.TABLE, default=OutputFormat.TABLE)
def main(ctx, output_format, output_json, output_table):
    fmt = resolve_format_from_options(ctx, output_format=output_format,
                                      output_json=output_json, output_table=output_table)
    if fmt == OutputFormat.JSON:
        ...
```

## Reading Configuration

```python
from cola.config import ConfigClient

client = ConfigClient()
client.wants_entry("mail.server", description="SMTP server", default="localhost")
cfg = client.get(with_death=True)  # dies if required key missing and no default
print(cfg.mail_server)
```

Register keys in `config_registry.yml` so that `cfg set` validates them.

## Running Tests

```bash
uv run pytest
```

## Updating jdvlib.sh

Edit `jdvlib.version` with the new version tag, then re-run the setup hook.
