# MAX AI — Security Documentation
**LEREON Technologies — MAX AI © 2026 LEREON Technologies. All rights reserved.**

---

## API Key Storage

API keys are sensitive credentials that allow MAX AI to access AI services on your behalf.

### Storage Priority

MAX AI uses the following priority order for storing secrets:

| Priority | Method | When Used |
|----------|--------|-----------|
| 1 | **OS Keyring** | Windows Credential Manager, macOS Keychain, Linux SecretService |
| 2 | **Fernet-encrypted file** | `config/.keystore` (AES-128, machine-specific key) |
| 3 | **Plaintext `.env` file** | Fallback when neither above is available |

Install `keyring` for OS-level protection: `pip install keyring`
Install `cryptography` for encrypted file storage: `pip install cryptography`

### What is NEVER Done With Your Keys

- API keys are **never** written to `config.json`.
- API keys are **never** written to log files.
- API keys are **never** included in crash reports.
- API keys are **never** sent to LEREON Technologies.
- API keys are **never** committed to source control (`.env` is in `.gitignore`).
- API keys are **never** exposed in screenshots or diagnostic output (they are masked).

### Key Rotation

To rotate an API key:
1. Generate a new key in your provider's dashboard.
2. Open MAX AI Settings → Full Settings Dialog → API Keys.
3. Paste the new key and save.
4. Revoke the old key in your provider's dashboard.

---

## Permissions Model

All sensitive permissions are **off by default**. Users must explicitly enable each one.

| Permission | Default | Risk Level | Notes |
|------------|---------|------------|-------|
| `web_browsing` | ✅ ON | Low | Read-only web access |
| `file_read` | ✅ ON | Low | Only reads files you share |
| `memory` | ✅ ON | Low | Local SQLite only |
| `microphone` | ❌ OFF | Medium | Required for voice input |
| `screen_capture` | ❌ OFF | Medium | Screenshots only |
| `file_write` | ❌ OFF | Medium | Creates new files only |
| `pc_control` | ❌ OFF | High | Requires confirmation per action |
| `camera` | ❌ OFF | High | Required for gestures |
| `automation` | ❌ OFF | High | Scheduled workflows |
| `notifications` | ❌ OFF | Low | System notifications |

---

## Desktop Automation Safety

MAX AI's desktop control features use a strict allowlist approach:

- Only **20 named, pre-approved applications** can be launched (Chrome, VSCode, Terminal, etc.).
- **No arbitrary shell commands** are ever executed.
- **No arbitrary file paths** are written to without user confirmation.
- Every launch and file-open operation calls a confirmation dialog before executing.
- The automation engine uses only pre-defined, typed action schemas.

---

## Network Security

- MAX AI only makes outbound HTTPS connections to configured AI providers.
- No data is sent to LEREON Technologies servers.
- No telemetry, analytics, or crash reporting sends user data externally.
- URL validation rejects private/local network targets in web tools.
- Provider API endpoints are hardcoded to official URLs — no redirects accepted.

---

## Local Data Storage

All user data is stored locally:

| Data | Location | Encrypted |
|------|----------|-----------|
| API keys | OS Keyring / `.keystore` | Yes |
| Conversations | `memory/max.db` | No (SQLite) |
| Knowledge docs | `memory/knowledge.db` | No |
| Config | `config/config.json` | No (no secrets) |
| Logs | `logs/max.log` | No |

Conversation data is never sent to LEREON Technologies. It is only sent to the AI provider you configure, as part of normal API usage.

---

## Threat Model

MAX AI is designed for a single-user local installation. It is **not** designed for:

- Multi-user shared systems (conversations are not user-isolated).
- Untrusted network environments without TLS.
- Storing government classified or medical HIPAA-covered data.

---

## Reporting Security Issues

To report a security vulnerability, contact LEREON Technologies privately:

**Website:** https://lereontech.netlify.app

Do not post security vulnerabilities as public GitHub issues.

---

## Dependency Security

- Dependencies are pinned in `requirements.txt`.
- The CI pipeline checks for hardcoded secrets before every build.
- PyInstaller builds exclude unused heavy packages (torch, tensorflow, cv2).
- Release artifacts include SHA-256 checksums for verification.
