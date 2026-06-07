"""
ALLICE — File Editor Panel
View and edit project files with save functionality.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTextEdit, QFrame, QMessageBox,
    QSizePolicy,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from core.file_manager import ProjectFileManager


MONO_FONT = ["JetBrains Mono", "Fira Code", "Cascadia Code", "Consolas", "Courier New"]


class FileEditorPanel(QWidget):
    """Editor for viewing and modifying project files."""

    file_saved = Signal(str)          # relative path
    file_closed = Signal()
    status_message = Signal(str)      # status bar / toast messages

    def __init__(self, file_manager: ProjectFileManager, parent=None):
        super().__init__(parent)
        self.fm = file_manager
        self._current_path: str | None = None
        self._original_content: str = ""
        self._is_dirty = False
        self._build()

    def _build(self):
        self.setObjectName("file_editor_panel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Header bar ──
        header = QWidget()
        header.setObjectName("workspace_header")
        header.setFixedHeight(40)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(16, 0, 12, 0)

        self.file_label = QLabel("No file open")
        self.file_label.setObjectName("workspace_title")
        f = QFont()
        f.setPointSize(12)
        f.setBold(True)
        self.file_label.setFont(f)
        h_layout.addWidget(self.file_label)

        self.dirty_label = QLabel("")
        self.dirty_label.setObjectName("stat_label")
        self.dirty_label.setStyleSheet("color: #f59e0b;")
        h_layout.addWidget(self.dirty_label)

        h_layout.addStretch()

        self.readonly_badge = QLabel("")
        self.readonly_badge.setObjectName("stat_label")
        h_layout.addWidget(self.readonly_badge)

        self.revert_btn = QPushButton("Revert")
        self.revert_btn.setObjectName("toggle_panel_btn")
        self.revert_btn.setFixedHeight(28)
        self.revert_btn.setCursor(Qt.PointingHandCursor)
        self.revert_btn.clicked.connect(self._revert)
        self.revert_btn.setEnabled(False)
        h_layout.addWidget(self.revert_btn)

        self.save_btn = QPushButton("Save")
        self.save_btn.setObjectName("send_btn")
        self.save_btn.setFixedHeight(28)
        self.save_btn.setMinimumWidth(64)
        self.save_btn.setCursor(Qt.PointingHandCursor)
        self.save_btn.clicked.connect(self._save)
        self.save_btn.setEnabled(False)
        h_layout.addWidget(self.save_btn)

        self.close_btn = QPushButton("✕")
        self.close_btn.setObjectName("toggle_panel_btn")
        self.close_btn.setFixedSize(28, 28)
        self.close_btn.setCursor(Qt.PointingHandCursor)
        self.close_btn.clicked.connect(self._close_editor)
        h_layout.addWidget(self.close_btn)

        layout.addWidget(header)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("background-color: #21262d; max-height: 1px;")
        layout.addWidget(sep)

        # ── Editor area ──
        self.editor = QTextEdit()
        self.editor.setObjectName("terminal_output")
        self.editor.setPlaceholderText("Select a file from the Project Files panel to view or edit...")
        ef = QFont()
        ef.setFamilies(MONO_FONT)
        ef.setPointSize(12)
        self.editor.setFont(ef)
        self.editor.setLineWrapMode(QTextEdit.NoWrap)
        self.editor.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.editor.textChanged.connect(self._on_text_changed)
        layout.addWidget(self.editor)

        # ── Status bar ──
        status_bar = QWidget()
        status_bar.setFixedHeight(24)
        sb_layout = QHBoxLayout(status_bar)
        sb_layout.setContentsMargins(16, 0, 16, 0)

        self.status_label = QLabel("Ready")
        self.status_label.setObjectName("stat_label")
        sf = QFont()
        sf.setPointSize(10)
        self.status_label.setFont(sf)
        sb_layout.addWidget(self.status_label)
        sb_layout.addStretch()

        self.encoding_label = QLabel("")
        self.encoding_label.setObjectName("stat_label")
        self.encoding_label.setFont(sf)
        sb_layout.addWidget(self.encoding_label)

        layout.addWidget(status_bar)

    def open_file(self, relative_path: str) -> bool:
        """Load a file into the editor. Returns True on success."""
        if self._is_dirty:
            if not self._confirm_discard():
                return False

        result = self.fm.read_file(relative_path)
        if not result.success:
            self._show_error("Cannot Read File", result.error)
            self.status_message.emit(f"Read error: {result.error}")
            return False

        self._current_path = relative_path
        self._original_content = result.content
        self._is_dirty = False

        self.editor.blockSignals(True)
        self.editor.setPlainText(result.content)
        self.editor.blockSignals(False)

        self.file_label.setText(relative_path)
        self.dirty_label.setText("")
        self.encoding_label.setText(f"{result.encoding}  ·  {len(result.content):,} chars")
        self.readonly_badge.setText("")
        self.save_btn.setEnabled(True)
        self.revert_btn.setEnabled(True)
        self.status_label.setText(f"Opened {relative_path}")
        self.status_message.emit(f"Opened {relative_path}")

        return True

    def _on_text_changed(self):
        if self._current_path is None:
            return
        current = self.editor.toPlainText()
        self._is_dirty = current != self._original_content
        self.dirty_label.setText("● Modified" if self._is_dirty else "")
        self.save_btn.setEnabled(self._is_dirty)

    def _save(self):
        if not self._current_path:
            return

        content = self.editor.toPlainText()
        result = self.fm.write_file(self._current_path, content)

        if not result.success:
            self._show_error("Cannot Save File", result.error)
            self.status_message.emit(f"Save error: {result.error}")
            return

        self._original_content = content
        self._is_dirty = False
        self.dirty_label.setText("")
        self.save_btn.setEnabled(False)
        self.status_label.setText(f"Saved {self._current_path}")
        self.status_message.emit(f"Saved {self._current_path}")
        self.file_saved.emit(self._current_path)

    def _revert(self):
        if not self._current_path or not self._is_dirty:
            return
        if not self._confirm_discard("Revert all unsaved changes?"):
            return

        self.editor.blockSignals(True)
        self.editor.setPlainText(self._original_content)
        self.editor.blockSignals(False)
        self._is_dirty = False
        self.dirty_label.setText("")
        self.save_btn.setEnabled(False)
        self.status_label.setText("Reverted to last saved version")

    def _close_editor(self):
        if self._is_dirty and not self._confirm_discard():
            return
        self._clear()
        self.file_closed.emit()

    def _clear(self):
        self._current_path = None
        self._original_content = ""
        self._is_dirty = False
        self.editor.clear()
        self.file_label.setText("No file open")
        self.dirty_label.setText("")
        self.encoding_label.setText("")
        self.readonly_badge.setText("")
        self.save_btn.setEnabled(False)
        self.revert_btn.setEnabled(False)
        self.status_label.setText("Ready")

    def _confirm_discard(self, message: str = "You have unsaved changes. Discard them?") -> bool:
        reply = QMessageBox.question(
            self,
            "Unsaved Changes",
            message,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        return reply == QMessageBox.Yes

    def _show_error(self, title: str, message: str):
        QMessageBox.warning(self, title, message)

    @property
    def current_file(self) -> str | None:
        return self._current_path

    @property
    def is_dirty(self) -> bool:
        return self._is_dirty
