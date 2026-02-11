"""MCP tool: list all configured PTX chassis."""
from tools.chassis_manager import list_all_chassis


async def list_chassis() -> str:
    """
    List all available PTX chassis and their IDs.

    Returns the chassis_id, hostname, and port for each configured chassis.
    Use the chassis_id value when calling other tools (e.g. run_cli, get_facts) to target a specific chassis.
    """
    chassis = list_all_chassis()
    if not chassis:
        return "No chassis configured. Create config/chassis.yml (see chassis.yml.example)."
    lines = []
    for cid, info in chassis.items():
        lines.append(f"  {cid}: {info['host']}:{info['port']} (user: {info['username'] or '(none)'})")
    return "Available chassis:\n" + "\n".join(lines)


def register(mcp):
    mcp.tool()(list_chassis)
