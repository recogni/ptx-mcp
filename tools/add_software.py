"""MCP tool: add/install software package on the PTX via SSH (request system software add)."""
from tools.common import run_cli_command_on_ptx

logger = __import__("logging").getLogger("ptx-mcp-server")


async def add_software(package_name: str, force: bool = False) -> str:
    """
    Add (install) a software package on the PTX via SSH.
    Runs 'request system software add' with the given package path or URL.

    Args:
        package_name: Path or URL to the package (e.g. /var/tmp/junos-install.tgz or http://...).
        force: If true, add 'force' option to overwrite existing. Defaults to False.
    """
    try:
        package_name = (package_name or "").strip()
        if not package_name:
            return "Error: package_name must be non-empty."
        cmd = "request system software add"
        if force:
            cmd += " force"
        cmd += f" {package_name}"
        ok, out = run_cli_command_on_ptx(cmd, timeout_sec=600)
        if not ok:
            return f"Error:\n{out}"
        return out
    except Exception as e:
        logger.error("add_software: %s", e)
        return f"Error: {str(e)}"


def register(mcp):
    mcp.tool()(add_software)
