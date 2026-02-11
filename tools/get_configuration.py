"""MCP tool: retrieve current configuration from the PTX via SSH."""
from tools.chassis_manager import get_chassis
from tools.common import run_cli_command_on_ptx

logger = __import__("logging").getLogger("ptx-mcp-server")


async def get_configuration(format: str = "text", chassis_id: str | None = None) -> str:
    """
    Retrieve the current configuration of a PTX chassis via SSH.

    Args:
        format: 'text' for hierarchical config, 'set' for set commands. Defaults to text.
        chassis_id: ID of the target chassis from config/chassis.yml (e.g. "ch0"). If omitted and only one chassis is configured, it is used automatically.
    """
    try:
        chassis = get_chassis(chassis_id)
        if format and format.strip().lower() == "set":
            cmd = "show configuration | display set"
        else:
            cmd = "show configuration"
        ok, out = run_cli_command_on_ptx(cmd, chassis, timeout_sec=120)
        if not ok:
            return f"Error:\n{out}"
        return out
    except Exception as e:
        logger.error("get_configuration: %s", e)
        return f"Error: {str(e)}"


def register(mcp):
    mcp.tool()(get_configuration)
