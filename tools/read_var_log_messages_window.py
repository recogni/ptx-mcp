"""MCP tool: read local /var/log file lines within a time window."""
import time
from datetime import datetime, timedelta
from pathlib import Path

from lxml import etree

from tools.common import (
    apply_match_filter,
    filter_log_lines_by_window,
    parse_iso_datetime,
    read_text_tail,
    resolve_var_log_path,
)

logger = __import__("logging").getLogger("ptx-mcp-server")


async def read_var_log_messages_window(
    start: str | None = None,
    end: str | None = None,
    last_seconds: int | None = None,
    filename: str = "syslog",
    max_lines: int = 5000,
    page: int = 0,
    page_size: int = 200,
    match: str | None = None,
) -> str:
    """
    Read a local log file under /var/log and return lines within an inclusive time window.

    This is useful for reading container/host-mounted logs (inside the MCP server container).
    Output is returned as a <file-content ...> XML element to match Junos get-log output shape.

    Args:
        start: ISO-8601 datetime string (e.g. 2026-02-05T01:09:00Z)
        end: ISO-8601 datetime string (e.g. 2026-02-05T01:10:00Z). If omitted, defaults to "now".
        last_seconds: Convenience option. If provided, ignores start/end and returns the last N seconds.
        filename: Log filename under /var/log (default: "syslog"). Absolute paths must stay under /var/log.
        max_lines: Max number of filtered lines to consider (client-side). Pagination operates within this cap.
        page: Page index (0 = most recent page, 1 = previous page, ...).
        page_size: Number of lines per page.
        match: Optional regex (or substring) filter applied before time filtering to reduce content.
    """
    try:
        if page < 0:
            return "Error: page must be >= 0"
        if page_size <= 0:
            return "Error: page_size must be > 0"

        if last_seconds is not None:
            if last_seconds <= 0:
                return "Error: last_seconds must be > 0"
            end_dt = datetime.now()
            start_dt = end_dt - timedelta(seconds=int(last_seconds))
        else:
            if start is None:
                return "Error: provide either (start, end) or last_seconds"
            start_dt = parse_iso_datetime(start)
            end_dt = parse_iso_datetime(end) if end is not None else datetime.now()

        start_dt = start_dt.replace(tzinfo=None)
        end_dt = end_dt.replace(tzinfo=None)
        if end_dt < start_dt:
            return "Error: end must be >= start"

        path = resolve_var_log_path(filename)
        log_text = read_text_tail(path)
        lines = [ln for ln in log_text.splitlines() if ln.strip()]

        lines = apply_match_filter(lines, match=match)
        filtered = filter_log_lines_by_window(lines, start=start_dt, end=end_dt)
        if max_lines and max_lines > 0 and len(filtered) > max_lines:
            filtered = filtered[-max_lines:]

        if filtered:
            end_idx = len(filtered) - (page * page_size)
            start_idx = max(0, end_idx - page_size)
            if end_idx <= 0 or start_idx >= end_idx:
                filtered_page = []
            else:
                filtered_page = filtered[start_idx:end_idx]
        else:
            filtered_page = []

        filtered_text = "\n".join(filtered_page)
        if log_text.endswith("\n") and filtered_text:
            filtered_text += "\n"

        attrib = {
            "filename": str(path.relative_to(Path("/var/log"))),
            "seconds": str(int(time.time())),
            "filesize": str(path.stat().st_size),
            "encoding": "text",
        }
        out_elem = etree.Element("file-content", **attrib)
        out_elem.text = filtered_text
        return etree.tostring(out_elem, encoding="unicode", pretty_print=True)
    except Exception as e:
        logger.error("Error reading /var/log window: %s", e)
        return f"Error: {str(e)}"


def register(mcp):
    """Register this tool with the FastMCP server."""
    mcp.tool()(read_var_log_messages_window)
