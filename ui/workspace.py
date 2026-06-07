"""
ALLICE — Main Workspace
Central workspace: message feed, input bar, terminal panel.
"""

import sys
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTextEdit, QFrame, QScrollArea,
    QSizePolicy, QSplitter, QApplication,
)
from PySide6.QtCore import Qt, Signal, QTimer, QProcess, QThread, QObject
from PySide6.QtGui import QFont, QKeyEvent, QColor

from core.agent import AgentState
from core.file_manager import ProjectFileManager
from ui.components.message_block import MessageBlock, ThinkingIndicator
from ui.file_editor import FileEditorPanel


class StreamWorker(QObject):
    """Runs Ollama streaming in a background thread."""
    token = Signal(str)
    done = Signal(str)
    error = Signal(str)
    finished = Signal()

    def __init__(self, client, messages):
        super().__init__()
        self.client = client
        self.messages = messages

    def run(self):
        self.client.stream_chat(
            messages=self.messages,
            on_token=self.token.emit,
            on_done=self.done.emit,
            on_error=self.error.emit,
        )
        self.finished.emit()


class InputBar(QWidget):
    send_requested = Signal(str)
    toggle_terminal = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("input_container")
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 16, 24, 20)
        outer.setSpacing(4)

        # Inner container with border
        inner = QWidget()
        inner.setObjectName("input_inner")
        inner_layout = QHBoxLayout(inner)
        inner_layout.setContentsMargins(0, 0, 0, 0)
        inner_layout.setSpacing(0)

        # Attach button
        attach = QPushButton("📎")
        attach.setObjectName("attach_btn")
        attach.setFixedSize(36, 36)
        attach.setCursor(Qt.PointingHandCursor)
        attach.setToolTip("Attach file")
        inner_layout.addWidget(attach)

        # Text input
        self.input = QTextEdit()
        self.input.setObjectName("input_field")
        self.input.setPlaceholderText("Ask ALLICE anything, or describe what you want to build...")
        f = QFont()
        f.setPointSize(13)
        self.input.setFont(f)
        self.input.setFixedHeight(44)
        self.input.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        # Auto-grow up to ~5 lines
        self.input.document().contentsChanged.connect(self._auto_resize)
        self.input.installEventFilter(self)
        inner_layout.addWidget(self.input)

        # Terminal toggle
        term_btn = QPushButton("⌨")
        term_btn.setObjectName("terminal_btn_input")
        term_btn.setFixedSize(36, 36)
        term_btn.setCursor(Qt.PointingHandCursor)
        term_btn.setToolTip("Toggle terminal")
        term_btn.clicked.connect(self.toggle_terminal.emit)
        inner_layout.addWidget(term_btn)

        # Send button
        self.send_btn = QPushButton("Send")
        self.send_btn.setObjectName("send_btn")
        self.send_btn.setFixedHeight(32)
        self.send_btn.setMinimumWidth(64)
        self.send_btn.setCursor(Qt.PointingHandCursor)
        f2 = QFont()
        f2.setBold(True)
        f2.setPointSize(12)
        self.send_btn.setFont(f2)
        self.send_btn.clicked.connect(self._on_send)
        inner_layout.addWidget(self.send_btn)

        outer.addWidget(inner)

        hint = QLabel("↵ Send  ·  Shift+↵ New line  ·  / Commands")
        hint.setObjectName("input_hint")
        fh = QFont()
        fh.setPointSize(10)
        hint.setFont(fh)
        outer.addWidget(hint)

    def _auto_resize(self):
        doc_height = self.input.document().size().height()
        new_height = max(44, min(int(doc_height) + 16, 140))
        self.input.setFixedHeight(new_height)

    def eventFilter(self, obj, event):
        if obj == self.input and isinstance(event, QKeyEvent):
            if event.key() == Qt.Key_Return and not (event.modifiers() & Qt.ShiftModifier):
                self._on_send()
                return True
        return super().eventFilter(obj, event)

    def _on_send(self):
        text = self.input.toPlainText().strip()
        if text:
            self.input.clear()
            self.input.setFixedHeight(44)
            self.send_requested.emit(text)

    def set_enabled(self, enabled: bool):
        self.input.setEnabled(enabled)
        self.send_btn.setEnabled(enabled)
        self.send_btn.setText("Send" if enabled else "…")


class TerminalPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("terminal_panel")
        self._build()
        self._process = None

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QWidget()
        header.setObjectName("terminal_header")
        header.setFixedHeight(30)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(12, 0, 8, 0)

        label = QLabel("TERMINAL")
        label.setObjectName("terminal_label")
        f = QFont()
        f.setPointSize(10)
        f.setBold(True)
        label.setFont(f)
        h_layout.addWidget(label)
        h_layout.addStretch()

        clear_btn = QPushButton("Clear")
        clear_btn.setObjectName("toggle_panel_btn")
        clear_btn.setFixedHeight(20)
        clear_btn.clicked.connect(self._clear)
        h_layout.addWidget(clear_btn)
        layout.addWidget(header)

        # Output
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setObjectName("terminal_output")
        f2 = QFont()
        f2.setFamilies(["JetBrains Mono", "Fira Code", "Consolas"])
        f2.setPointSize(11)
        self.output.setFont(f2)
        layout.addWidget(self.output)

        # Input line
        self.cmd_input = QTextEdit()
        self.cmd_input.setObjectName("terminal_input")
        self.cmd_input.setFixedHeight(30)
        self.cmd_input.setPlaceholderText("$ Enter command...")
        self.cmd_input.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.cmd_input.setFont(f2)
        self.cmd_input.installEventFilter(self)
        layout.addWidget(self.cmd_input)

    def eventFilter(self, obj, event):
        if obj == self.cmd_input and isinstance(event, QKeyEvent):
            if event.key() == Qt.Key_Return and not (event.modifiers() & Qt.ShiftModifier):
                cmd = self.cmd_input.toPlainText().strip()
                if cmd:
                    self.cmd_input.clear()
                    self.run_command(cmd)
                return True
        return super().eventFilter(obj, event)

    def run_command(self, command: str):
        self.output.append(f"<span style='color:#484f58'>$ {command}</span>")

        self._process = QProcess(self)
        self._process.readyReadStandardOutput.connect(self._on_stdout)
        self._process.readyReadStandardError.connect(self._on_stderr)
        self._process.finished.connect(self._on_finish)

        if sys.platform == "win32":
            self._process.start("cmd.exe", ["/c", command])
        else:
            self._process.start("bash", ["-c", command])

    def _on_stdout(self):
        data = self._process.readAllStandardOutput().data().decode(errors="replace")
        self.output.append(f"<span style='color:#22c55e'>{data}</span>")

    def _on_stderr(self):
        data = self._process.readAllStandardError().data().decode(errors="replace")
        self.output.append(f"<span style='color:#ef4444'>{data}</span>")

    def _on_finish(self, exit_code, _):
        if exit_code != 0:
            self.output.append(f"<span style='color:#ef4444'>Exited with code {exit_code}</span>")
        self.output.append("")

    def _clear(self):
        self.output.clear()

    def append_text(self, text: str, color: str = "#22c55e"):
        self.output.append(f"<span style='color:{color}'>{text}</span>")


