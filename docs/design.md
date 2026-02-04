# Design Decisions

Key design choices for the Juniper PTX MCP Server.

1. **SSH-only** — No NETCONF/RPC; all commands run over SSH. Simpler stack and no PyEZ dependency.
2. **Central YAML config** — `config/tools.yml` enables/disables tools and defines the CLI allowlist (regex). Single place to lock down what can run.
3. **Regex allowlist** — Only commands in `allowed_ssh_commands` are executed (e.g. `show .*`). Reduces risk of arbitrary commands.
4. **Docker** — Consistent environment and deployment.
5. **Environment variables for credentials** — No secrets in code; 12-factor style.
6. **SSH key support (`PTX_SSH_KEY`)** — Preferred over password for production.
7. **Docker Compose V2** — Modern plugin; avoids V1 issues with newer Docker.
8. **Bind to 0.0.0.0** — Container accepts external connections.
9. **HTTP Stream transport** — `streamable-http`; avoids deprecated SSE and SDK initialization bugs.
