"""
ALLICE — Message Block Components
Claude-style message rendering with code blocks and syntax highlighting.
"""

import re
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTextEdit, QPushButton, QFrame, QSizePolicy,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QFontMetrics, QColor, QTextCharFormat, QSyntaxHighlighter, QTextDocument

try:
    from pygments import highlight
    from pygments.lexers import get_lexer_by_name, TextLexer
    from pygments.formatters import HtmlFormatter
    HAS_PYGMENTS = True
except ImportError:
    HAS_PYGMENTS = False


MONO_FONT = "JetBrains Mono,Fira Code,Cascadia Code,Consolas,Courier New"


def make_label(text="", object_name="", font_size=13, bold=False, wrap=True) -> QLabel:
    lbl = QLabel(text)
    lbl.setObjectName(object_name)
    if wrap:
        lbl.setWordWrap(True)
    f = QFont("Segoe UI", font_size)
    if bold:
        f.setBold(True)
    lbl.setFont(f)
    lbl.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.LinksAccessibleByMouse)
    return lbl


class CodeBlockWidget(QWidget):
    """Syntax-highlighted code block with a copy button."""

    def __init__(self, code: str, language: str = "python", parent=None):
        super().__init__(parent)
        self.code = code.strip()
        self.language = language or "text"
        self.setObjectName("code_block_container")
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header bar
        header = QWidget()
        header.setObjectName("code_block_header")
        header.setFixedHeight(34)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(12, 0, 8, 0)

        lang_label = QLabel(self.language.lower())
        lang_label.setObjectName("code_lang_label")
        h_layout.addWidget(lang_label)
        h_layout.addStretch()

        self.copy_btn = QPushButton("Copy")
        self.copy_btn.setObjectName("copy_code_btn")
        self.copy_btn.setFixedHeight(24)
        self.copy_btn.clicked.connect(self._copy)
        h_layout.addWidget(self.copy_btn)
        layout.addWidget(header)

        # Code area
        code_display = QTextEdit()
        code_display.setReadOnly(True)
        code_display.setObjectName("code_block_container")
        f = QFont()
        f.setFamilies(MONO_FONT.split(","))
        f.setPointSize(12)
        code_display.setFont(f)
        code_display.setLineWrapMode(QTextEdit.NoWrap)

        if HAS_PYGMENTS:
            try:
                lexer = get_lexer_by_name(self.language, stripall=True)
            except Exception:
                from pygments.lexers import TextLexer
                lexer = TextLexer()
            formatter = HtmlFormatter(
                style="github-dark",
                noclasses=True,
                nowrap=False,
                cssclass="",
            )
            html = highlight(self.code, lexer, formatter)
            # wrap in dark background
            styled = f"""
            <div style="background:#161b22;padding:12px;font-family:{MONO_FONT};font-size:12px;">
            {html}
            </div>
            """
            code_display.setHtml(styled)
        else:
            code_display.setPlainText(self.code)
            code_display.setStyleSheet("background:#161b22;color:#e6edf3;padding:12px;")

        # Auto-size height based on lines
        line_count = self.code.count("\n") + 1
        line_height = QFontMetrics(f).height()
        display_height = min(max(line_count * line_height + 40, 60), 500)
        code_display.setFixedHeight(display_height)

        layout.addWidget(code_display)

    def _copy(self):
        from PySide6.QtWidgets import QApplication
        QApplication.clipboard().setText(self.code)
        self.copy_btn.setText("Copied!")
        QTimer.singleShot(1500, lambda: self.copy_btn.setText("Copy"))


