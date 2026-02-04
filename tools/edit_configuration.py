"""MCP tool: modify configuration on the PTX via SSH (configure private, load merge/set, commit)."""
from tools.common import run_cli_stdin_on_ptx

logger = __import__("logging").getLogger("ptx-mcp-server")


async def edit_configuration(
    config_text: str,
    format: str = "set",
    commit: bool = True,
) -> str:
    """
    Load configuration into the PTX via SSH and optionally commit.

    Uses 'configure private', then 'load merge terminal' (text) or 'load set terminal' (set),
    then optionally 'commit'. Configuration is sent on stdin.

    Args:
        config_text: The configuration to load (set commands or hierarchical text).
        format: 'set' for set-style lines, 'text' for hierarchical. Defaults to set.
        commit: If true, commit after loading. Defaults to True.
    """
    try:
        config_text = (config_text or "").strip()
        if not config_text:
            return "Error: config_text must be non-empty."
        load_cmd = "load set terminal" if (format or "set").strip().lower() == "set" else "load merge terminal"
        # Junos: configure private, load ... terminal (reads until EOF), then commit and exit
        stdin_content = f"configure private\n{load_cmd}\n{config_text}\n"
        if commit:
            stdin_content += "commit\n"
        stdin_content += "exit\n"
        ok, out = run_cli_stdin_on_ptx("cli", stdin_content, timeout_sec=120)
        if not ok:
            return f"Error:\n{out}"
        return out
    except Exception as e:
        logger.error("edit_configuration: %s", e)
        return f"Error: {str(e)}"


def register(mcp):
    mcp.tool()(edit_configuration)
