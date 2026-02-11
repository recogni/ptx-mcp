"""MCP tool: add/install software package on the PTX via SSH (request system software add)."""
from tools.chassis_manager import get_chassis
from tools.common import run_cli_command_on_ptx

logger = __import__("logging").getLogger("ptx-mcp-server")


async def add_software(package_name: str, force: bool = False, chassis_id: str | None = None) -> str:
    """
    Add (install) a software package on a PTX chassis via SSH.
    Runs 'request system software add' with the given package path or URL.

    Args:
        package_name: Path or URL to the package (e.g. /var/tmp/junos-install.tgz or http://...).
        force: If true, add 'force' option to overwrite existing. Defaults to False.
        chassis_id: ID of the target chassis from config/chassis.yml (e.g. "ch0"). If omitted and only one chassis is configured, it is used automatically.
    """
    try:
        package_name = (package_name or "").strip()
        if not package_name:
            return "Error: package_name must be non-empty."
        chassis = get_chassis(chassis_id)
        cmd = "request system software add"
        if force:
            cmd += " force"
        cmd += f" {package_name}"
        ok, out = run_cli_command_on_ptx(cmd, chassis, timeout_sec=600)
        if not ok:
            return f"Error:\n{out}"
        return out
    except Exception as e:
        logger.error("add_software: %s", e)
        return f"Error: {str(e)}"


def register(mcp):
    mcp.tool()(add_software)
