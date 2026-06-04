import tkinter as tk
from tkinter import ttk

BG_LIGHT = "#f6f7fb"
BG_DARK = "#0b0f19"
PANEL = "#111827"
BORDER = "#2a2f3a"

TEXT = "#e5e7eb"
MUTED = "#9ca3af"

USER_BUBBLE = "#ffffff"
ASSIST_BUBBLE = "#eef2ff"

ACCENT = "#4f46e5"


class ChatApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Co-Dev GPT UI")
        self.geometry("1200x800")
        self.configure(bg=BG_LIGHT)

        self._build_ui()

    # ---------------- UI ----------------
    def _build_ui(self):
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        self._sidebar()
        self._main()

    # ---------------- Sidebar ----------------
    def _sidebar(self):
        side = tk.Frame(self, bg=BG_DARK, width=280)
        side.grid(row=0, column=0, sticky="ns")
        side.pack_propagate(False)

        tk.Label(
            side,
            text="☰  Menu",
            bg=BG_DARK,
            fg=TEXT,
            font=("Segoe UI", 12, "bold")
        ).pack(anchor="w", padx=15, pady=15)

        tk.Button(
            side,
            text="+ New Chat",
            bg=PANEL,
            fg=TEXT,
            relief="flat",
            activebackground="#1f2937",
            activeforeground="white",
            font=("Segoe UI", 11),
            pady=10
        ).pack(fill="x", padx=15, pady=10)

        # placeholder chat list
        for i in range(6):
            tk.Button(
                side,
                text=f"Chat {i+1}",
                bg=BG_DARK,
                fg=MUTED,
                relief="flat",
                anchor="w",
                activebackground="#111827",
                activeforeground="white"
            ).pack(fill="x", padx=15, pady=5)

    # ---------------- Main ----------------
    def _main(self):
        main = tk.Frame(self, bg=BG_LIGHT)
        main.grid(row=0, column=1, sticky="nsew")
        main.rowconfigure(1, weight=1)
        main.columnconfigure(0, weight=1)

        self._topbar(main)
        self._chat_area(main)
        self._composer(main)

    # ---------------- Top bar ----------------
    def _topbar(self, parent):
        bar = tk.Frame(parent, bg=BG_LIGHT, height=60)
        bar.grid(row=0, column=0, sticky="ew")
        bar.pack_propagate(False)

        tk.Button(bar, text="🗑", bg=BG_LIGHT, relief="flat", font=("Segoe UI", 12)).pack(side="left", padx=10)

        search = tk.Entry(bar, font=("Segoe UI", 11))
        search.insert(0, "Search")
        search.pack(side="right", padx=20, ipadx=10, ipady=4)

    # ---------------- Chat area ----------------
    def _chat_area(self, parent):
        self.chat = tk.Frame(parent, bg=BG_LIGHT)
        self.chat.grid(row=1, column=0, sticky="nsew")

        self.add_message("assistant",
            "This AI chatbot has been developed to optimize communication and simplify workflows."
        )

    def add_message(self, role, text):
        wrap = tk.Frame(self.chat, bg=BG_LIGHT)
        wrap.pack(fill="x", pady=10, padx=20)

        is_user = role == "user"

        bubble_color = USER_BUBBLE if is_user else ASSIST_BUBBLE
        anchor = "e" if is_user else "w"

        container = tk.Frame(wrap, bg=BG_LIGHT)
        container.pack(fill="x", anchor=anchor)

        bubble = tk.Frame(
            container,
            bg=bubble_color,
            padx=14,
            pady=10,
            highlightthickness=1,
            highlightbackground="#d1d5db"
        )
        bubble.pack(anchor=anchor, padx=(200 if is_user else 0, 0 if is_user else 200))

        tk.Label(
            bubble,
            text=text,
            bg=bubble_color,
            fg="#111827",
            font=("Segoe UI", 11),
            wraplength=500,
            justify="left"
        ).pack()

    # ---------------- Composer ----------------
    def _composer(self, parent):
        box = tk.Frame(parent, bg="white", highlightthickness=1, highlightbackground="#d1d5db")
        box.grid(row=2, column=0, sticky="ew", padx=20, pady=15)
        box.columnconfigure(1, weight=1)

        tk.Label(box, text="📎", bg="white", font=("Segoe UI", 14)).grid(row=0, column=0, padx=10)

        entry = tk.Entry(box, font=("Segoe UI", 12), bd=0)
        entry.insert(0, "Type a new message here")
        entry.grid(row=0, column=1, sticky="ew", padx=5, pady=10)

        tk.Label(box, text="🙂", bg="white", font=("Segoe UI", 14)).grid(row=0, column=2, padx=10)

        tk.Button(
            box,
            text="➤",
            bg=ACCENT,
            fg="white",
            bd=0,
            font=("Segoe UI", 12),
            padx=12,
            pady=6
        ).grid(row=0, column=3, padx=10)


if __name__ == "__main__":
    app = ChatApp()
    app.mainloop()