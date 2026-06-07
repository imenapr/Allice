"""
ALLICE — AI File Edit Executor
Parses <allice_write> blocks from AI responses and applies them to disk.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from core.file_manager import ProjectFileManager


# Primary format: <allice_write path="README.md">content</allice_write>
_WRITE_PATTERN = re.compile(
    r'<allice_write\s+path=["\']([^"\']+)["\']\s*>(.*?)</allice_write>',
    re.DOTALL | re.IGNORECASE,
)

# Fallback: ```allice-write README.md\ncontent```
_FALLBACK_PATTERN = re.compile(
    r'```allice-write\s+([^\n]+)\n(.*?)```',
    re.DOTALL | re.IGNORECASE,
)


@dataclass
class EditResult:
    path: str
    success: bool
    error: str = ""


def parse_write_commands(text: str) -> list[tuple[str, str]]:
    """Extract (path, content) pairs from an AI response."""
    edits: list[tuple[str, str]] = []
    seen: set[str] = set()

    for match in _WRITE_PATTERN.finditer(text):
        path = match.group(1).strip().replace("\\", "/")
        content = match.group(2)
        if path not in seen:
            edits.append((path, content))
            seen.add(path)

    for match in _FALLBACK_PATTERN.finditer(text):
        path = match.group(1).strip().replace("\\", "/")
        content = match.group(2)
        if path not in seen:
            edits.append((path, content))
            seen.add(path)

    return edits


def apply_edits(file_manager: ProjectFileManager, text: str) -> list[EditResult]:
    """Parse and apply all write commands in an AI response."""
    results: list[EditResult] = []
    for path, content in parse_write_commands(text):
        # Strip one leading/trailing newline from model output, preserve internal formatting
        if content.startswith("\n"):
            content = content[1:]
        if content.endswith("\n"):
            content = content[:-1]

        write_result = file_manager.write_file(path, content)
        results.append(EditResult(
            path=path,
            success=write_result.success,
            error=write_result.error,
        ))
    return results


def format_results_summary(results: list[EditResult]) -> str:
    """Human-readable summary of applied file edits."""
    if not results:
        return ""

    lines = ["**File changes applied:**"]
    for r in results:
        if r.success:
            lines.append(f"- ✅ `{r.path}` saved")
        else:
            lines.append(f"- ❌ `{r.path}` failed: {r.error}")
    return "\n".join(lines)
