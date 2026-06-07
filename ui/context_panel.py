"""
ALLICE — Right Context Panel
System stats, file explorer, AI memory, and task status.
"""

import psutil
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QProgressBar, QScrollArea, QFrame, QTreeWidget,
    QTreeWidgetItem, QPushButton, QSizePolicy,
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont, QIcon


class StatRow(QWidget):
    def __init__(self, label: str, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(3)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)

        lbl = QLabel(label)
        lbl.setObjectName("stat_label")
        f = QFont()
        f.setPointSize(11)
        lbl.setFont(f)
        row.addWidget(lbl)
        row.addStretch()

        self.value_label = QLabel("—")
        self.value_label.setObjectName("stat_value")
        fv = QFont()
        fv.setPointSize(11)
        fv.setBold(True)
        self.value_label.setFont(fv)
        row.addWidget(self.value_label)

        layout.addLayout(row)

        self.bar = QProgressBar()
        self.bar.setRange(0, 100)
        self.bar.setValue(0)
        self.bar.setFixedHeight(4)
        self.bar.setTextVisible(False)
        layout.addWidget(self.bar)

    def update(self, percent: float, label: str = None):
        self.bar.setValue(int(percent))
        if label:
            self.value_label.setText(label)
        else:
            self.value_label.setText(f"{percent:.0f}%")

        # Color coding
        if percent > 85:
            self.bar.setProperty("danger", True)
            self.bar.setProperty("warning", False)
        elif percent > 65:
            self.bar.setProperty("warning", True)
            self.bar.setProperty("danger", False)
        else:
            self.bar.setProperty("warning", False)
            self.bar.setProperty("danger", False)
        self.bar.style().unpolish(self.bar)
        self.bar.style().polish(self.bar)


class SectionHeader(QWidget):
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 4)

        lbl = QLabel(title)
        lbl.setObjectName("panel_section_title")
        f = QFont()
        f.setPointSize(9)
        f.setBold(True)
        lbl.setFont(f)
        layout.addWidget(lbl)
        layout.addStretch()


