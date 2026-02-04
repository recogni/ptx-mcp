"""MCP tool: run allowed CLI commands on the PTX via SSH (allowlist with regex)."""
from tools.common import run_cli_command_on_ptx, _log_tool_call
from tools.config_loader import is_command_allowed

logger = __import__("logging").getLogger("ptx-mcp-server")


async def run_cli(command: str) -> str:
    """
    Run a single CLI command on the PTX chassis via SSH.

    Only commands that match the allowlist in config/tools.yml (allowed_ssh_commands) are executed.
    Example: "show .*" allows any command starting with "show " (e.g. "show version", "show configuration").

    Args:
        command: Full CLI command to run (e.g. "show version", "show system users").
    """
    cmd = (command or "").strip()
    _log_tool_call("TOOL: run_cli", command=cmd or "(empty)", allowed=None)
    try:
        if not cmd:
            _log_tool_call("TOOL: run_cli RESULT", result="rejected", reason="command empty")
            return "Error: command must be non-empty."
        allowed = is_command_allowed(cmd)
        _log_tool_call("TOOL: run_cli ALLOWLIST", command=cmd, allowed=allowed)
        if not allowed:
            _log_tool_call("TOOL: run_cli RESULT", result="rejected", reason="not in allowlist")
            return (
                "Error: command is not allowed by the configured allowlist (allowed_ssh_commands in config/tools.yml). "
                "Only commands matching one of the regex patterns are permitted."
            )
        ok, output = run_cli_command_on_ptx(cmd)
        _log_tool_call(
            "TOOL: run_cli RESULT",
            success=ok,
            output_len=len(output),
            output_preview=output[:400] if output else "(none)",
        )
        if not ok:
            return f"Error running CLI command:\n{output}"
        return output
    except Exception as e:
        _log_tool_call("TOOL: run_cli EXCEPTION", error=str(e), error_type=type(e).__name__)
        logger.error("run_cli: %s", e)
        return f"Error: {str(e)}"


def register(mcp):
    """Register this tool with the FastMCP server."""
    mcp.tool()(run_cli)
