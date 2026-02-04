# Getting Started

## Services

| Service       | URL                  | Purpose                    |
|---------------|----------------------|----------------------------|
| PTX MCP Server| http://localhost:8001 | MCP server (tools at `/mcp`) |
| Open WebUI    | http://localhost:3001 | Web UI for AI + MCP        |

## Quick Commands

```bash
docker compose up -d          # Start
docker compose ps             # Status
docker compose logs -f        # Logs (all)
docker compose down           # Stop
```

## Open WebUI

1. Open http://localhost:3001 and create an account.
2. In **Admin Panel → Settings → Connections**, add an OpenAI-compatible API (e.g. Ollama, OpenAI).
3. Chat; the MCP tools are available to the model. Example prompts: *"Get facts from the PTX chassis"*, *"Show hardware inventory"*, *"Get current configuration in text format"*.

## Connecting Other Clients

**Cursor / Claude Desktop** — Add to MCP config:

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

For remote access, use `http://<your-server-ip>:8001/mcp`. See [Remote Access](remote-access.md).

## Environment Variables

Copy `.env.example` to `.env` and set:

- `PTX_HOST` — PTX hostname or IP
- `PTX_USER` — Login username
- `PTX_PASSWORD` — Login password
- `PTX_PORT` — Optional; default 22
- `PTX_SSH_KEY` — Optional; path to SSH private key (preferred over password)

## Troubleshooting

**Test PTX connection:**

```bash
docker exec ptx-mcp-server python -c "
from tools.common import run_cli_command_on_ptx
ok, out = run_cli_command_on_ptx('show version')
print('OK:', out[:80] if ok else out)
"
```

**Container restarts** — Check `docker compose logs`. Ensure `.env` has valid `PTX_HOST`, `PTX_USER`, `PTX_PASSWORD` (or `PTX_SSH_KEY`).

**Port in use** — Change host port in `docker-compose.yml` (e.g. `"8002:8000"`).

## Security

This setup is for **lab/development**. For production: use SSH keys, HTTPS, and restrict network access. Do not commit `.env`.
