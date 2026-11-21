# MAX AI — Troubleshooting Guide
**LEREON Technologies — MAX AI © 2026 LEREON Technologies. All rights reserved.**

---

## Run Diagnostics First

```bash
python main.py --diagnose
```

This performs a 7-category health check and reports exactly what is working and what needs fixing.

---

## Common Problems

### "No AI providers available"

**Cause:** No API key has been configured.

**Fix:**
1. Open Settings → Open Full Settings Dialog → API Keys.
2. Add at least one API key.
3. Click Save — MAX AI will reload providers automatically.

Or edit `.env` and restart MAX AI.

---

### MAX AI won't start / blank window

**On Linux:**
```bash
export QT_QPA_PLATFORM=xcb
python main.py
```

**Missing PyQt6:**
```bash
pip install PyQt6
```

**Still failing:**
```bash
python main.py --debug
# Check logs/max.log for the error
```

---

### "No module named X"

```bash
pip install -r requirements.txt
```

If that fails for a specific package, try:
```bash
pip install --upgrade pip setuptools wheel
pip install <package_name>
```

---

### Voice input not working

1. Enable **Microphone** in Settings → Permissions.
2. Verify pyaudio is installed:
   ```bash
   python -c "import pyaudio; print('OK')"
   ```
3. If not:
   - **Windows:** `pip install pyaudio` or `pip install pipwin && pipwin install pyaudio`
   - **macOS:** `brew install portaudio && pip install pyaudio`
   - **Ubuntu:** `sudo apt-get install portaudio19-dev && pip install pyaudio`
4. Test microphone in your OS settings.

---

### pyaudio installation fails

**macOS:**
```bash
brew install portaudio
pip install pyaudio
```

**Ubuntu/Debian:**
```bash
sudo apt-get install python3-dev portaudio19-dev
pip install pyaudio
```

**Windows:** Try PyInstaller-packaged version which includes pyaudio.

---

### Screenshots not working

1. Enable **Screen Capture** in Settings → Permissions.
2. Install mss: `pip install mss`
3. On macOS: grant Screen Recording permission in System Settings → Privacy & Security → Screen Recording.

---

### Provider error: 401 Unauthorized

Your API key is invalid or expired.

1. Log in to your provider's dashboard.
2. Generate a new API key.
3. Update in MAX AI Settings.
4. Revoke the old key.

---

### Provider error: 429 Rate Limited

You've exceeded your provider's rate limit.

- Wait a few minutes and try again.
- Upgrade your account tier for higher limits.
- Switch to a different provider temporarily.

---

### Ollama not connecting

1. Verify Ollama is running: `ollama serve`
2. Verify a model is downloaded: `ollama pull llama3`
3. Test the endpoint: `curl http://localhost:11434/api/tags`
4. Check MAX AI Settings → Ollama → Base URL is `http://localhost:11434`

---

### Memory/database errors

```bash
# Check database integrity
python -c "
import sqlite3
conn = sqlite3.connect('memory/max.db')
result = conn.execute('PRAGMA integrity_check').fetchone()
print('DB integrity:', result[0])
conn.close()
"
```

If corrupted, rename `memory/max.db` to create a fresh one (conversations will be lost).

---

### Settings not saving

Check write permissions:
```bash
ls -la config/config.json     # Linux/macOS
```

If read-only, fix with:
```bash
chmod 644 config/config.json  # Linux/macOS
```

---

### High CPU usage

The system monitor runs every 2.5 seconds. The animated sphere runs at 60fps.

To reduce CPU:
1. In `config/config.json`, the monitor interval can be increased.
2. The sphere animation uses minimal CPU — it draws only simple geometry.

On slow machines (Intel i3, 4GB RAM), MAX AI is specifically optimized to use lazy loading and async operations so the UI stays responsive.

---

### "Setup wizard not appearing"

Force it:
```bash
python main.py --setup
```

Or reset setup state:
```python
# In Python:
import json
cfg = json.load(open('config/config.json'))
cfg.get('app', {}).pop('setup_complete', None)
json.dump(cfg, open('config/config.json','w'), indent=2)
```

---

## Getting More Help

1. Run `python main.py --diagnose` and check the output.
2. Check `logs/max.log` for detailed error messages.
3. Run `python main.py --debug` for verbose logging.
4. Visit https://lereontech.netlify.app for support.
