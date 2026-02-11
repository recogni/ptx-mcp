import logging

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

# Configure logging
logging.basicConfig(level=logging.INFO, format="[%(asctime)s][%(levelname)s]: %(message)s")
logger = logging.getLogger("ptx-mcp-server")

# SIMPLEST (INSECURE) MODE:
# Disable MCP DNS rebinding protection so requests with Host: ptx-mcp:8000 succeed.
# This is NOT recommended for production.
transport_security = TransportSecuritySettings(enable_dns_rebinding_protection=False)

# Initialize FastMCP server (bind to all interfaces for Docker)
mcp = FastMCP(
    "Juniper PTX Server",
    host="0.0.0.0",
    port=8000,
    transport_security=transport_security,
)

# Register all MCP tools (one tool per file under tools/)
from tools import register_all_tools

register_all_tools(mcp)

if __name__ == "__main__":
    logger.warning("⚠️  MCP DNS rebinding protection DISABLED (insecure mode)")
    logger.warning("⚠️  This should ONLY be used in lab/dev environments")
    print("Starting MCP server on 0.0.0.0:8000 with HTTP Stream transport")
    mcp.run(transport="streamable-http")
