"""Load and manage multi-chassis configuration from config/chassis.yml."""
from pathlib import Path
from typing import Any

import yaml

logger = __import__("logging").getLogger("ptx-mcp-server")

_TOOLS_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _TOOLS_DIR.parent
_DEFAULT_CHASSIS_PATH = _PROJECT_ROOT / "config" / "chassis.yml"


def _load_chassis_file() -> dict[str, dict[str, Any]]:
    """Load chassis definitions from config/chassis.yml. Returns {id: {host, ...}}."""
    p = _DEFAULT_CHASSIS_PATH
    if not p.is_file():
        return {}
    with p.open() as f:
        data = yaml.safe_load(f) or {}
    raw = data.get("chassis")
    if not isinstance(raw, dict) or not raw:
        return {}
    result: dict[str, dict[str, Any]] = {}
    for cid, info in raw.items():
        if not isinstance(info, dict) or not info.get("host"):
            logger.warning("Skipping chassis %r: missing 'host'", cid)
            continue
        result[str(cid)] = {
            "host": str(info["host"]),
            "username": str(info.get("username", "")),
            "password": str(info.get("password", "")),
            "port": int(info.get("port", 22)),
            "ssh_key": str(info["ssh_key"]) if info.get("ssh_key") else None,
            "cli_invoke": str(info["cli_invoke"]).strip().lower() if info.get("cli_invoke") else None,
        }
    return result


def load_chassis_config() -> dict[str, dict[str, Any]]:
    """Load all chassis from config/chassis.yml."""
    return _load_chassis_file()


def get_chassis(chassis_id: str | None = None) -> dict[str, Any]:
    """Resolve a chassis by ID. If chassis_id is None and only one exists, use it.

    Returns dict with keys: host, username, password, port, ssh_key, cli_invoke.
    Raises ValueError if chassis not found or ambiguous.
    """
    all_chassis = load_chassis_config()
    if not all_chassis:
        raise ValueError(
            "No chassis configured. Create config/chassis.yml (see chassis.yml.example)."
        )
    if chassis_id is not None:
        chassis = all_chassis.get(chassis_id)
        if chassis is None:
            available = ", ".join(sorted(all_chassis.keys()))
            raise ValueError(
                f"Unknown chassis_id '{chassis_id}'. Available: {available}"
            )
        return chassis
    # chassis_id is None — auto-select if only one
    if len(all_chassis) == 1:
        return next(iter(all_chassis.values()))
    available = ", ".join(sorted(all_chassis.keys()))
    raise ValueError(
        f"Multiple chassis configured ({available}). "
        f"Please specify chassis_id."
    )


def list_all_chassis() -> dict[str, dict[str, Any]]:
    """Return all chassis with safe info (no passwords/keys)."""
    all_chassis = load_chassis_config()
    safe: dict[str, dict[str, Any]] = {}
    for cid, info in all_chassis.items():
        safe[cid] = {
            "host": info["host"],
            "port": info["port"],
            "username": info["username"],
        }
    return safe