class MessageBlock(QWidget):
    """
    A single message in the workspace.
    Renders text with embedded code blocks, Claude-style.
    Role: 'user' | 'assistant'
    """

    def __init__(self, role: str, text: str = "", parent=None):
        super().__init__(parent)
        self.role = role
        self.is_user = role == "user"
        self._content_layout = None
        self._streaming_label = None
        self._current_text = ""
        self._build(text)

    def _build(self, initial_text: str):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        row = QWidget()
        row.setObjectName("msg_container_user" if self.is_user else "msg_container_assistant")
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(32, 14, 32, 14)
        row_layout.setSpacing(0)

        bubble = QWidget()
        bubble.setObjectName("msg_bubble_user" if self.is_user else "msg_bubble_assistant")
        bubble.setMaximumWidth(820)
        bubble.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Minimum)

        wrapper_layout = QVBoxLayout(bubble)
        wrapper_layout.setContentsMargins(14, 10, 14, 12)
        wrapper_layout.setSpacing(8)

        # Role label row
        role_row = QHBoxLayout()
        role_row.setContentsMargins(0, 0, 0, 0)

        role_label = QLabel("You" if self.is_user else "ALLICE")
        role_label.setObjectName("msg_role_user" if self.is_user else "msg_role_assistant")
        f = QFont()
        f.setPointSize(10)
        f.setBold(True)
        role_label.setFont(f)
        if self.is_user:
            role_row.addStretch()
            role_row.addWidget(role_label)
        else:
            role_row.addWidget(role_label)
            role_row.addStretch()
        wrapper_layout.addLayout(role_row)

        # Content area - will hold text and code blocks
        self._content_layout = QVBoxLayout()
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(8)

        if initial_text:
            self._render_content(initial_text)

        wrapper_layout.addLayout(self._content_layout)
        if self.is_user:
            row_layout.addStretch(1)
            row_layout.addWidget(bubble, 0, Qt.AlignRight)
        else:
            row_layout.addWidget(bubble, 0, Qt.AlignLeft)
            row_layout.addStretch(1)

        outer.addWidget(row)

    def _render_content(self, text: str):
        """Parse text into text segments and code blocks."""
        # Clear existing content
        while self._content_layout.count():
            item = self._content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        segments = self._parse_segments(text)

        for seg_type, content, lang in segments:
            if seg_type == "text":
                content = content.strip()
                if not content:
                    continue
                lbl = QLabel(content)
                lbl.setObjectName("msg_text_user" if self.is_user else "msg_text")
                lbl.setWordWrap(True)
                lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
                lbl.setAlignment(Qt.AlignRight if self.is_user else Qt.AlignLeft)
                f = QFont()
                f.setPointSize(13)
                lbl.setFont(f)
                lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
                self._content_layout.addWidget(lbl)
            elif seg_type == "code":
                block = CodeBlockWidget(content, language=lang)
                self._content_layout.addWidget(block)

        self._content_layout.addStretch(1)

    def _parse_segments(self, text: str) -> list:
        """Split text into (type, content, lang) tuples."""
        segments = []
        pattern = re.compile(r"```(\w*)\n?(.*?)```", re.DOTALL)
        last_end = 0

        for match in pattern.finditer(text):
            # text before code block
            before = text[last_end:match.start()]
            if before:
                segments.append(("text", before, ""))

            lang = match.group(1).strip() or "text"
            code = match.group(2)
            segments.append(("code", code, lang))
            last_end = match.end()

        # remaining text
        remaining = text[last_end:]
        if remaining:
            segments.append(("text", remaining, ""))

        return segments

    def append_token(self, token: str):
        """For streaming: accumulate tokens and update display."""
        self._current_text += token
        self._render_content(self._current_text)

    def finalize(self, full_text: str):
        """Called when streaming is complete."""
        self._current_text = full_text
        self._render_content(full_text)


class ThinkingIndicator(QWidget):
    """Animated 'ALLICE is thinking' indicator."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._dots = 0
        self._build()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(400)

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 16, 32, 16)

        wrapper = QWidget()
        wrapper.setObjectName("agent_status_card")
        w_layout = QHBoxLayout(wrapper)
        w_layout.setContentsMargins(14, 10, 14, 10)

        self.dot_label = QLabel("●")
        self.dot_label.setObjectName("agent_status_label")
        self.dot_label.setFixedWidth(14)
        w_layout.addWidget(self.dot_label)

        self.status_label = QLabel("ALLICE")
        self.status_label.setObjectName("agent_status_label")
        f = QFont()
        f.setBold(True)
        f.setPointSize(10)
        self.status_label.setFont(f)
        w_layout.addWidget(self.status_label)

        self.action_label = QLabel("Thinking...")
        self.action_label.setObjectName("agent_status_text")
        f2 = QFont()
        f2.setPointSize(12)
        self.action_label.setFont(f2)
        w_layout.addWidget(self.action_label)
        w_layout.addStretch()

        layout.addWidget(wrapper)

        self.detail_label = QLabel("Starting...")
        self.detail_label.setObjectName("agent_status_detail")
        self.detail_label.setWordWrap(True)
        f3 = QFont()
        f3.setPointSize(11)
        self.detail_label.setFont(f3)
        layout.addWidget(self.detail_label)

    def update_state(self, state_name: str, label: str):
        self.action_label.setText(label)
        colors = {
            "thinking": "#f59e0b",
            "coding": "#7c3aed",
            "executing": "#22c55e",
            "reading": "#38bdf8",
            "error": "#ef4444",
        }
        color = colors.get(state_name, "#484f58")
        self.dot_label.setStyleSheet(f"color: {color};")
        details = {
            "thinking": "Sending the request to the local model.",
            "coding": "Preparing or applying file changes.",
            "executing": "Running a local project action.",
            "reading": "Loading selected project files.",
            "error": "Something failed; check the message below.",
            "idle": "Ready for your next request.",
        }
        self.set_detail(details.get(state_name, label))

    def set_detail(self, text: str):
        self.detail_label.setText(text)

    def _tick(self):
        self._dots = (self._dots + 1) % 4
        dots = "." * self._dots
        current = self.action_label.text().rstrip(".")
        self.action_label.setText(current + dots)

    def stop(self):
        self._timer.stop()
        self.hide()
