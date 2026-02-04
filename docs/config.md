# Tool configuration

All tool behavior is controlled by `config/tools.yml` (or the path in `PTX_TOOLS_CONFIG`).

## Enable/disable tools

```yaml
allowed_tools:
  - run_cli
  - get_facts
  - get_configuration
  - edit_configuration
  - rollback_configuration
  - add_software
  - read_var_log_messages_window
```

Only tools in the list are registered. Built-in tools (get_facts, get_configuration, etc.) use SSH directly; only **run_cli** is restricted by `allowed_ssh_commands`.

## Allowed SSH commands (allowlist)

The `run_cli` tool runs commands on the PTX via SSH. Only commands that match one of the **regex** patterns in `allowed_ssh_commands` are executed. Patterns are matched from the **start** of the command.

```yaml
allowed_ssh_commands:
  - "show .*"      # any command starting with "show "
  - "request .*"   # any command starting with "request "
```

Examples:

- `show version` → allowed by `show .*`
- `show configuration` → allowed
- `request system reboot` → allowed by `request .*`
- `configure` → not allowed unless you add a pattern that matches it

Invalid regex entries are logged and skipped.
