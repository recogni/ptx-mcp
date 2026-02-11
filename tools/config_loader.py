"""Load tools.yml: enable/disable tools and allowed CLI command patterns."""
import re
from pathlib import Path
from typing import List

logger = __import__("logging").getLogger("ptx-mcp-server")

# Default path: config/tools.yml relative to project root (parent of tools/)
_TOOLS_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _TOOLS_DIR.parent
_DEFAULT_CONFIG_PATH = _PROJECT_ROOT / "config" / "tools.yml"


def _find_config() -> Path:
    if _DEFAULT_CONFIG_PATH.is_file():
        return _DEFAULT_CONFIG_PATH
    raise FileNotFoundError(
        f"Tools config not found. Create config/tools.yml at {_DEFAULT_CONFIG_PATH}"
    )


def load_config() -> dict:
    """Load config/tools.yml. Returns dict with allowed_tools and allowed_ssh_commands."""
    import yaml

    path = _find_config()
    with path.open() as f:
        data = yaml.safe_load(f) or {}
    at = data.get("allowed_tools")
    if at is None:
        at = []
    if isinstance(at, dict):
        at = [k for k, v in at.items() if v]
    return {
        "allowed_tools": list(at) if at else [],
        "allowed_ssh_commands": data.get("allowed_ssh_commands") or [],
    }


def is_tool_enabled(tool_name: str, config: dict | None = None) -> bool:
    """Return True if tool_name is in the allowed_tools list."""
    if config is None:
        config = load_config()
    return tool_name in (config.get("allowed_tools") or [])


def get_allowed_command_patterns(config: dict | None = None) -> List[re.Pattern]:
    """Return compiled regex patterns for allowed SSH commands."""
    if config is None:
        config = load_config()
    patterns = []
    for pat in config.get("allowed_ssh_commands") or []:
        try:
            patterns.append(re.compile(pat))
        except re.error as e:
            logger.warning("Invalid allowed_ssh_commands regex %r: %s", pat, e)
    return patterns


def is_command_allowed(command: str, config: dict | None = None) -> bool:
    """Return True if command is allowed by at least one allowed_ssh_commands pattern. Patterns match from start of command."""
    if not (command or command.strip()):
        return False
    cmd = command.strip()
    for pattern in get_allowed_command_patterns(config):
        if pattern.match(cmd):
            return True
    return False
