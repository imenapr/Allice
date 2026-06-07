"""
ALLICE - AI Software Engineering Assistant
Entry point.

Startup notes:
  The old entry point imported PySide6 and ui.app at module import time. That
  meant users saw no feedback while Qt, Pygments, psutil, requests, and the UI
  tree initialized. The right context panel also performed blocking Windows
  system probes during construction. This file now starts a tiny tkinter splash
  process before heavy imports, then profiles each startup phase.

Run:
  python main.py

Profile:
  python main.py --profile-startup
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path


APP_DIR = Path(__file__).resolve().parent
LOGO_PATH = APP_DIR / "images" / "logo.png"
THEME_PATH = APP_DIR / "styles" / "theme.qss"


class StartupProfiler:
    """Small wall-clock profiler for startup phases."""

    def __init__(self, enabled: bool = False):
        self.enabled = enabled
        self._last = time.perf_counter()
        self._events: list[tuple[str, float]] = []

    def mark(self, label: str) -> None:
        if not self.enabled:
            return
        now = time.perf_counter()
        self._events.append((label, now - self._last))
        self._last = now

    def report(self) -> None:
        if not self.enabled:
            return
        print("\nALLICE startup profile:")
        for label, elapsed in sorted(self._events, key=lambda item: item[1], reverse=True):
            print(f"  {elapsed:8.3f}s  {label}")
        print("")


def run_splash() -> int:
    """
    Standalone tkinter loading screen.

    It intentionally runs as a separate process so it stays responsive while the
    main process imports Qt and builds the app. Mixing tkinter and PySide event
    loops in one process would make one of them freeze.
    """
    import tkinter as tk
    from tkinter import ttk

    root = tk.Tk()
    root.title("ALLICE")
    root.configure(bg="black")
    root.overrideredirect(True)
    root.attributes("-topmost", True)

    width, height = 520, 360
    x = max(0, (root.winfo_screenwidth() - width) // 2)
    y = max(0, (root.winfo_screenheight() - height) // 2)
    root.geometry(f"{width}x{height}+{x}+{y}")

    frame = tk.Frame(root, bg="black")
    frame.pack(expand=True, fill="both")

    logo_label = tk.Label(frame, bg="black")
    logo_label.pack(expand=True, pady=(46, 18))

    # tkinter can load PNG files on modern Python/Tk builds. If that fails, the
    # text fallback keeps the splash functional instead of delaying startup.
    image = None
    if LOGO_PATH.exists():
        try:
            image = tk.PhotoImage(file=str(LOGO_PATH))
            max_width, max_height = 220, 180
            scale = max(1, int(max(image.width() / max_width, image.height() / max_height)))
            if scale > 1:
                image = image.subsample(scale, scale)
            logo_label.configure(image=image)
            logo_label.image = image
        except tk.TclError:
            logo_label.configure(text="ALLICE", fg="white", font=("Segoe UI", 34, "bold"))
    else:
        logo_label.configure(text="ALLICE", fg="white", font=("Segoe UI", 34, "bold"))

    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure(
        "Allice.Horizontal.TProgressbar",
        background="#7c3aed",
        troughcolor="#161b22",
        bordercolor="#161b22",
        lightcolor="#7c3aed",
        darkcolor="#7c3aed",
    )

    bar = ttk.Progressbar(
        frame,
        mode="indeterminate",
        length=320,
        style="Allice.Horizontal.TProgressbar",
    )
    bar.pack(pady=(0, 14))
    bar.start(12)

    label = tk.Label(
        frame,
        text="Starting ALLICE...",
        bg="black",
        fg="#8b949e",
        font=("Segoe UI", 11),
    )
    label.pack(pady=(0, 36))

    root.mainloop()
    return 0


def start_splash_process(enabled: bool = True) -> subprocess.Popen | None:
    if not enabled:
        return None
    try:
        return subprocess.Popen(
            [sys.executable, str(Path(__file__).resolve()), "--splash"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except Exception:
        # Splash is feedback only. Never block the real application if tkinter
        # or process creation is unavailable on a user machine.
        return None


def stop_splash_process(process: subprocess.Popen | None) -> None:
    if process is None or process.poll() is not None:
        return
    try:
        process.terminate()
        process.wait(timeout=2)
    except Exception:
        try:
            process.kill()
        except Exception:
            pass


def load_theme(app) -> None:
    try:
        app.setStyleSheet(THEME_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"[ALLICE] Warning: theme.qss not found at {THEME_PATH}")


def set_windows_app_id() -> None:
    """Give Windows taskbar a stable app identity for the custom icon."""
    if sys.platform != "win32":
        return
    try:
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "Allice.AISoftwareEngineeringAssistant"
        )
    except Exception:
        pass


def run_app(profile_startup: bool = False, show_splash: bool = True) -> int:
    profiler = StartupProfiler(profile_startup)

    # Show feedback before importing PySide6 or ui.app. Those imports are the
    # first heavy phase and previously happened while the user saw nothing.
    splash = start_splash_process(show_splash)
    profiler.mark("start splash process")

    sys.path.insert(0, str(APP_DIR))

    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QFont, QIcon

    profiler.mark("import PySide6")

    from ui.app import AlliceWindow

    profiler.mark("import ALLICE UI modules")

    set_windows_app_id()
    app = QApplication(sys.argv)
    app.setApplicationName("ALLICE")
    app.setOrganizationName("ALLICE")
    icon = QIcon(str(LOGO_PATH))
    if not icon.isNull():
        app.setWindowIcon(icon)
    profiler.mark("create QApplication")

    font = QFont("Segoe UI", 12)
    font.setStyleStrategy(QFont.PreferAntialias)
    app.setFont(font)
    load_theme(app)
    profiler.mark("load font and stylesheet")

    window = AlliceWindow()
    if not icon.isNull():
        window.setWindowIcon(icon)
    profiler.mark("construct main window")

    window.show()
    profiler.mark("show main window")
    profiler.report()

    stop_splash_process(splash)
    return app.exec()


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ALLICE")
    parser.add_argument("--splash", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--no-splash", action="store_true", help="Disable loading screen")
    parser.add_argument("--profile-startup", action="store_true", help="Print startup phase timings")
    return parser.parse_args(argv)


def main() -> int:
    args = parse_args(sys.argv[1:])
    if args.splash:
        return run_splash()
    return run_app(
        profile_startup=args.profile_startup,
        show_splash=not args.no_splash,
    )


if __name__ == "__main__":
    raise SystemExit(main())
