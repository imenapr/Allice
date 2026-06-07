"""
ALLICE — Project File Manager
Handles file discovery, reading, writing, and selection for the AI assistant.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
# Directories and patterns to skip when scanning a project
SKIP_DIRS = {
    ".git", ".hg", ".svn", "__pycache__", ".pytest_cache",
    "node_modules", ".venv", "venv", "env", ".mypy_cache",
    ".tox", "dist", "build", ".idea", ".vscode", "egg-info",
}
SKIP_EXTENSIONS = {".pyc", ".pyo", ".pyd", ".so", ".dll", ".exe", ".bin"}
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2 MB — skip very large files for context


@dataclass
class FileEntry:
    """A file or directory in the project tree."""
    path: str          # relative path from project root
    name: str
    is_dir: bool
    size: int = 0


@dataclass
class FileReadResult:
    """Result of reading a file."""
    success: bool
    content: str = ""
    encoding: str = "utf-8"
    error: str = ""
    path: str = ""


@dataclass
class FileWriteResult:
    """Result of writing a file."""
    success: bool
    error: str = ""
    path: str = ""


class ProjectFileManager:
    """
    Manages project file operations with path-safety checks.
    All paths are resolved relative to the project root.
    """

    def __init__(self, project_root: str | None = None):
        self._root = Path(project_root or os.getcwd()).resolve()
        self._selected: set[str] = set()

    @property
    def project_root(self) -> Path:
        return self._root

    @property
    def project_name(self) -> str:
        return self._root.name

    def set_project_root(self, path: str) -> tuple[bool, str]:
        """Change the project root directory."""
        try:
            resolved = Path(path).resolve()
            if not resolved.is_dir():
                return False, f"Not a directory: {path}"
            self._root = resolved
            self._selected.clear()
            return True, ""
        except Exception as e:
            return False, str(e)

    def _resolve_safe(self, relative_path: str) -> Path | None:
        """Resolve a relative path and ensure it stays within project root."""
        try:
            full = (self._root / relative_path).resolve()
            full.relative_to(self._root)
            return full
        except (ValueError, OSError):
            return None

    def scan_project(self) -> list[FileEntry]:
        """Recursively scan the project and return all file/directory entries."""
        entries: list[FileEntry] = []

        def _walk(directory: Path, prefix: str = "") -> None:
            try:
                items = sorted(directory.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
            except PermissionError:
                return

            for item in items:
                rel = f"{prefix}{item.name}" if not prefix else f"{prefix}/{item.name}"

                if item.is_dir():
                    if item.name in SKIP_DIRS:
                        continue
                    entries.append(FileEntry(path=rel, name=item.name, is_dir=True))
                    _walk(item, rel)
                else:
                    if item.suffix.lower() in SKIP_EXTENSIONS:
                        continue
                    try:
                        size = item.stat().st_size
                    except OSError:
                        size = 0
                    entries.append(FileEntry(path=rel, name=item.name, is_dir=False, size=size))

        _walk(self._root)
        return entries

    def build_tree(self) -> dict:
        """
        Build a nested tree structure from flat entries.
        Returns: {name: {"_entry": FileEntry, "children": {...}}}
        """
        tree: dict = {"_entry": FileEntry(path="", name=self._root.name, is_dir=True), "children": {}}

        for entry in self.scan_project():
            parts = entry.path.replace("\\", "/").split("/")
            node = tree
            for i, part in enumerate(parts):
                if part not in node["children"]:
                    is_last = i == len(parts) - 1
                    node["children"][part] = {
                        "_entry": entry if is_last else FileEntry(
                            path="/".join(parts[: i + 1]),
                            name=part,
                            is_dir=True,
                        ),
                        "children": {},
                    }
                node = node["children"][part]

        return tree

    def read_file(self, relative_path: str) -> FileReadResult:
        """Read a file and return its contents, preserving formatting."""
        full = self._resolve_safe(relative_path)
        if full is None:
            return FileReadResult(success=False, error="Invalid or unsafe path", path=relative_path)

        if not full.exists():
            return FileReadResult(success=False, error="File not found", path=relative_path)

        if not full.is_file():
            return FileReadResult(success=False, error="Path is not a file", path=relative_path)

        if full.stat().st_size > MAX_FILE_SIZE:
            return FileReadResult(
                success=False,
                error=f"File too large ({full.stat().st_size:,} bytes, max {MAX_FILE_SIZE:,})",
                path=relative_path,
            )

        # Try UTF-8 first, then fall back to latin-1 for binary-ish text
        for encoding in ("utf-8", "utf-8-sig", "latin-1"):
            try:
                content = full.read_text(encoding=encoding)
                return FileReadResult(
                    success=True,
                    content=content,
                    encoding=encoding,
                    path=relative_path,
                )
            except UnicodeDecodeError:
                continue
            except PermissionError:
                return FileReadResult(success=False, error="Permission denied", path=relative_path)
            except OSError as e:
                return FileReadResult(success=False, error=str(e), path=relative_path)

        return FileReadResult(success=False, error="Unable to decode file", path=relative_path)

    def write_file(self, relative_path: str, content: str) -> FileWriteResult:
        """Write content to a file, preserving the exact text provided."""
        full = self._resolve_safe(relative_path)
        if full is None:
            return FileWriteResult(success=False, error="Invalid or unsafe path", path=relative_path)

        try:
            full.parent.mkdir(parents=True, exist_ok=True)
            full.write_text(content, encoding="utf-8", newline="")
            return FileWriteResult(success=True, path=relative_path)
        except PermissionError:
            return FileWriteResult(success=False, error="Permission denied", path=relative_path)
        except OSError as e:
            return FileWriteResult(success=False, error=str(e), path=relative_path)

    # ── Selection management ──

    def select_file(self, relative_path: str) -> None:
        self._selected.add(relative_path.replace("\\", "/"))

    def deselect_file(self, relative_path: str) -> None:
        self._selected.discard(relative_path.replace("\\", "/"))

    def toggle_selection(self, relative_path: str) -> bool:
        """Toggle selection; returns new selected state."""
        norm = relative_path.replace("\\", "/")
        if norm in self._selected:
            self._selected.discard(norm)
            return False
        self._selected.add(norm)
        return True

    def clear_selection(self) -> None:
        self._selected.clear()

    def select_all_files(self) -> None:
        for entry in self.scan_project():
            if not entry.is_dir:
                self._selected.add(entry.path.replace("\\", "/"))

    @property
    def selected_files(self) -> list[str]:
        return sorted(self._selected)

    def get_selected_context(self) -> str:
        """Build a context string from all selected files for the AI."""
        if not self._selected:
            return ""

        parts = []
        for path in sorted(self._selected):
            result = self.read_file(path)
            if result.success:
                parts.append(f"--- FILE: {path} ---\n{result.content}\n--- END FILE ---")
            else:
                parts.append(f"--- FILE: {path} (ERROR: {result.error}) ---")

        return "\n\n".join(parts)

    def format_size(self, size: int) -> str:
        if size < 1024:
            return f"{size} B"
        if size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        return f"{size / (1024 * 1024):.1f} MB"