class Workspace(QWidget):
    """
    Main content area. Contains:
    - Header bar
    - Message feed (scrollable)
    - Thinking indicator
    - Terminal panel (collapsible)
    - Input bar
    """

    context_updated = Signal(int, int)  # (message_count, token_estimate)
    file_saved = Signal(str)

    def __init__(self, ollama_client, agent, file_manager: ProjectFileManager, parent=None):
        super().__init__(parent)
        self.setObjectName("workspace")
        self.ollama = ollama_client
        self.agent = agent
        self.file_manager = file_manager

        self._messages: list[dict] = []
        self._current_block: MessageBlock | None = None
        self._thread: QThread | None = None
        self._worker: StreamWorker | None = None
        self._terminal_visible = False
        self._editor_visible = False

        # System prompt
        self._messages.append({
            "role": "system",
            "content": (
                "You are ALLICE, a professional AI software engineering assistant. "
                "You help users write code, debug issues, understand repositories, "
                "and build software. Format code in markdown code blocks with language tags. "
                "Be concise, precise, and developer-friendly."
            )
        })

        self._build()
        self._connect_agent()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Header ──
        header = QWidget()
        header.setObjectName("workspace_header")
        header.setFixedHeight(44)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(24, 0, 16, 0)

        self.title = QLabel("New Conversation")
        self.title.setObjectName("workspace_title")
        ft = QFont()
        ft.setPointSize(13)
        ft.setBold(True)
        self.title.setFont(ft)
        h_layout.addWidget(self.title)
        h_layout.addStretch()

        self.token_count_label = QLabel("0 tokens")
        self.token_count_label.setObjectName("stat_label")
        ftk = QFont()
        ftk.setPointSize(10)
        self.token_count_label.setFont(ftk)
        h_layout.addWidget(self.token_count_label)
        layout.addWidget(header)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("background-color: #21262d; max-height: 1px;")
        layout.addWidget(sep)

        # ── Splitter: messages + terminal ──
        self.splitter = QSplitter(Qt.Vertical)
        self.splitter.setHandleWidth(1)
        self.splitter.setChildrenCollapsible(False)

        # Message scroll area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setObjectName("workspace")
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setFrameShape(QFrame.NoFrame)

        self.msg_container = QWidget()
        self.msg_container.setObjectName("workspace")
        self.msg_layout = QVBoxLayout(self.msg_container)
        self.msg_layout.setContentsMargins(0, 0, 0, 0)
        self.msg_layout.setSpacing(0)
        self.msg_layout.addStretch()

        # Welcome screen
        self._show_welcome()

        self.scroll.setWidget(self.msg_container)
        self.splitter.addWidget(self.scroll)

        # File editor panel (shown when a file is opened)
        self.file_editor = FileEditorPanel(self.file_manager)
        self.file_editor.setFixedHeight(300)
        self.file_editor.hide()
        self.file_editor.file_saved.connect(self.file_saved.emit)
        self.file_editor.file_closed.connect(self._hide_editor)
        self.splitter.addWidget(self.file_editor)

        # Terminal panel
        self.terminal = TerminalPanel()
        self.terminal.setFixedHeight(220)
        self.terminal.hide()
        self.splitter.addWidget(self.terminal)

        layout.addWidget(self.splitter, stretch=1)

        # ── Thinking indicator (fixed, above input) ──
        self.thinking = ThinkingIndicator()
        self.thinking.hide()
        layout.addWidget(self.thinking)

        # ── Input bar ──
        self.input_bar = InputBar()
        self.input_bar.send_requested.connect(self.send_message)
        self.input_bar.toggle_terminal.connect(self._toggle_terminal)
        layout.addWidget(self.input_bar)

    def _show_welcome(self):
        welcome = QWidget()
        welcome.setObjectName("workspace")
        w_layout = QVBoxLayout(welcome)
        w_layout.setContentsMargins(60, 80, 60, 40)
        w_layout.setAlignment(Qt.AlignCenter)

        title = QLabel("ALLICE")
        title.setObjectName("sidebar_logo")
        ft = QFont()
        ft.setPointSize(36)
        ft.setBold(True)
        title.setFont(ft)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #e6edf3; letter-spacing: 4px;")
        w_layout.addWidget(title)

        sub = QLabel("AI Software Engineering Assistant")
        sub.setObjectName("stat_label")
        fs = QFont()
        fs.setPointSize(14)
        sub.setFont(fs)
        sub.setAlignment(Qt.AlignCenter)
        w_layout.addWidget(sub)

        w_layout.addSpacing(40)

        hints = [
            ("💬", "Ask about your codebase", "Explain what this function does"),
            ("🔧", "Get code written", "Write a REST API endpoint in FastAPI"),
            ("🐛", "Debug problems", "Why is this returning None?"),
            ("📦", "Manage projects", "Set up a new Python project with Poetry"),
        ]

        hints_widget = QWidget()
        hints_widget.setObjectName("workspace")
        hints_layout = QHBoxLayout(hints_widget)
        hints_layout.setSpacing(12)

        for icon, label, example in hints:
            card = QPushButton(f"{icon}\n{label}\n\n{example}")
            card.setObjectName("nav_btn")
            card.setCursor(Qt.PointingHandCursor)
            fc = QFont()
            fc.setPointSize(11)
            card.setFont(fc)
            card.setFixedSize(180, 100)
            card.setStyleSheet("""
                QPushButton {
                    background-color: #161b22;
                    border: 1px solid #21262d;
                    border-radius: 8px;
                    color: #8b949e;
                    text-align: left;
                    padding: 12px;
                }
                QPushButton:hover {
                    border-color: #7c3aed;
                    color: #e6edf3;
                }
            """)
            card.clicked.connect(lambda checked, ex=example: self.send_message(ex))
            hints_layout.addWidget(card)

        w_layout.addWidget(hints_widget)
        self.msg_layout.insertWidget(0, welcome)
        self._welcome_widget = welcome

    def _connect_agent(self):
        self.agent.state_changed.connect(self.thinking.update_state)

    def _toggle_terminal(self):
        self._terminal_visible = not self._terminal_visible
        if self._terminal_visible:
            self.terminal.show()
        else:
            self.terminal.hide()

    def send_message(self, text: str):
        # Hide welcome on first message
        if hasattr(self, "_welcome_widget") and self._welcome_widget.isVisible():
            self._welcome_widget.hide()

        # Add user message
        self._add_message_block("user", text)
        self._messages.append({"role": "user", "content": text})

        # Update title from first message
        if self.title.text() == "New Conversation":
            short = text[:40] + ("…" if len(text) > 40 else "")
            self.title.setText(short)

        # Show thinking
        self.input_bar.set_enabled(False)
        self.thinking.show()
        self.agent.begin_response()

        # Create assistant block (empty, will fill by streaming)
        self._current_block = self._add_message_block("assistant", "")

        # Start streaming in background thread
        self._thread = QThread()
        messages = self._build_messages_with_context()
        self._worker = StreamWorker(self.ollama, messages)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.token.connect(self._on_token)
        self._worker.done.connect(self._on_done)
        self._worker.error.connect(self._on_error)
        self._worker.finished.connect(self._thread.quit)
        self._thread.start()

    def _add_message_block(self, role: str, text: str) -> MessageBlock:
        block = MessageBlock(role, text)
        # Insert before the stretch
        count = self.msg_layout.count()
        self.msg_layout.insertWidget(count - 1, block)
        QTimer.singleShot(50, self._scroll_to_bottom)
        return block

    def _on_token(self, token: str):
        if self._current_block:
            self._current_block.append_token(token)
        self.agent.on_token(token)
        QTimer.singleShot(10, self._scroll_to_bottom)

    def _on_done(self, full_reply: str):
        if self._current_block:
            self._current_block.finalize(full_reply)
        self._messages.append({"role": "assistant", "content": full_reply})
        self.agent.on_done(full_reply)

        self.thinking.stop()
        self.thinking.hide()
        self.input_bar.set_enabled(True)

        # Update context stats
        msg_count = len([m for m in self._messages if m["role"] != "system"])
        token_est = sum(len(m["content"].split()) * 1.3 for m in self._messages)
        self.context_updated.emit(msg_count, int(token_est))
        self.token_count_label.setText(f"~{int(token_est):,} tokens")

        self._scroll_to_bottom()

    def _on_error(self, message: str):
        self.agent.on_error(message)
        if self._current_block:
            self._current_block.finalize(f"⚠ {message}")
        self.thinking.stop()
        self.thinking.hide()
        self.input_bar.set_enabled(True)

    def _scroll_to_bottom(self):
        bar = self.scroll.verticalScrollBar()
        bar.setValue(bar.maximum())

    def _build_messages_with_context(self) -> list[dict]:
        """Build message list, injecting selected file contents into context."""
        messages = list(self._messages)
        file_context = self.file_manager.get_selected_context()
        if file_context:
            context_msg = {
                "role": "system",
                "content": (
                    "The user has selected the following project files for context. "
                    "Use this information when answering:\n\n" + file_context
                ),
            }
            # Insert after the main system prompt
            messages.insert(1, context_msg)
        return messages

    def open_file(self, relative_path: str):
        """Open a file in the editor panel."""
        self.agent.set_state(AgentState.READING)
        if self.file_editor.open_file(relative_path):
            self._editor_visible = True
            self.file_editor.show()
        self.agent.set_state(AgentState.IDLE)

    def _hide_editor(self):
        self._editor_visible = False
        self.file_editor.hide()

    def on_file_selection_changed(self, selected: list[str]):
        """Called when user checks/unchecks files in the context panel."""
        pass  # Selection is read at send time via file_manager

    def on_project_changed(self, project_path: str):
        """Called when user opens a different project folder."""
        if self._editor_visible:
            self._hide_editor()

    def new_conversation(self):
        """Reset workspace for a new chat."""
        # Clear message blocks
        while self.msg_layout.count() > 1:
            item = self.msg_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._messages = [{
            "role": "system",
            "content": (
                "You are ALLICE, a professional AI software engineering assistant. "
                "You help users write code, debug issues, understand repositories, "
                "and build software. Format code in markdown code blocks with language tags."
            )
        }]
        self._current_block = None
        self.title.setText("New Conversation")
        self.token_count_label.setText("0 tokens")
        self._show_welcome()
        self._welcome_widget.show()
