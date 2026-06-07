# ALLICE — AI Software Engineering Assistant

A professional AI coding assistant built with PySide6 and Ollama.
Inspired by Claude Desktop, Cursor, and Linear.

---

## Requirements

- Python 3.11+
- [Ollama](https://ollama.ai) running locally
- At least one model pulled (e.g. `ollama pull qwen2.5-coder:7b`)

## Setup

```bash
# 1. Start Ollama (in a separate terminal)
ollama serve

# 2. Run ALLICE
python main.py
```

---

## Architecture

```
allice/
├── main.py                    # Entry point
├── requirements.txt
├── styles/
│   └── theme.qss              # Global dark theme (QSS)
├── core/
│   ├── ollama_client.py       # Ollama streaming API client
│   └── agent.py               # Agent state machine (thinking/coding/idle)
└── ui/
    ├── app.py                 # Main window (assembles all panels)
    ├── sidebar.py             # Left sidebar (nav, models, conversations)
    ├── workspace.py           # Center workspace (messages, input, terminal)
    ├── context_panel.py       # Right panel (stats, files, memory)
    └── components/
        └── message_block.py   # Claude-style message rendering + code blocks
```

## Layout

```
┌──────────────┬────────────────────────────────┬─────────────────┐
│   SIDEBAR    │         WORKSPACE              │  CONTEXT PANEL  │
│              │                                │                 │
│ ALLICE  [AI] │  Conversation title    ~tokens │ AI STATUS       │
│              │ ─────────────────────────────  │ ● Ready         │
│ + New Chat   │                                │ Model: qwen...  │
│              │  ALLICE                        │                 │
│ WORKSPACE    │  Here's how to do that:        │ SYSTEM          │
│ 💬 Chat      │                                │ CPU  ██░░  24%  │
│ 📁 Projects  │  ```python                     │ RAM  ████  61%  │
│ 🔍 Search    │  def hello():                  │ GPU  ░░░░  N/A  │
│ ⚙️ Settings  │      return "world"            │                 │
│              │  ```                           │ PROJECT FILES   │
│ RECENT CHATS │                                │ 📁 allice/      │
│ New Chat #1  │  You                           │   📄 main.py    │
│              │  Explain this to me            │   📁 core/      │
│              │ ─────────────────────────────  │                 │
│ MODEL        │  [📎] [Ask ALLICE...] [⌨] Send │ CONTEXT MEMORY  │
│ qwen2.5-...  │  ↵ Send  · Shift+↵ New line   │ 4 messages      │
│ ● connected  │                                │ ~1,240 tokens   │
└──────────────┴────────────────────────────────┴─────────────────┘
```

## Roadmap

- [x] Step 1: Core architecture + PySide6 shell
- [x] Step 2: Dark theme (Linear/Claude inspired)  
- [x] Step 3: Left sidebar with nav + model selector
- [x] Step 4: Claude-style message blocks with code highlighting
- [x] Step 5: Ollama streaming integration
- [x] Step 6: Agent state machine (thinking/coding/executing)
- [x] Step 7: Right context panel (system stats, file tree, memory)
- [x] Step 8: Embedded terminal panel
- [ ] Step 9: File explorer with project loading
- [ ] Step 10: Code editor (QScintilla or Monaco via WebView)
- [ ] Step 11: Agent tool use (read files, run commands)
- [ ] Step 12: Conversation persistence (SQLite)
- [ ] Step 13: Semantic search over codebase
- [ ] Step 14: Plugin system

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Enter` | Send message |
| `Shift+Enter` | New line in input |
| `⌨` button | Toggle terminal panel |
| `📎` button | Attach file (coming soon) |
