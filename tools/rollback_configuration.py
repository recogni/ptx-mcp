"""MCP tool: rollback configuration on the PTX via SSH."""
from tools.chassis_manager import get_chassis
from tools.common import run_cli_stdin_on_ptx

logger = __import__("logging").getLogger("ptx-mcp-server")


async def rollback_configuration(rollback_id: int = 0, chassis_id: str | None = None) -> str:
    """
    Rollback the configuration to a previous state via SSH.
    Runs configure private, rollback <id>, commit, exit.

    Args:
        rollback_id: Rollback configuration ID (0 = most recent). Defaults to 0.
        chassis_id: ID of the target chassis from config/chassis.yml (e.g. "ch0"). If omitted and only one chassis is configured, it is used automatically.
    """
    try:
        chassis = get_chassis(chassis_id)
        stdin_content = f"configure private\nrollback {rollback_id}\ncommit\nexit\n"
        ok, out = run_cli_stdin_on_ptx("cli", stdin_content, chassis, timeout_sec=90)
        if not ok:
            return f"Error:\n{out}"
        return out
    except Exception as e:
        logger.error("rollback_configuration: %s", e)
        return f"Error: {str(e)}"


def register(mcp):
    mcp.tool()(rollback_configuration)
