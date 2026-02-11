"""
Shared helpers for PTX MCP tools. SSH-only (no NETCONF/RPC).
"""
import logging
import os
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Tuple

import paramiko

logger = logging.getLogger("ptx-mcp-server")

# Box-drawing for visual tool-call logs (debug)
_BOX_WIDTH = 72
_B = "═" * _BOX_WIDTH
_S = "─" * _BOX_WIDTH


def _format_tool_log(title: str, **fields: Any) -> str:
    """Build a visually formatted tool-call log block for debugging."""
    max_val_len = _BOX_WIDTH - 6  # space for "│   key: "
    lines = [
        "",
        "┌" + _B + "┐",
        "│ " + title.ljust(_BOX_WIDTH - 1) + "│",
        "├" + _S + "┤",
    ]
    for key, value in fields.items():
        label = f"  {key}:"
        if value is None:
            val_str = "(none)"
        else:
            val_str = str(value).replace("\n", " | ")
        if len(val_str) > max_val_len:
            val_str = val_str[: max_val_len - 3] + "..."
        # One line per field so the box stays aligned
        lines.append("│ " + (label + " " + val_str).ljust(_BOX_WIDTH - 1) + "│")
    lines.append("└" + _B + "┘")
    return "\n".join(lines)


def _log_tool_call(title: str, **fields: Any) -> None:
    """Log a formatted tool-call block at INFO level."""
    logger.info("%s", _format_tool_log(title, **fields))

_MONTHS = {
    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
    "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12,
}

_ISO_PREFIX_RE = re.compile(r"^(?P<iso>\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2})")
_SYSLOG_PREFIX_RE = re.compile(r"^(?P<mon>[A-Z][a-z]{2})\s+(?P<day>\d{1,2})\s+(?P<hms>\d{2}:\d{2}:\d{2})\b")


def parse_iso_datetime(value: str) -> datetime:
    """Parse a user-provided ISO-8601 datetime."""
    v = value.strip()
    if v.endswith("Z"):
        v = v[:-1] + "+00:00"
    v = v.replace(" ", "T")
    return datetime.fromisoformat(v)


def parse_log_line_timestamp(line: str, default_year: int) -> datetime | None:
    """Parse timestamp from a log line (ISO or syslog prefix). Returns naive datetime or None."""
    m = _ISO_PREFIX_RE.match(line)
    if m:
        try:
            iso = m.group("iso").replace(" ", "T")
            return datetime.fromisoformat(iso)
        except Exception:
            return None
    m = _SYSLOG_PREFIX_RE.match(line)
    if not m:
        return None
    mon = _MONTHS.get(m.group("mon"))
    if not mon:
        return None
    try:
        day = int(m.group("day"))
        h, mi, s = (int(x) for x in m.group("hms").split(":"))
        return datetime(default_year, mon, day, h, mi, s)
    except Exception:
        return None


def filter_log_lines_by_window(lines: list[str], start: datetime, end: datetime) -> list[str]:
    default_year = start.year
    out = []
    for line in lines:
        ts = parse_log_line_timestamp(line, default_year=default_year)
        if ts is None:
            continue
        if start <= ts <= end:
            out.append(line)
    return out


def resolve_var_log_path(filename: str) -> Path:
    """Resolve filename to a path under /var/log (security: no traversal)."""
    if not filename or not filename.strip():
        raise ValueError("filename must be non-empty")
    raw = filename.strip()
    base = Path("/var/log").resolve()
    p = Path(raw)
    if not p.is_absolute():
        p = (base / p).resolve()
    else:
        p = p.resolve()
    if not p.is_relative_to(base):
        raise ValueError("filename must resolve under /var/log")
    if p.suffix.lower() == ".gz":
        raise ValueError("compressed .gz logs are not supported")
    if not p.exists():
        raise ValueError(f"file does not exist: {p}")
    if not p.is_file():
        raise ValueError(f"not a file: {p}")
    return p


def read_text_tail(path: Path, max_bytes: int = 8_000_000) -> str:
    """Read up to the last max_bytes of a text file."""
    size = path.stat().st_size
    start = max(0, size - max_bytes)
    with path.open("rb") as f:
        if start:
            f.seek(start)
            _ = f.readline()
        data = f.read()
    return data.decode("utf-8", errors="replace")


def apply_match_filter(lines: list[str], match: str | None) -> list[str]:
    if not match:
        return lines
    pat = match.strip()
    if not pat:
        return lines
    try:
        rx = re.compile(pat)
        return [ln for ln in lines if rx.search(ln)]
    except re.error:
        return [ln for ln in lines if pat in ln]


