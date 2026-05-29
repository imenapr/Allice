import tkinter as tk
from tkinter import ttk


class AlliceUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Allice AI")
        self.root.geometry("1000x620")
        self.root.minsize(900, 560)
        self.root.configure(bg="#0f172a")

        # ---------- STYLE ----------
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "Modern.TButton",
            font=("Segoe UI", 11, "bold"),
            padding=10,
            foreground="white",
            background="#2563eb",
            borderwidth=0
        )

        style.map(
            "Modern.TButton",
            background=[("active", "#1d4ed8")]
        )

        # ---------- SIDEBAR ----------
        sidebar = tk.Frame(root, bg="#111827", width=220)
        sidebar.pack(side="left", fill="y")

        logo = tk.Label(
            sidebar,
            text="AL LICE",
            fg="white",
            bg="#111827",
            font=("Segoe UI", 24, "bold")
        )
        logo.pack(pady=(30, 10))

        subtitle = tk.Label(
            sidebar,
            text="Desktop AI Assistant",
            fg="#9ca3af",
            bg="#111827",
            font=("Segoe UI", 10)
        )
        subtitle.pack()

        menu_frame = tk.Frame(sidebar, bg="#111827")
        menu_frame.pack(pady=40)

        self.create_menu_button(menu_frame, "🏠 Dashboard")
        self.create_menu_button(menu_frame, "💬 Chat")
        self.create_menu_button(menu_frame, "🧠 Memory")
        self.create_menu_button(menu_frame, "⚙ Settings")

        # ---------- MAIN AREA ----------
        main = tk.Frame(root, bg="#0f172a")
        main.pack(side="right", fill="both", expand=True)

        topbar = tk.Frame(main, bg="#111827", height=70)
        topbar.pack(fill="x")

        title = tk.Label(
            topbar,
            text="Welcome back, Nick 👋",
            fg="white",
            bg="#111827",
            font=("Segoe UI", 20, "bold")
        )
        title.pack(side="left", padx=25, pady=15)

        # ---------- CONTENT ----------
        content = tk.Frame(main, bg="#0f172a")
        content.pack(fill="both", expand=True, padx=25, pady=25)

        # LEFT PANEL
        left_panel = tk.Frame(
            content,
            bg="#111827",
            bd=0,
            highlightthickness=0
        )
        left_panel.pack(side="left", fill="both", expand=True)

        left_title = tk.Label(
            left_panel,
            text="Allice Console",
            fg="white",
            bg="#111827",
            font=("Segoe UI", 16, "bold")
        )
        left_title.pack(anchor="w", padx=20, pady=(20, 10))

        self.chat_box = tk.Text(
            left_panel,
            bg="#1f2937",
            fg="#e5e7eb",
            insertbackground="white",
            relief="flat",
            font=("Consolas", 11),
            wrap="word"
        )
        self.chat_box.pack(fill="both", expand=True, padx=20, pady=10)

        self.chat_box.insert(
            "end",
            "Allice initialized successfully...\n\n"
            "> Vision System: ONLINE\n"
            "> Voice Module: READY\n"
            "> PC Control: ACTIVE\n"
            "> Neural Interface: STANDBY\n\n"
        )

        bottom_input = tk.Frame(left_panel, bg="#111827")
        bottom_input.pack(fill="x", padx=20, pady=20)

        self.entry = tk.Entry(
            bottom_input,
            bg="#1f2937",
            fg="white",
            insertbackground="white",
            relief="flat",
            font=("Segoe UI", 11)
        )
        self.entry.pack(side="left", fill="x", expand=True, ipady=10)

        send_btn = ttk.Button(
            bottom_input,
            text="Send",
            style="Modern.TButton",
            command=self.send_message
        )
        send_btn.pack(side="left", padx=10)

        # RIGHT PANEL
        right_panel = tk.Frame(
            content,
            bg="#111827",
            width=260
        )
        right_panel.pack(side="right", fill="y", padx=(20, 0))

        stats_title = tk.Label(
            right_panel,
            text="System Status",
            fg="white",
            bg="#111827",
            font=("Segoe UI", 15, "bold")
        )
        stats_title.pack(anchor="w", padx=20, pady=(20, 15))

        self.create_status_card(right_panel, "CPU Usage", "21%")
        self.create_status_card(right_panel, "RAM Usage", "4.2 GB")
        self.create_status_card(right_panel, "GPU Temp", "57°C")
        self.create_status_card(right_panel, "AI State", "ONLINE")

    def create_menu_button(self, parent, text):
        btn = tk.Button(
            parent,
            text=text,
            fg="white",
            bg="#1f2937",
            activebackground="#374151",
            activeforeground="white",
            relief="flat",
            font=("Segoe UI", 11),
            padx=20,
            pady=12,
            width=18,
            anchor="w",
            cursor="hand2"
        )
        btn.pack(pady=6)

    def create_status_card(self, parent, title, value):
        card = tk.Frame(parent, bg="#1f2937")
        card.pack(fill="x", padx=20, pady=8)

        tk.Label(
            card,
            text=title,
            fg="#9ca3af",
            bg="#1f2937",
            font=("Segoe UI", 10)
        ).pack(anchor="w", padx=15, pady=(12, 0))

        tk.Label(
            card,
            text=value,
            fg="white",
            bg="#1f2937",
            font=("Segoe UI", 16, "bold")
        ).pack(anchor="w", padx=15, pady=(2, 12))

    def send_message(self):
        message = self.entry.get().strip()

        if not message:
            return

        # print user message
        self.add_message("You", message)

        # fake AI response
        response = self.generate_response(message)

        # print AI response
        self.add_message("Allice", response)

        self.entry.delete(0, "end")

    def add_message(self, sender, text):
        self.chat_box.insert("end", f"{sender}: {text}\n\n")
        self.chat_box.see("end")

    def generate_response(self, message):
        message = message.lower()

        if "hello" in message:
            return "Hello Nick 👋"

        elif "open youtube" in message:
            return "Opening YouTube..."

        elif "how are you" in message:
            return "Systems operating normally."

        else:
            return f"I received: {message}"


if __name__ == "__main__":
    root = tk.Tk()
    app = AlliceUI(root)
    root.mainloop()