class ContextPanel(QWidget):
    panel_close_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("right_panel")
        self._build()

        # Stats refresh timer
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh_stats)
        self._timer.start(2000)
        self._refresh_stats()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Header ──
        header = QWidget()
        header.setObjectName("right_panel")
        header.setFixedHeight(44)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(16, 0, 8, 0)

        title = QLabel("CONTEXT")
        title.setObjectName("right_panel_header")
        f = QFont()
        f.setPointSize(10)
        f.setBold(True)
        title.setFont(f)
        h_layout.addWidget(title)
        h_layout.addStretch()

        close_btn = QPushButton("✕")
        close_btn.setObjectName("toggle_panel_btn")
        close_btn.setFixedSize(24, 24)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(self.panel_close_requested.emit)
        h_layout.addWidget(close_btn)

        layout.addWidget(header)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("background-color: #21262d; max-height: 1px;")
        layout.addWidget(sep)

        # Scrollable content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setObjectName("right_panel")
        scroll.setFrameShape(QFrame.NoFrame)

        content = QWidget()
        content.setObjectName("right_panel")
        self._content_layout = QVBoxLayout(content)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(0)

        # ── AI Status ──
        self._content_layout.addWidget(SectionHeader("AI STATUS"))

        status_container = QWidget()
        status_container.setObjectName("right_panel")
        s_layout = QVBoxLayout(status_container)
        s_layout.setContentsMargins(16, 4, 16, 12)
        s_layout.setSpacing(6)

        self.agent_state_row = QHBoxLayout()
        self.agent_dot = QLabel("●")
        self.agent_dot.setObjectName("status_dot_idle")
        fd = QFont()
        fd.setPointSize(8)
        self.agent_dot.setFont(fd)
        self.agent_state_row.addWidget(self.agent_dot)

        self.agent_state_label = QLabel("Ready")
        fs = QFont()
        fs.setPointSize(12)
        self.agent_state_label.setFont(fs)
        self.agent_state_label.setObjectName("stat_label")
        self.agent_state_row.addWidget(self.agent_state_label)
        self.agent_state_row.addStretch()
        s_layout.addLayout(self.agent_state_row)

        self.model_label = QLabel("Model: —")
        self.model_label.setObjectName("stat_label")
        fm = QFont()
        fm.setPointSize(11)
        self.model_label.setFont(fm)
        s_layout.addWidget(self.model_label)

        self._content_layout.addWidget(status_container)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet("background-color: #21262d; max-height: 1px;")
        self._content_layout.addWidget(sep2)

        # ── System Stats ──
        self._content_layout.addWidget(SectionHeader("SYSTEM"))

        stats_container = QWidget()
        stats_container.setObjectName("right_panel")
        st_layout = QVBoxLayout(stats_container)
        st_layout.setContentsMargins(16, 4, 16, 12)
        st_layout.setSpacing(2)

        self.cpu_row = StatRow("CPU")
        self.ram_row = StatRow("RAM")
        self.gpu_row = StatRow("GPU")

        st_layout.addWidget(self.cpu_row)
        st_layout.addWidget(self.ram_row)
        st_layout.addWidget(self.gpu_row)
        self._content_layout.addWidget(stats_container)

        sep3 = QFrame()
        sep3.setFrameShape(QFrame.HLine)
        sep3.setStyleSheet("background-color: #21262d; max-height: 1px;")
        self._content_layout.addWidget(sep3)

        # ── Project Files ──
        self._content_layout.addWidget(SectionHeader("PROJECT FILES"))

        self.file_tree = QTreeWidget()
        self.file_tree.setObjectName("file_tree")
        self.file_tree.setHeaderHidden(True)
        self.file_tree.setIndentation(14)
        self.file_tree.setFixedHeight(200)
        ft_font = QFont()
        ft_font.setPointSize(11)
        self.file_tree.setFont(ft_font)
        self._content_layout.addWidget(self.file_tree)

        self._populate_default_tree()

        sep4 = QFrame()
        sep4.setFrameShape(QFrame.HLine)
        sep4.setStyleSheet("background-color: #21262d; max-height: 1px;")
        self._content_layout.addWidget(sep4)

        # ── Context Memory ──
        self._content_layout.addWidget(SectionHeader("CONTEXT MEMORY"))

        mem_container = QWidget()
        mem_container.setObjectName("right_panel")
        m_layout = QVBoxLayout(mem_container)
        m_layout.setContentsMargins(16, 4, 16, 12)

        self.ctx_messages = QLabel("0 messages in context")
        self.ctx_messages.setObjectName("stat_label")
        fm2 = QFont()
        fm2.setPointSize(11)
        self.ctx_messages.setFont(fm2)
        m_layout.addWidget(self.ctx_messages)

        self.ctx_tokens = QLabel("~0 tokens")
        self.ctx_tokens.setObjectName("stat_label")
        self.ctx_tokens.setFont(fm2)
        m_layout.addWidget(self.ctx_tokens)

        self._content_layout.addWidget(mem_container)
        self._content_layout.addStretch()

        scroll.setWidget(content)
        layout.addWidget(scroll)

    def _populate_default_tree(self):
        self.file_tree.clear()
        root = QTreeWidgetItem(self.file_tree, ["📁 allice/"])
        root.setExpanded(True)

        for name in ["main.py", "README.md"]:
            QTreeWidgetItem(root, [f"📄 {name}"])

        core = QTreeWidgetItem(root, ["📁 core/"])
        for name in ["ollama_client.py", "agent.py"]:
            QTreeWidgetItem(core, [f"🐍 {name}"])

        ui = QTreeWidgetItem(root, ["📁 ui/"])
        for name in ["app.py", "sidebar.py", "workspace.py"]:
            QTreeWidgetItem(ui, [f"🐍 {name}"])

    def _refresh_stats(self):
        # CPU
        cpu = psutil.cpu_percent(interval=None)
        self.cpu_row.update(cpu)

        # RAM
        mem = psutil.virtual_memory()
        ram_pct = mem.percent
        ram_used = mem.used / (1024 ** 3)
        ram_total = mem.total / (1024 ** 3)
        self.ram_row.update(ram_pct, f"{ram_used:.1f}/{ram_total:.0f}GB")

        # GPU — optional, graceful fallback
        try:
            import subprocess
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=1
            )
            if result.returncode == 0:
                gpu_pct = float(result.stdout.strip())
                self.gpu_row.update(gpu_pct)
            else:
                self.gpu_row.value_label.setText("N/A")
                self.gpu_row.bar.setValue(0)
        except Exception:
            self.gpu_row.value_label.setText("N/A")
            self.gpu_row.bar.setValue(0)

    def update_agent_state(self, state_name: str, label: str):
        self.agent_state_label.setText(label)
        colors = {
            "idle": "#484f58",
            "thinking": "#f59e0b",
            "coding": "#7c3aed",
            "executing": "#22c55e",
            "reading": "#38bdf8",
            "error": "#ef4444",
        }
        color = colors.get(state_name, "#484f58")
        self.agent_dot.setStyleSheet(f"color: {color};")

    def update_model(self, model: str):
        self.model_label.setText(f"Model: {model}")

    def update_context(self, message_count: int, token_estimate: int):
        self.ctx_messages.setText(f"{message_count} messages in context")
        self.ctx_tokens.setText(f"~{token_estimate:,} tokens")
