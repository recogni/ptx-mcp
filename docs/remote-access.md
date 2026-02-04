# Remote Access

## URLs

- **MCP**: `http://<your-server-ip>:8001/mcp`
- **Open WebUI**: `http://<your-server-ip>:3001`

Server listens on `0.0.0.0`; ensure firewall allows ports 8001 and 3001.

## Testing Connectivity

```bash
# From remote machine (replace <your-server-ip>)
nc -zv <your-server-ip> 8001
curl -v http://<your-server-ip>:8001/mcp   # 406 is expected without proper MCP headers
```

## MCP Session (Streamable HTTP)

The server is session-based. Clients must:

1. **POST** `initialize` to the MCP URL and read **`Mcp-Session-Id`** from response headers.
2. **POST** `notifications/initialized` with header `Mcp-Session-Id: <value>`.
3. Send all later requests (e.g. `tools/list`, `tools/call`) with the same **`Mcp-Session-Id`** header.

A plain GET to `/mcp` returns 400 or 406; use the POST flow above.

## Client Configuration

Point your MCP client (Cursor, Claude Desktop, etc.) at `http://<your-server-ip>:8001/mcp` with transport `http`. Open WebUI: open `http://<your-server-ip>:3001` in a browser.

## Troubleshooting

- **Connection refused / timeout** — Check firewall and that the server is running (`docker compose ps`). On the server: `netstat -tlnp | grep 8001`.
- **"Missing session ID"** — Use the initialize → initialized → subsequent requests flow with `Mcp-Session-Id`.
- **406 Not Acceptable** — Client must send `Accept: application/json, text/event-stream` (or include `text/event-stream`).

## Nginx Reverse Proxy (HTTPS)

Example snippet for terminating SSL and proxying to localhost:

```nginx
server {
    listen 443 ssl;
    server_name <your-server-hostname>;
    ssl_certificate /etc/ssl/certs/server.crt;
    ssl_certificate_key /etc/ssl/private/server.key;

    location /mcp {
        proxy_pass http://localhost:8001/mcp;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location / {
        proxy_pass http://localhost:3001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

For production, add authentication and restrict access (e.g. VPN, IP allowlist).
