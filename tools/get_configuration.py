"""MCP tool: retrieve current configuration from the PTX via SSH."""
from tools.common import run_cli_command_on_ptx

logger = __import__("logging").getLogger("ptx-mcp-server")


async def get_configuration(format: str = "text") -> str:
    """
    Retrieve the current configuration of the PTX chassis via SSH.

    Args:
        format: 'text' for hierarchical config, 'set' for set commands. Defaults to text.
    """
    try:
        if format and format.strip().lower() == "set":
            cmd = "show configuration | display set"
        else:
            cmd = "show configuration"
        ok, out = run_cli_command_on_ptx(cmd, timeout_sec=120)
        if not ok:
            return f"Error:\n{out}"
        return out
    except Exception as e:
        logger.error("get_configuration: %s", e)
        return f"Error: {str(e)}"


def register(mcp):
    mcp.tool()(get_configuration)
