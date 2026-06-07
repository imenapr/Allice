"""
ALLICE — Right Context Panel
System stats, file explorer with selection, AI memory, and task status.
"""

import os
import psutil
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QProgressBar, QScrollArea, QFrame, QTreeWidget,
    QTreeWidgetItem, QPushButton, QFileDialog, QMessageBox,
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont

from core.file_manager import ProjectFileManager


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
    file_open_requested = Signal(str)       # relative path — open in editor
    selection_changed = Signal(list)       # list of selected relative paths
    project_changed = Signal(str)            # new project root path

    def __init__(self, file_manager: ProjectFileManager, parent=None):
        super().__init__(parent)
        self.setObjectName("right_panel")
        self.fm = file_manager
        self._path_to_item: dict[str, QTreeWidgetItem] = {}
        self._build()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh_stats)
        self._timer.start(2000)
        self._refresh_stats()
        self.refresh_file_tree()

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

        self._add_separator()

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

        self._add_separator()

        # ── Project Files ──
        files_header = QWidget()
        fh_layout = QHBoxLayout(files_header)
        fh_layout.setContentsMargins(16, 10, 16, 4)

        files_title = QLabel("PROJECT FILES")
        files_title.setObjectName("panel_section_title")
        ff = QFont()
        ff.setPointSize(9)
        ff.setBold(True)
        files_title.setFont(ff)
        fh_layout.addWidget(files_title)
        fh_layout.addStretch()
        self._content_layout.addWidget(files_header)

        # Project path + open button
        proj_row = QWidget()
        pr_layout = QHBoxLayout(proj_row)
        pr_layout.setContentsMargins(16, 0, 16, 4)

        self.project_path_label = QLabel(self.fm.project_name)
        self.project_path_label.setObjectName("stat_label")
        self.project_path_label.setToolTip(str(self.fm.project_root))
        pf = QFont()
        pf.setPointSize(10)
        self.project_path_label.setFont(pf)
        pr_layout.addWidget(self.project_path_label, stretch=1)

        open_btn = QPushButton("Open")
        open_btn.setObjectName("toggle_panel_btn")
        open_btn.setFixedHeight(22)
        open_btn.setCursor(Qt.PointingHandCursor)
        open_btn.setToolTip("Open a different project folder")
        open_btn.clicked.connect(self._open_project_dialog)
        pr_layout.addWidget(open_btn)
        self._content_layout.addWidget(proj_row)

        # Selection controls
        sel_row = QWidget()
        sr_layout = QHBoxLayout(sel_row)
        sr_layout.setContentsMargins(16, 0, 16, 4)
        sr_layout.setSpacing(4)

        self.selected_count_label = QLabel("0 selected")
        self.selected_count_label.setObjectName("stat_label")
        sf = QFont()
        sf.setPointSize(10)
        self.selected_count_label.setFont(sf)
        sr_layout.addWidget(self.selected_count_label)
        sr_layout.addStretch()

        for label, handler in [("All", self._select_all), ("None", self._clear_selection)]:
            btn = QPushButton(label)
            btn.setObjectName("toggle_panel_btn")
            btn.setFixedHeight(20)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(handler)
            sr_layout.addWidget(btn)

        refresh_btn = QPushButton("↻")
        refresh_btn.setObjectName("toggle_panel_btn")
        refresh_btn.setFixedSize(22, 20)
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.setToolTip("Refresh file tree")
        refresh_btn.clicked.connect(self.refresh_file_tree)
        sr_layout.addWidget(refresh_btn)
        self._content_layout.addWidget(sel_row)

        self.file_tree = QTreeWidget()
        self.file_tree.setObjectName("file_tree")
        self.file_tree.setHeaderHidden(True)
        self.file_tree.setIndentation(14)
        self.file_tree.setFixedHeight(220)
        ft_font = QFont()
        ft_font.setPointSize(11)
        self.file_tree.setFont(ft_font)
        self.file_tree.itemChanged.connect(self._on_item_changed)
        self.file_tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        self._content_layout.addWidget(self.file_tree)

        self._add_separator()

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

        self.ctx_files = QLabel("0 files selected")
        self.ctx_files.setObjectName("stat_label")
        self.ctx_files.setFont(fm2)
        m_layout.addWidget(self.ctx_files)

        self._content_layout.addWidget(mem_container)
        self._content_layout.addStretch()

        scroll.setWidget(content)
        layout.addWidget(scroll)

    def _add_separator(self):
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("background-color: #21262d; max-height: 1px;")
        self._content_layout.addWidget(sep)

    def refresh_file_tree(self):
        """Rebuild the file tree from the current project."""
        self.file_tree.blockSignals(True)
        self.file_tree.clear()
        self._path_to_item.clear()

        tree = self.fm.build_tree()
        root_entry = tree["_entry"]
        root_item = QTreeWidgetItem(self.file_tree, [f"📁 {root_entry.name}/"])
        root_item.setData(0, Qt.UserRole, "")
        root_item.setExpanded(True)

        self._populate_tree_node(root_item, tree["children"])
        self.file_tree.blockSignals(False)
        self._update_selection_label()

    def _populate_tree_node(self, parent_item: QTreeWidgetItem, children: dict):
        for name in sorted(children.keys(), key=lambda n: (not children[n]["_entry"].is_dir, n.lower())):
            node = children[name]
            entry = node["_entry"]

            if entry.is_dir:
                icon = "📁"
                label = f"{icon} {name}/"
                item = QTreeWidgetItem(parent_item, [label])
                item.setData(0, Qt.UserRole, entry.path)
                self._populate_tree_node(item, node["children"])
            else:
                ext = os.path.splitext(name)[1].lower()
                icon = self._file_icon(ext)
                size_str = self.fm.format_size(entry.size)
                label = f"{icon} {name}  ({size_str})"
                item = QTreeWidgetItem(parent_item, [label])
                item.setData(0, Qt.UserRole, entry.path)
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                item.setCheckState(0, Qt.Checked if entry.path in self.fm.selected_files else Qt.Unchecked)
                self._path_to_item[entry.path] = item

    @staticmethod
    def _file_icon(ext: str) -> str:
        icons = {
            ".py": "🐍", ".js": "📜", ".ts": "📜", ".tsx": "⚛",
            ".jsx": "⚛", ".html": "🌐", ".css": "🎨", ".json": "📋",
            ".md": "📝", ".txt": "📄", ".yml": "⚙", ".yaml": "⚙",
            ".toml": "⚙", ".qss": "🎨", ".sql": "🗄", ".sh": "💻",
        }
        return icons.get(ext, "📄")

    def _on_item_changed(self, item: QTreeWidgetItem, column: int):
        path = item.data(0, Qt.UserRole)
        if not path:
            return

        self.file_tree.blockSignals(True)
        if item.checkState(0) == Qt.Checked:
            self.fm.select_file(path)
        else:
            self.fm.deselect_file(path)
        self.file_tree.blockSignals(False)
        self._update_selection_label()
        self.selection_changed.emit(self.fm.selected_files)

    def _on_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        path = item.data(0, Qt.UserRole)
        if not path:
            return

        # Only open files, not directories
        if item.flags() & Qt.ItemIsUserCheckable:
            self.file_open_requested.emit(path)

    def _select_all(self):
        self.file_tree.blockSignals(True)
        self.fm.select_all_files()
        for path, item in self._path_to_item.items():
            item.setCheckState(0, Qt.Checked)
        self.file_tree.blockSignals(False)
        self._update_selection_label()
        self.selection_changed.emit(self.fm.selected_files)

    def _clear_selection(self):
        self.file_tree.blockSignals(True)
        self.fm.clear_selection()
        for item in self._path_to_item.values():
            item.setCheckState(0, Qt.Unchecked)
        self.file_tree.blockSignals(False)
        self._update_selection_label()
        self.selection_changed.emit(self.fm.selected_files)

    def _update_selection_label(self):
        count = len(self.fm.selected_files)
        self.selected_count_label.setText(f"{count} selected")
        self.ctx_files.setText(f"{count} file{'s' if count != 1 else ''} selected")

    def _open_project_dialog(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "Open Project Folder",
            str(self.fm.project_root),
        )
        if not folder:
            return

        ok, err = self.fm.set_project_root(folder)
        if not ok:
            QMessageBox.warning(self, "Cannot Open Project", err)
            return

        self.project_path_label.setText(self.fm.project_name)
        self.project_path_label.setToolTip(str(self.fm.project_root))
        self.refresh_file_tree()
        self.project_changed.emit(str(self.fm.project_root))

    def _refresh_stats(self):
        cpu = psutil.cpu_percent(interval=None)
        self.cpu_row.update(cpu)

        mem = psutil.virtual_memory()
        ram_pct = mem.percent
        ram_used = mem.used / (1024 ** 3)
        ram_total = mem.total / (1024 ** 3)
        self.ram_row.update(ram_pct, f"{ram_used:.1f}/{ram_total:.0f}GB")

        try:
            import subprocess
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=1,
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
