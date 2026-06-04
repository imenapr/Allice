import tkinter as tk
from tkinter import ttk
import webbrowser
import psutil
import requests
import json
import threading
import subprocess


# ---------------- CHAT UI ----------------
class ChatCanvas(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#111827")

        self.canvas = tk.Canvas(self, bg="#0f172a", highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)

        self.inner = tk.Frame(self.canvas, bg="#0f172a")

        self.inner.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas_window = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")

        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.canvas.bind("<Configure>", self._resize)

    def _resize(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def add_bubble(self, role, text):
        is_user = role.lower() in ["you", "user"]

        bubble_color = "#ffffff" if is_user else "#eef2ff"
        text_color = "#111827"

        wrapper = tk.Frame(self.inner, bg="#0f172a")
        wrapper.pack(fill="x", pady=8, padx=20)

        align = "e" if is_user else "w"

        container = tk.Frame(wrapper, bg="#0f172a")
        container.pack(fill="x", anchor=align)

        bubble = tk.Frame(
            container,
            bg=bubble_color,
            padx=12,
            pady=8,
            highlightthickness=1,
            highlightbackground="#d1d5db"
        )
        bubble.pack(anchor=align)

        tk.Label(
            bubble,
            text="You" if is_user else "ALLICE",
            bg=bubble_color,
            fg="#4f46e5" if not is_user else "#6b7280",
            font=("Segoe UI", 9, "bold")
        ).pack(anchor="w")

        tk.Label(
            bubble,
            text=text,
            bg=bubble_color,
            fg=text_color,
            font=("Segoe UI", 11),
            wraplength=520,
            justify="left"
        ).pack(anchor="w")

        self.canvas.yview_moveto(1)


# ---------------- MAIN APP ----------------
class AlliceUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ALLICE AI")
        self.root.geometry("1000x620")
        self.root.configure(bg="#0f172a")

        # Ollama config
        self.OLLAMA_URL = "http://localhost:11434/api/chat"
        self.models = ["qwen3.5:4b", "qwen2.5-coder:7b"]
        self.current_model_index = 1

        self.messages = [
            {
                "role": "system",
                "content": "You are ALLICE, a helpful coding assistant."
            }
        ]

        # ---------------- UI ----------------
        main = tk.Frame(root, bg="#0f172a")
        main.pack(fill="both", expand=True)

        top = tk.Frame(main, bg="#111827", height=60)
        top.pack(fill="x")

        tk.Label(
            top,
            text="ALLICE AI",
            bg="#111827",
            fg="white",
            font=("Segoe UI", 16, "bold")
        ).pack(side="left", padx=20)

        self.model_btn = ttk.Button(
            top,
            text=self.models[self.current_model_index],
            command=self.toggle_model
        )
        self.model_btn.pack(side="right", padx=20)

        content = tk.Frame(main, bg="#0f172a")
        content.pack(fill="both", expand=True, padx=20, pady=20)

        self.chat = ChatCanvas(content)
        self.chat.pack(fill="both", expand=True)

        bottom = tk.Frame(content, bg="#0f172a")
        bottom.pack(fill="x", pady=10)

        self.entry = tk.Entry(bottom, font=("Segoe UI", 12))
        self.entry.pack(side="left", fill="x", expand=True)

        send = ttk.Button(bottom, text="Send", command=self.send)
        send.pack(side="left", padx=10)

    # ---------------- MESSAGE HANDLING ----------------
    def add_message(self, role, text):
        self.root.after(0, lambda: self.chat.add_bubble(role, text))

    def send(self):
        msg = self.entry.get().strip()
        if not msg:
            return

        self.entry.delete(0, "end")

        self.add_message("You", msg)

        self.entry.config(state="disabled")
        threading.Thread(target=self.ask_ai, args=(msg,), daemon=True).start()

    # ---------------- OLLAMA ----------------
    def ask_ai(self, msg):
        try:
            self.messages.append({"role": "user", "content": msg})

            payload = {
                "model": self.models[self.current_model_index],
                "messages": self.messages,
                "stream": True
            }

            res = requests.post(self.OLLAMA_URL, json=payload, stream=True)

            reply = ""

            for line in res.iter_lines():
                if not line:
                    continue

                data = json.loads(line)

                content = data.get("message", {}).get("content", "")
                reply += content

            self.messages.append({"role": "assistant", "content": reply})
            self.add_message("ALLICE", reply)

        except Exception as e:
            self.add_message("ALLICE", f"Error: {e}")

        finally:
            self.root.after(0, lambda: self.entry.config(state="normal"))

    # ---------------- MODEL SWITCH ----------------
    def toggle_model(self):
        self.current_model_index = (self.current_model_index + 1) % len(self.models)
        self.model_btn.config(text=self.models[self.current_model_index])
        self.add_message("ALLICE", f"Switched to {self.models[self.current_model_index]}")


# ---------------- RUN ----------------
if __name__ == "__main__":
    root = tk.Tk()
    app = AlliceUI(root)
    root.mainloop()