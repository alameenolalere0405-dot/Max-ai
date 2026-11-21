# MAX AI — User Guide
**LEREON Technologies — MAX AI © 2026 LEREON Technologies. All rights reserved.**

---

## Interface Overview

MAX AI has a clean, minimal layout. Everything is accessible from the icon navigation rail on the left.

```
┌──┬────────────────────────────────────────────┐
│  │  Chat Header (title, provider, clock)      │
│  ├──────────────┬─────────────────────────────┤
│ 💬│  Sphere +   │                             │
│ 🛠│  Conv List  │      Chat Area              │
│ 🧠│             │                             │
│ ⚙│  Provider   │                             │
│  │  selector   │      Input Bar              │
└──┴──────────────┴─────────────────────────────┘
```

**Navigation Rail (left edge):**
- 💬 **Chat** — main conversation interface
- 🛠 **Tools** — Studio, Automation, Monitor, Plugins, Desktop
- 🧠 **Memory** — History, Knowledge Base, Productivity
- ⚙ **Settings** — providers, permissions, personality

---

## Having a Conversation

1. Click **💬 Chat** in the nav rail.
2. Type your message in the input bar at the bottom.
3. Press **Enter** to send (Shift+Enter for a new line).
4. MAX AI responds. The animated sphere changes color to show its state.

**Sphere states:**
| Color | Meaning |
|-------|---------|
| Cyan/Blue | Idle — ready |
| Green | Listening (voice) |
| Purple | Thinking / processing |
| Orange | Executing a task |
| Teal | Searching the web |
| Red | Error |

---

## Starting a New Conversation

Click **✚ New Chat** above the conversation list in the left panel.
Previous conversations appear in the list below — click any to revisit it.

---

## Switching AI Providers

Use the **Provider** dropdown in the bottom-left panel under the conversation list.
"Auto" selects the best available provider.

To add a new provider, go to **Settings** (⚙) → **Open Full Settings Dialog** → **API Keys**.

---

## Voice Input

1. Enable **Microphone** in Settings → Permissions.
2. Click the **🎤** button in the bottom of the nav rail.
3. Speak your message.
4. MAX AI transcribes and responds.

For wake word ("Hey MAX"), you need a free Picovoice API key — see [API_SETUP.md](API_SETUP.md).

---

## MAX Studio

Go to **🛠 Tools → Studio**.

**Task types:**
| Task | What it does |
|------|-------------|
| Summarize | Condenses long text |
| Code Review | Finds bugs and improvements |
| Write Docs | Generates documentation |
| README | Creates a README.md |
| Explain | Explains code or concepts |
| Refactor | Rewrites code more cleanly |
| Unit Tests | Generates test cases |
| Report | Structured report from data |
| Email Draft | Drafts a professional email |
| Meeting Summary | Extracts action items |
| Custom | Your own instruction |

**To use:** Paste text or load a file → select task → click **▶ Run** → save output with **💾**.

---

## Knowledge Base

Go to **🧠 Memory → Knowledge Base**.

Import documents (PDF, DOCX, TXT, MD, Python, JSON, CSV) that MAX can reference when answering questions. When you ask about a topic, MAX searches your knowledge base and includes relevant context automatically.

- Click **📂 Import Document** to add files.
- Use the search bar to find content across all documents.
- Right-click any document to delete it.

---

## Productivity

Go to **🧠 Memory → Productivity**.

**Todos:** Add tasks with priorities. Double-click to mark complete.

**Notes:** Save notes with a title and content. Searchable.

**Reminders:** Set a future time — MAX shows a dialog when the time arrives.

---

## Automation Workflows

Go to **🛠 Tools → Automate**.

Create workflows that run automatically:
- **Manual** — run on demand
- **Schedule** — daily at a specific time
- **Keyword** — fires when your chat contains a keyword
- **Startup** — runs once when MAX starts

Actions include: send a message, open an app, clipboard copy, system info, speak, wait.

> All sensitive actions require your confirmation. No arbitrary shell commands are ever executed.

---

## System Monitor

Go to **🛠 Tools → Monitor**.

Shows real-time CPU, RAM, disk, battery, and network stats. Updates every 2.5 seconds. The top processes list shows what's using your CPU.

---

## Multi-Model Collaboration

Click **🤝 Collaborate** in the chat header.

Select 2–4 AI providers. Each contributes in sequence:
1. First model **researches** the topic.
2. Second model **analyzes** the research.
3. Third model **reviews** the analysis.
4. Final model **synthesizes** everything.

Results are shown per-model so you can see each contribution.

---

## Personality Modes

Go to **⚙ Settings** and find the Personality section.

| Mode | Style |
|------|-------|
| Sarcastic (default) | Witty, dry humor, still helpful |
| Professional | Polished, precise, no jokes |
| Friendly | Warm, encouraging |
| Nerdy | Technical enthusiasm, programming references |
| Creative | Imaginative, expressive |
| Savage | Blunt, brutally honest |

The **Sarcasm** slider (0–100) controls humor intensity. Set to 0 for no humor at all.

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+N` | New conversation |
| `Ctrl+,` | Settings |
| `Ctrl+Q` | Quit |
| `Enter` | Send message |
| `Shift+Enter` | New line in message |

---

## Tips

- Ask MAX to **search the web** for current information: "Search for the latest Python 3.13 features."
- Ask MAX to **read a file**: "Read and summarize this document" then load it in Studio.
- Use **natural language** for desktop control: "Open my browser", "Take a screenshot."
- Ask MAX for a **calculation**: "What is 15% of 847?"
- Ask MAX for **system info**: "How much RAM am I using?"
- Use the **knowledge base** for private docs: import your notes, then ask questions about them.
