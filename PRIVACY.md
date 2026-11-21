# MAX AI — Privacy Policy
**LEREON Technologies — MAX AI © 2026 LEREON Technologies. All rights reserved.**
**Last updated: 2026**

---

## Summary

MAX AI is a local desktop application. Your conversations, files, and API keys stay on your computer. LEREON Technologies does not collect, store, or process your personal data.

---

## What MAX AI Stores Locally

| Data | Where | Purpose | You Control It |
|------|-------|---------|----------------|
| Conversation history | `memory/max.db` | Context for AI responses | ✅ Clear any time |
| Knowledge documents | `memory/knowledge.db` | Reference for AI answers | ✅ Delete any time |
| Preferences | `config/config.json` | Your settings | ✅ Edit any time |
| API keys | OS Keyring / `.keystore` | Provider authentication | ✅ Delete any time |
| Logs | `logs/max.log` | Debugging | ✅ Delete any time |
| Productivity data | `memory/productivity.db` | Todos, notes, reminders | ✅ Delete any time |

---

## What is Sent to External Services

When you send a message in MAX AI, your message is sent to the AI provider you have configured (OpenAI, Anthropic, etc.) via their API. This is necessary for MAX AI to function.

**What is sent:**
- Your message text.
- Recent conversation history (for context).
- Any documents you explicitly share in the conversation.
- The AI's system prompt (personality instructions).

**What is NOT sent:**
- Your API key content (only used as an authentication header).
- Your local files (unless you explicitly ask MAX AI to read and discuss them).
- Your computer's system information (unless you run the system info tool).
- Your name or identity (MAX AI has no account system).

Each AI provider has its own privacy policy:
- OpenAI: https://openai.com/policies/privacy-policy
- Anthropic: https://www.anthropic.com/privacy
- Google: https://policies.google.com/privacy
- Groq: https://groq.com/privacy-policy/

---

## What LEREON Technologies Does NOT Collect

LEREON Technologies does **not**:

- Collect your conversations.
- Collect your API keys.
- Collect your files or documents.
- Collect your name, email, or identity.
- Track your usage of MAX AI.
- Send telemetry or analytics from the application.
- Require you to create a LEREON account.
- Synchronize your data to LEREON servers.

---

## Microphone and Camera

Microphone and camera access are **off by default**.

If you enable the microphone: audio is processed locally by SpeechRecognition or Whisper. Audio is not recorded or stored permanently.

If you enable the camera: camera frames are processed locally for gesture recognition. Camera images are not stored unless you explicitly take a screenshot.

---

## Children's Privacy

MAX AI is not designed for or directed at children under 13. We do not knowingly collect data from children.

---

## Changes to This Policy

If this policy changes materially, the updated version will be distributed with the next MAX AI release and noted in CHANGELOG.md.

---

## Contact

**LEREON Technologies**
Website: https://lereontech.netlify.app