def _escape_single_quoted(s: str) -> str:
    """Escape a string for use inside single-quoted shell argument (end quote, backslash, quote, char, start quote)."""
    return s.replace("'", "'\"'\"'")


def run_cli_command_on_ptx(command: str, chassis: Dict[str, Any], timeout_sec: int = 90) -> Tuple[bool, str]:
    """Run a single CLI command on the PTX via SSH. Returns (success, output).

    Args:
        command: CLI command to execute.
        chassis: Connection dict with keys: host, username, password, port, ssh_key, cli_invoke.
        timeout_sec: SSH command timeout in seconds.
    """
    host = chassis["host"]
    port = chassis.get("port", 22)
    username = chassis.get("username", "")
    password = chassis.get("password", "")
    ssh_key = chassis.get("ssh_key")
    cli_invoke = chassis.get("cli_invoke") or ""
    if cli_invoke == "cli-quoted":
        wrapped = "cli '" + _escape_single_quoted(command) + "'"
    else:
        wrapped = "cli " + command
        cli_invoke = "cli"
    auth = "key" if ssh_key and os.path.exists(ssh_key) else "password"
    _log_tool_call(
        "CLI SSH REQUEST",
        command=command,
        wrapped=wrapped,
        cli_invoke=cli_invoke,
        host=host,
        port=port,
        user=username or "(empty)",
        auth=auth,
        timeout_sec=timeout_sec,
    )
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    start = time.monotonic()
    try:
        if ssh_key and os.path.exists(ssh_key):
            client.connect(host, port=port, username=username, key_filename=ssh_key, timeout=min(30, timeout_sec))
        else:
            client.connect(host, port=port, username=username, password=password, timeout=min(30, timeout_sec))
        stdin, stdout, stderr = client.exec_command(wrapped, timeout=timeout_sec)
        out = stdout.read().decode("utf-8", errors="replace")
        err = stderr.read().decode("utf-8", errors="replace")
        code = stdout.channel.recv_exit_status()
        duration_ms = int((time.monotonic() - start) * 1000)
        out_preview = (out + "\n" + err).strip()[:500] if (out.strip() or err.strip()) else "(no output)"
        _log_tool_call(
            "CLI SSH RESPONSE",
            exit_code=code,
            success=code == 0,
            duration_ms=duration_ms,
            stdout_len=len(out),
            stderr_len=len(err),
            output_preview=out_preview,
        )
        if err.strip():
            out = out + "\n" + err if out.strip() else err
        return (code == 0, out.strip() or "(no output)")
    except Exception as e:
        duration_ms = int((time.monotonic() - start) * 1000)
        _log_tool_call(
            "CLI SSH EXCEPTION",
            error=str(e),
            error_type=type(e).__name__,
            duration_ms=duration_ms,
        )
        logger.error("CLI SSH: %s", e)
        return (False, str(e))
    finally:
        client.close()


def run_cli_stdin_on_ptx(command: str, stdin_content: str, chassis: Dict[str, Any], timeout_sec: int = 120) -> Tuple[bool, str]:
    """Run a CLI command on the PTX and feed stdin (e.g. 'cli' with multi-line input). Returns (success, output).

    Args:
        command: Shell command to execute (e.g. 'cli').
        stdin_content: Content to feed on stdin.
        chassis: Connection dict with keys: host, username, password, port, ssh_key.
        timeout_sec: SSH command timeout in seconds.
    """
    host = chassis["host"]
    port = chassis.get("port", 22)
    username = chassis.get("username", "")
    password = chassis.get("password", "")
    ssh_key = chassis.get("ssh_key")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        if ssh_key and os.path.exists(ssh_key):
            client.connect(host, port=port, username=username, key_filename=ssh_key, timeout=min(30, timeout_sec))
        else:
            client.connect(host, port=port, username=username, password=password, timeout=min(30, timeout_sec))
        stdin, stdout, stderr = client.exec_command(command, timeout=timeout_sec)
        stdin.write(stdin_content)
        stdin.channel.shutdown_write()
        out = stdout.read().decode("utf-8", errors="replace")
        err = stderr.read().decode("utf-8", errors="replace")
        code = stdout.channel.recv_exit_status()
        if err.strip():
            out = out + "\n" + err if out.strip() else err
        return (code == 0, out.strip() or "(no output)")
    except Exception as e:
        logger.error("CLI SSH (stdin): %s", e)
        return (False, str(e))
    finally:
        client.close()
