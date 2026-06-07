"""
ALLICE — Left Sidebar
Navigation, model selection, and conversation history.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QScrollArea, QFrame,
    QSizePolicy, QSpacerItem,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont


NAV_ITEMS = [
    ("💬", "Chat", "chat"),
    ("📁", "Projects", "projects"),
    ("🔍", "Search", "search"),
    ("⚙️", "Settings", "settings"),
]


class NavButton(QPushButton):
    def __init__(self, icon: str, label: str, page_id: str):
        super().__init__(f"  {icon}  {label}")
        self.page_id = page_id
        self.setObjectName("nav_btn")
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        f = QFont()
        f.setPointSize(12)
        self.setFont(f)
        self.setFixedHeight(36)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)


class ConversationItem(QPushButton):
    def __init__(self, title: str, conv_id: str):
        super().__init__(title)
        self.conv_id = conv_id
        self.setObjectName("conv_item")
        self.setCursor(Qt.PointingHandCursor)
        f = QFont()
        f.setPointSize(11)
        self.setFont(f)
        self.setFixedHeight(30)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setToolTip(title)


class Sidebar(QWidget):
    new_chat_requested = Signal()
    nav_changed = Signal(str)
    model_changed = Signal(str)
    conversation_selected = Signal(str)

    def __init__(self, models: list[str], parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.models = models
        self._conversations = []
        self._nav_buttons = []
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 16, 12, 16)
        layout.setSpacing(0)

        # ── Logo ──
        logo_row = QHBoxLayout()
        logo_row.setContentsMargins(4, 0, 0, 0)

        logo = QLabel("ALLICE")
        logo.setObjectName("sidebar_logo")
        f = QFont()
        f.setPointSize(14)
        f.setBold(True)
        f.setLetterSpacing(QFont.AbsoluteSpacing, 2)
        logo.setFont(f)
        logo_row.addWidget(logo)

        badge = QLabel("AI")
        badge.setObjectName("sidebar_logo_badge")
        f2 = QFont()
        f2.setPointSize(9)
        f2.setBold(True)
        badge.setFont(f2)
        logo_row.addWidget(badge, alignment=Qt.AlignBottom)
        logo_row.addStretch()
        layout.addLayout(logo_row)

        layout.addSpacing(20)

        # ── New Chat ──
        new_chat = QPushButton("＋  New Chat")
        new_chat.setObjectName("new_chat_btn")
        new_chat.setCursor(Qt.PointingHandCursor)
        f3 = QFont()
        f3.setPointSize(12)
        f3.setBold(True)
        new_chat.setFont(f3)
        new_chat.setFixedHeight(38)
        new_chat.clicked.connect(self.new_chat_requested.emit)
        layout.addWidget(new_chat)

        layout.addSpacing(20)

        # ── Navigation ──
        nav_label = QLabel("WORKSPACE")
        nav_label.setObjectName("sidebar_section_label")
        f4 = QFont()
        f4.setPointSize(9)
        f4.setBold(True)
        nav_label.setFont(f4)
        layout.addWidget(nav_label)
        layout.addSpacing(4)

        for icon, label, page_id in NAV_ITEMS:
            btn = NavButton(icon, label, page_id)
            btn.clicked.connect(lambda checked, pid=page_id: self._on_nav(pid))
            self._nav_buttons.append(btn)
            layout.addWidget(btn)
            layout.addSpacing(2)

        # Set Chat as default active
        if self._nav_buttons:
            self._nav_buttons[0].setChecked(True)

        layout.addSpacing(24)

        # ── Conversations ──
        conv_label = QLabel("RECENT CHATS")
        conv_label.setObjectName("sidebar_section_label")
        f5 = QFont()
        f5.setPointSize(9)
        f5.setBold(True)
        conv_label.setFont(f5)
        layout.addWidget(conv_label)
        layout.addSpacing(4)

        # Scrollable conversation list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setObjectName("sidebar")
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setFixedHeight(200)

        self._conv_container = QWidget()
        self._conv_container.setObjectName("sidebar")
        self._conv_layout = QVBoxLayout(self._conv_container)
        self._conv_layout.setContentsMargins(0, 0, 0, 0)
        self._conv_layout.setSpacing(2)
        self._conv_layout.addStretch()

        scroll.setWidget(self._conv_container)
        layout.addWidget(scroll)

        layout.addStretch()

        # ── Model Selector ──
        model_label = QLabel("MODEL")
        model_label.setObjectName("sidebar_section_label")
        f6 = QFont()
        f6.setPointSize(9)
        f6.setBold(True)
        model_label.setFont(f6)
        layout.addWidget(model_label)
        layout.addSpacing(4)

        self.model_combo = QComboBox()
        self.model_combo.setObjectName("model_selector")
        for m in self.models:
            self.model_combo.addItem(m)
        self.model_combo.currentTextChanged.connect(self.model_changed.emit)
        self.model_combo.setCursor(Qt.PointingHandCursor)
        f7 = QFont()
        f7.setPointSize(11)
        self.model_combo.setFont(f7)
        self.model_combo.setFixedHeight(34)
        layout.addWidget(self.model_combo)

        layout.addSpacing(8)

        # ── Status dot ──
        self.ollama_status = QLabel("● Ollama disconnected")
        self.ollama_status.setObjectName("sidebar_section_label")
        fst = QFont()
        fst.setPointSize(10)
        self.ollama_status.setFont(fst)
        self.ollama_status.setStyleSheet("color: #ef4444;")
        layout.addWidget(self.ollama_status)

    def _on_nav(self, page_id: str):
        for btn in self._nav_buttons:
            btn.setChecked(btn.page_id == page_id)
        self.nav_changed.emit(page_id)

    def set_ollama_status(self, connected: bool):
        if connected:
            self.ollama_status.setText("● Ollama connected")
            self.ollama_status.setStyleSheet("color: #22c55e;")
        else:
            self.ollama_status.setText("● Ollama disconnected")
            self.ollama_status.setStyleSheet("color: #ef4444;")

    def update_models(self, models: list[str]):
        current = self.model_combo.currentText()
        self.model_combo.blockSignals(True)
        self.model_combo.clear()
        for m in models:
            self.model_combo.addItem(m)
        # restore selection if still available
        idx = self.model_combo.findText(current)
        if idx >= 0:
            self.model_combo.setCurrentIndex(idx)
        self.model_combo.blockSignals(False)

    def add_conversation(self, title: str, conv_id: str, select: bool = False):
        item = ConversationItem(title[:28] + "…" if len(title) > 28 else title, conv_id)
        item.clicked.connect(lambda: self.conversation_selected.emit(conv_id))
        self._conversations.append((conv_id, item))

        # Insert before the stretch at the end
        count = self._conv_layout.count()
        self._conv_layout.insertWidget(count - 1, item)

        if select:
            self._select_conversation(conv_id)

    def _select_conversation(self, conv_id: str):
        for cid, btn in self._conversations:
            btn.setProperty("active", cid == conv_id)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
