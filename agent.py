import os
import json
from ollama import chat

MODEL = "qwen2.5-coder:7b"

# ---------- FILE SYSTEM ----------

def read_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except:
        return ""

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

# ---------- AI CALL ----------

def ask(prompt):
    res = chat(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}]
    )
    return res["message"]["content"]

# ---------- TOOL EXECUTOR ----------

def execute(action):
    if action["action"] == "read_file":
        return read_file(action["path"])

    if action["action"] == "write_file":
        write_file(action["path"], action["content"])
        return "file_written"

    if action["action"] == "done":
        return "done"

    return "unknown_action"

# ---------- AGENT LOOP ----------

def run_task(task):
    print("\n🧠 TASK START:", task)

    context = ""

    for step in range(20):  # safety limit
        prompt = f"""
You are a senior autonomous coding agent.

TASK:
{task}

CONTEXT:
{context}

You must respond with ONE JSON action only:

Actions:
1. read_file
{{"action":"read_file","path":"file.js"}}

2. write_file
{{"action":"write_file","path":"file.js","content":"..."}}

3. done
{{"action":"done","reason":"..."}}

RULES:
- no text
- no markdown
- only JSON
"""

        response = ask(prompt)

        try:
            action = json.loads(response)
        except:
            print("⚠ invalid JSON, retrying...")
            continue

        result = execute(action)

        print(f"\n⚙️ ACTION: {action}")
        print(f"📦 RESULT: {str(result)[:200]}")

        context += f"\nACTION: {action}\nRESULT: {result}\n"

        if action["action"] == "done":
            print("\n✅ TASK COMPLETE")
            break

# ---------- CLI ----------

def run():
    print("ALLICE v6 AUTONOMOUS AGENT ⚡")
    print("Commands:")
    print("  run <task>")
    print("  exit\n")

    while True:
        cmd = input("> ")

        if cmd == "exit":
            break

        if cmd.startswith("run "):
            task = cmd[4:]
            run_task(task)
        else:
            print("Use: run <task>")

run()