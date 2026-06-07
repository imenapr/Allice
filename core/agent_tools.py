"""
ALLICE agent tools.

The local model can request these actions with simple XML-like blocks. The
desktop app executes them inside the active project and feeds the result back
to the model.
"""

from __future__ import annotations

import html
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from core.edit_executor import apply_edits, EditResult
from core.file_manager import ProjectFileManager


MAX_TOOL_OUTPUT = 16_000
COMMAND_TIMEOUT_SECONDS = 180

_READ_PATTERN = re.compile(
    r'<allice_read\s+path=["\']([^"\']+)["\']\s*/?>',
    re.IGNORECASE,
)
_LIST_PATTERN = re.compile(
    r'<allice_list(?:\s+path=["\']([^"\']*)["\'])?\s*/?>',
    re.IGNORECASE,
)
_RUN_PATTERN = re.compile(
    r'<allice_run\s+command=["\']([^"\']+)["\']\s*/?>',
    re.IGNORECASE,
)
_WRITE_DISPLAY_PATTERN = re.compile(
    r'<allice_write\s+path=["\']([^"\']+)["\']\s*>(.*?)</allice_write>',
    re.DOTALL | re.IGNORECASE,
)


@dataclass
class ToolRunResult:
    requested: bool
    feedback: str = ""
    display: str = ""
    edits: list[EditResult] | None = None
    changed_paths: list[str] | None = None


def has_tool_requests(text: str) -> bool:
    return bool(
        _READ_PATTERN.search(text)
        or _LIST_PATTERN.search(text)
        or _RUN_PATTERN.search(text)
    )


def clean_tool_blocks_for_display(text: str) -> str:
    """Keep tool directives out of the visible chat transcript."""
    cleaned = _WRITE_DISPLAY_PATTERN.sub(
        lambda match: f"[file write requested: {match.group(1).strip()}]",
        text,
    )
    cleaned = _READ_PATTERN.sub(
        lambda match: f"[file read requested: {match.group(1).strip()}]",
        cleaned,
    )
    cleaned = _LIST_PATTERN.sub(
        lambda match: f"[folder list requested: {(match.group(1) or '.').strip() or '.'}]",
        cleaned,
    )
    cleaned = _RUN_PATTERN.sub(
        lambda match: f"[command requested: {html.unescape(match.group(1).strip())}]",
        cleaned,
    )
    return cleaned.strip()


def run_requested_tools(file_manager: ProjectFileManager, text: str) -> ToolRunResult:
    """
    Execute all tool requests found in an assistant reply.

    File writes are applied first so a following test command sees the updated
    files. Read/list/run outputs are returned as a hidden follow-up message.
    """
    sections: list[str] = []
    display_lines: list[str] = []
    changed_paths: list[str] = []

    edits = apply_edits(file_manager, text)
    for edit in edits:
        if edit.success:
            changed_paths.append(edit.path)
            sections.append(f"WRITE {edit.path}: saved")
            display_lines.append(f"Saved `{edit.path}`")
        else:
            sections.append(f"WRITE {edit.path}: failed - {edit.error}")
            display_lines.append(f"Could not save `{edit.path}`: {edit.error}")

    for path in _READ_PATTERN.findall(text):
        result = file_manager.read_file(path.strip())
        if result.success:
            sections.append(
                f"READ {result.path}:\n```text\n{_trim(result.content)}\n```"
            )
            display_lines.append(f"Read `{result.path}`")
        else:
            sections.append(f"READ {path}: failed - {result.error}")
            display_lines.append(f"Could not read `{path}`: {result.error}")

    for raw_path in _LIST_PATTERN.findall(text):
        path = (raw_path or ".").strip() or "."
        listing = _list_path(file_manager, path)
        sections.append(f"LIST {path}:\n{listing}")
        display_lines.append(f"Listed `{path}`")

    for command in _RUN_PATTERN.findall(text):
        command = html.unescape(command.strip())
        command_result = _run_command(file_manager.project_root, command)
        sections.append(command_result)
        first_line = command_result.splitlines()[0] if command_result else command
        display_lines.append(first_line)

    requested = bool(sections)
    if not requested:
        return ToolRunResult(requested=False, edits=edits, changed_paths=changed_paths)

    feedback = (
        "ALLICE LOCAL TOOL RESULTS\n"
        "Use these real project results to continue. If the task is complete, "
        "answer the user briefly. If more actions are needed, request another "
        "tool block.\n\n"
        + "\n\n".join(sections)
    )
    display = "Local actions:\n" + "\n".join(f"- {line}" for line in display_lines)
    return ToolRunResult(
        requested=True,
        feedback=feedback,
        display=display,
        edits=edits,
        changed_paths=changed_paths,
    )


def _list_path(file_manager: ProjectFileManager, relative_path: str) -> str:
    full = _resolve_safe(file_manager.project_root, relative_path)
    if full is None:
        return "failed - invalid or unsafe path"
    if not full.exists():
        return "failed - path not found"
    if full.is_file():
        return f"{relative_path} ({full.stat().st_size} bytes)"

    lines: list[str] = []
    try:
        for item in sorted(full.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
            suffix = "/" if item.is_dir() else ""
            try:
                rel = item.resolve().relative_to(file_manager.project_root).as_posix()
            except ValueError:
                continue
            lines.append(f"- {rel}{suffix}")
    except OSError as exc:
        return f"failed - {exc}"

    return "\n".join(lines[:250]) if lines else "(empty)"


def _run_command(project_root: Path, command: str) -> str:
    try:
        completed = subprocess.run(
            command,
            cwd=str(project_root),
            shell=True,
            capture_output=True,
            text=True,
            timeout=COMMAND_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        output = "\n".join(part for part in [exc.stdout or "", exc.stderr or ""] if part)
        return (
            f"RUN {command}: timed out after {COMMAND_TIMEOUT_SECONDS}s\n"
            f"OUTPUT:\n{_trim(output)}"
        )
    except OSError as exc:
        return f"RUN {command}: failed to start - {exc}"

    output = "\n".join(
        part for part in [completed.stdout, completed.stderr] if part
    ).strip()
    return (
        f"RUN {command}: exit code {completed.returncode}\n"
        f"OUTPUT:\n{_trim(output) if output else '(no output)'}"
    )


def _resolve_safe(root: Path, relative_path: str) -> Path | None:
    try:
        full = (root / relative_path).resolve()
        full.relative_to(root)
        return full
    except (ValueError, OSError):
        return None


def _trim(text: str) -> str:
    if len(text) <= MAX_TOOL_OUTPUT:
        return text
    return text[:MAX_TOOL_OUTPUT] + "\n...[output trimmed]"
