# Juniper PTX MCP Server

Model Context Protocol (MCP) server for Juniper PTX chassis via **SSH only** (no NETCONF/RPC). Commands are executed over SSH and restricted by a regex allowlist.

## Features

- **SSH-only** — All PTX commands run over SSH; no PyEZ/NETCONF.
- **Central config** — Enable/disable tools and define allowed CLI commands in `config/tools.yml`.
- **Regex allowlist** — Only commands in `allowed_ssh_commands` are run (e.g. `show .*` allows all `show` commands).
- **Docker** — Consistent deployment.

## Quick Start

1. Copy `.env.example` to `.env` and set `PTX_HOST`, `PTX_USER`, `PTX_PASSWORD` (or `PTX_SSH_KEY`).
2. Edit `config/tools.yml` to list allowed tools and `allowed_ssh_commands` (e.g. `show .*`, `request .*`).
3. Run: `docker compose up -d`
4. MCP endpoint: `http://localhost:8001/mcp` (HTTP Stream transport)

**Cursor / MCP clients** — Add to your MCP config:

```json
{
  "mcpServers": {
    "ptx-mcp": {
      "url": "http://localhost:8001/mcp",
      "transport": "http"
    }
  }
}
```

## Config: `config/tools.yml`

- **tools** — Enable/disable each tool by name (`run_cli`, `read_var_log_messages_window`).
- **allowed_ssh_commands** — List of regex patterns. Only SSH commands matching one of these (from the start) are executed. Examples:
  - `show .*` — allow any command starting with `show `
  - `request .*` — allow any command starting with `request `

## Available Tools

All tools use the SSH layer (no NETCONF). Enable/disable each in `config/tools.yml`.

- **run_cli** — Run a single CLI command; must match `allowed_ssh_commands` in config.
- **get_facts** — Device facts (version, model, serial, etc.) via `show version` and `show system information`.
- **get_configuration** — Current config (text or set format) via `show configuration`.
- **edit_configuration** — Load and commit configuration (set or merge).
- **rollback_configuration** — Rollback to a previous config (e.g. rollback 0).
- **add_software** — Install software package via `request system software add` (path or URL).
- **read_var_log_messages_window** — Read local `/var/log` files (e.g. in the container) within a time window.

## Project Structure

```
├── server.py              # MCP server entrypoint
├── config/
│   └── tools.yml          # allowed_tools + allowed_ssh_commands (regex)
├── tools/                  # MCP tools (run_cli, read_var_log_messages_window, config_loader)
├── docs/                   # Documentation
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

## Documentation

| Doc | Description |
|-----|-------------|
| [docs/getting-started.md](docs/getting-started.md) | Services, Open WebUI, env vars, troubleshooting |
| [docs/config.md](docs/config.md) | config/tools.yml: allowed_tools, allowed_ssh_commands |
| [docs/remote-access.md](docs/remote-access.md) | Remote access and MCP session flow |
| [docs/architecture.md](docs/architecture.md) | Architecture and data flow |
| [docs/design.md](docs/design.md) | Design decisions |

## Requirements

- Docker & Docker Compose
- Juniper PTX reachable via SSH
- Network access to PTX management interface

## Troubleshooting

- **Container restarts** — `docker compose logs`; verify `.env` and that `config/tools.yml` exists and is valid YAML.
- **Command not allowed** — Ensure the command matches one of the `allowed_ssh_commands` patterns in `config/tools.yml`.
- **Auth failures** — Check `PTX_HOST`, `PTX_USER`, `PTX_PASSWORD` (or `PTX_SSH_KEY`).

## License

MIT
