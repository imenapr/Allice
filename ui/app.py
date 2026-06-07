"""
ALLICE — Main Application Window
Assembles sidebar + workspace + context panel.
"""

import threading
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout,
    QSplitter, QApplication,
)
from PySide6.QtCore import Qt, QTimer, QThread, QObject, Signal
from PySide6.QtGui import QFont

from core.ollama_client import OllamaClient, AVAILABLE_MODELS
from core.agent import Agent
from ui.sidebar import Sidebar
from ui.workspace import Workspace
from ui.context_panel import ContextPanel


class OllamaPoller(QObject):
    """Polls Ollama availability and model list in background."""
    status_changed = Signal(bool)
    models_updated = Signal(list)

    def __init__(self, client: OllamaClient):
        super().__init__()
        self.client = client
        self._running = True

    def run(self):
        while self._running:
            available = self.client.is_available()
            self.status_changed.emit(available)
            if available:
                models = self.client.list_models()
                if models:
                    self.models_updated.emit(models)
            import time
            time.sleep(5)

    def stop(self):
        self._running = False


class AlliceWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ALLICE — AI Software Engineering Assistant")
        self.resize(1280, 800)
        self.setMinimumSize(900, 600)

        # Core
        self.ollama = OllamaClient()
        self.agent = Agent()

        self._conversations: dict[str, list] = {}
        self._conv_counter = 0

        self._build_ui()
        self._connect_signals()
        self._start_ollama_poll()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Sidebar (fixed width) ──
        self.sidebar = Sidebar(models=AVAILABLE_MODELS)
        layout.addWidget(self.sidebar)

        # ── Workspace (fills remaining space) ──
        self.workspace = Workspace(self.ollama, self.agent)
        layout.addWidget(self.workspace, stretch=1)

        # ── Right Context Panel (fixed width, collapsible) ──
        self.context_panel = ContextPanel()
        layout.addWidget(self.context_panel)

    def _connect_signals(self):
        # Sidebar signals
        self.sidebar.new_chat_requested.connect(self._new_chat)
        self.sidebar.model_changed.connect(self._on_model_changed)
        self.sidebar.conversation_selected.connect(self._on_conv_selected)

        # Agent state → context panel
        self.agent.state_changed.connect(self.context_panel.update_agent_state)

        # Context stats
        self.workspace.context_updated.connect(self.context_panel.update_context)

        # Right panel close
        self.context_panel.panel_close_requested.connect(self._toggle_context_panel)

    def _new_chat(self):
        self._conv_counter += 1
        self.workspace.new_conversation()
        conv_id = f"conv_{self._conv_counter}"
        self.sidebar.add_conversation(
            f"New Chat #{self._conv_counter}",
            conv_id,
            select=True
        )

    def _on_model_changed(self, model: str):
        self.ollama.set_model(model)
        self.context_panel.update_model(model)

    def _on_conv_selected(self, conv_id: str):
        # Future: restore conversation history
        pass

    def _toggle_context_panel(self):
        self.context_panel.setVisible(not self.context_panel.isVisible())

    def _start_ollama_poll(self):
        self._poll_thread = QThread()
        self._poller = OllamaPoller(self.ollama)
        self._poller.moveToThread(self._poll_thread)
        self._poll_thread.started.connect(self._poller.run)
        self._poller.status_changed.connect(self.sidebar.set_ollama_status)
        self._poller.models_updated.connect(self.sidebar.update_models)
        self._poll_thread.start()

    def closeEvent(self, event):
        if hasattr(self, "_poller"):
            self._poller.stop()
        if hasattr(self, "_poll_thread"):
            self._poll_thread.quit()
            self._poll_thread.wait(1000)
        event.accept()
