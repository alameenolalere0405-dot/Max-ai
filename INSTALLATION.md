# MAX AI — Installation Guide
**LEREON Technologies — MAX AI © 2026 LEREON Technologies. All rights reserved.**

---

## System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| OS | Windows 10 64-bit / macOS 12 / Ubuntu 20.04 | Windows 11 / macOS 14 / Ubuntu 22.04 |
| CPU | Intel Core i3 (any generation) | Intel Core i5 or better |
| RAM | 2 GB | 4 GB or more |
| Storage | 300 MB free | 1 GB free |
| Internet | Required for cloud AI providers | Broadband |
| Python | 3.10+ (source install only) | 3.11 |

MAX AI uses cloud AI providers by default. No local AI model download is required unless you choose Ollama.

---

## Option 1 — Windows Installer (Recommended)

1. Download `MAXSetup.exe` from the [LEREON Technologies website](https://lereontech.netlify.app/products/max-ai) or the GitHub Releases page.
2. Verify the SHA-256 checksum (see `MAXSetup.exe.sha256`).
3. Run `MAXSetup.exe` and follow the installer wizard.
4. Launch **MAX AI** from the Start Menu or desktop shortcut.
5. The first-launch setup wizard will guide you through API key configuration.

**No Python installation required.**

---

## Option 2 — macOS DMG

1. Download `MAX AI.dmg`.
2. Verify the SHA-256 checksum.
3. Open the DMG and drag **MAX AI** to your Applications folder.
4. First launch: right-click → Open (required on first run due to Gatekeeper).
5. The setup wizard will start automatically.

> **Note:** For public distribution builds, the app will be signed and notarized so Gatekeeper warnings do not appear.

---

## Option 3 — Linux AppImage

```bash
# Download MAX_AI.AppImage
wget https://lereontech.netlify.app/releases/MAX_AI.AppImage

# Verify checksum
sha256sum -c MAX_AI.AppImage.sha256

# Make executable
chmod +x MAX_AI.AppImage

# Run
./MAX_AI.AppImage
```

**Ubuntu/Debian — .deb package:**
```bash
sudo dpkg -i max-ai_2.0.0_amd64.deb
max-ai
```

---

## Option 4 — From Source (Developers)

```bash
# 1. Clone
git clone https://github.com/lereontech/max-ai.git
cd max-ai

# 2. Create virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
.venv\Scripts\activate           # Windows

# 3. Run setup wizard
python setup.py

# 4. Launch
python main.py
```

### macOS: pyaudio dependency
```bash
brew install portaudio
pip install pyaudio
```

### Ubuntu/Debian: pyaudio dependency
```bash
sudo apt-get install portaudio19-dev python3-pyaudio
```

### Windows: pyaudio
```bash
pip install pyaudio
# If that fails:
pip install pipwin && pipwin install pyaudio
```

---

## First-Launch Setup

When MAX AI starts for the first time, the setup wizard will:

1. Welcome you and explain MAX AI.
2. Ask you to choose an AI provider.
3. Walk you through getting and entering your API key.
4. Test the connection to verify the key works.
5. Let you set optional permissions (microphone, files, etc.).
6. Let you personalize the assistant name and personality.
7. Launch you into your first conversation.

You can skip any optional step and return to Settings later.

---

## Adding API Keys After Setup

Open **Settings** (⚙ icon or `Ctrl+,`) and click **Open Full Settings Dialog**, or edit your `.env` file:

```
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AIza...
GROQ_API_KEY=gsk_...
```

Restart MAX AI after editing `.env` manually.

---

## Updating MAX AI

**From installer:** Download and run the new installer. Your conversations and settings are preserved.

**From source:**
```bash
git pull
pip install -r requirements.txt
python main.py
```

---

## Uninstalling

**Windows:** Control Panel → Add/Remove Programs → MAX AI → Uninstall.
Your data in `%APPDATA%\MAX AI` is preserved unless you check "Remove user data".

**macOS:** Drag MAX AI from Applications to Trash. Data in `~/Library/Application Support/MAX AI` is preserved.

**Linux:** `sudo dpkg -r max-ai` or delete the AppImage. Data in `~/.config/MAX AI` is preserved.

---

## Troubleshooting Installation

| Problem | Solution |
|---------|----------|
| "Windows protected your PC" | Click "More info" → "Run anyway" (unsigned build) |
| macOS "unidentified developer" | Right-click → Open on first launch |
| AppImage won't run | `chmod +x MAX_AI.AppImage` |
| Black window on Linux | `export QT_QPA_PLATFORM=xcb` |
| "No module named PyQt6" | `pip install PyQt6` |
| Setup wizard doesn't appear | Run `python main.py --setup` |

See also: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
