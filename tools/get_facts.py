"""MCP tool: retrieve device facts from the PTX via SSH (show version, show system information)."""
from tools.chassis_manager import get_chassis
from tools.common import run_cli_command_on_ptx, _log_tool_call

logger = __import__("logging").getLogger("ptx-mcp-server")


async def get_facts(chassis_id: str | None = None) -> str:
    """
    Retrieve device facts (model, version, serial, hostname, etc.) from a PTX chassis via SSH.
    Runs 'show version' and 'show system information' and returns the combined output.

    Args:
        chassis_id: ID of the target chassis from config/chassis.yml (e.g. "ch0"). If omitted and only one chassis is configured, it is used automatically.
    """
    _log_tool_call("TOOL: get_facts", chassis_id=chassis_id, started=True)
    try:
        chassis = get_chassis(chassis_id)
        out_parts = []
        for cmd in ("show version", "show system information"):
            _log_tool_call("TOOL: get_facts COMMAND", command=cmd)
            ok, out = run_cli_command_on_ptx(cmd, chassis)
            _log_tool_call(
                "TOOL: get_facts COMMAND RESULT",
                command=cmd,
                success=ok,
                output_len=len(out),
                output_preview=out[:400] if out else "(none)",
            )
            if ok:
                out_parts.append(f"--- {cmd} ---\n{out}")
            else:
                out_parts.append(f"--- {cmd} (error) ---\n{out}")
        _log_tool_call("TOOL: get_facts RESULT", parts=len(out_parts), success=len(out_parts) == 2)
        return "\n\n".join(out_parts) if out_parts else "No output."
    except Exception as e:
        _log_tool_call("TOOL: get_facts EXCEPTION", error=str(e), error_type=type(e).__name__)
        logger.error("get_facts: %s", e)
        return f"Error: {str(e)}"


def register(mcp):
    mcp.tool()(get_facts)
