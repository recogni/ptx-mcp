"""
PTX MCP tools: SSH-only. Enable/disable in config/tools.yml.
"""
from tools.config_loader import load_config

_registry = {
    "run_cli": ("tools.run_cli", "register"),
    "get_facts": ("tools.get_facts", "register"),
    "get_configuration": ("tools.get_configuration", "register"),
    "edit_configuration": ("tools.edit_configuration", "register"),
    "rollback_configuration": ("tools.rollback_configuration", "register"),
    "add_software": ("tools.add_software", "register"),
    "read_var_log_messages_window": ("tools.read_var_log_messages_window", "register"),
    "list_chassis": ("tools.list_chassis", "register"),
}


def register_all_tools(mcp):
    """Register only tools that are enabled in config/tools.yml."""
    config = load_config()
    for name, (module_path, attr) in _registry.items():
        if name not in (config.get("allowed_tools") or []):
            continue
        mod = __import__(module_path, fromlist=[attr])
        getattr(mod, attr)(mcp)
