#!/usr/bin/env python3
"""
MAX AI — Setup & Installation Wizard v2
LEREON Technologies
"""
import sys, os, subprocess, json
from pathlib import Path

ROOT = Path(__file__).parent

REQUIRED = [
    "PyQt6>=6.5.0","openai>=1.0.0","anthropic>=0.20.0",
    "google-generativeai","groq","mistralai","aiohttp>=3.9.0",
    "requests>=2.31.0","Pillow>=10.0.0","mss>=9.0.0","psutil>=5.9.0",
    "pyperclip>=1.8.0","beautifulsoup4>=4.12.0","lxml>=4.9.0",
    "PyPDF2>=3.0.0","python-docx>=1.1.0","cryptography>=41.0.0",
    "rich>=13.0.0","pydantic>=2.0.0",
]

OPTIONAL = {
    "SpeechRecognition":"Voice input (STT)",
    "pyttsx3":"Voice output (TTS)",
    "pyaudio":"Microphone (may need system libportaudio)",
    "openai-whisper":"Local Whisper STT (~1 GB)",
    "pvporcupine":"Wake word (needs Picovoice key)",
    "opencv-python":"Camera / vision / gesture",
    "mediapipe":"Hand gesture recognition",
    "pytesseract":"OCR text extraction",
    "openpyxl":"Excel reading",
    "pyautogui":"PC keyboard/mouse control",
}

def banner():
    print("\n"+"="*60)
    print("  MAX AI — Modular Autonomous eXecutive")
    print("  Setup Wizard  |  LEREON Technologies")
    print("="*60+"\n")

def check_python():
    v = sys.version_info
    if (v.major, v.minor) < (3,10):
        print(f"Python 3.10+ required. You have {v.major}.{v.minor}")
        sys.exit(1)
    print(f"Python {v.major}.{v.minor}.{v.micro} OK")

def pip_install(pkg):
    r = subprocess.run([sys.executable,"-m","pip","install",pkg,"-q"],
                       capture_output=True, text=True)
    return r.returncode == 0

def install_required():
    print("\nInstalling required packages...")
    for pkg in REQUIRED:
        name = pkg.split(">=")[0].split(">")[0].split("=")[0]
        ok = pip_install(pkg)
        print(f"  {'OK' if ok else 'FAIL'}  {name}")

def install_optional():
    print("\nOptional packages (Enter to skip):")
    for pkg, desc in OPTIONAL.items():
        ans = input(f"  Install {pkg}? ({desc}) [y/N]: ").strip().lower()
        if ans == "y":
            ok = pip_install(pkg)
            print(f"  {'OK' if ok else 'FAIL'}  {pkg}")

def create_dirs():
    for d in ["config","logs","memory","uploads","exports","tasks","plugins/installed","knowledge"]:
        (ROOT/d).mkdir(parents=True, exist_ok=True)
    print("Directories created.")

def create_config():
    cfg_file = ROOT/"config"/"config.json"
    if cfg_file.exists():
        print("config.json already exists - skipping.")
        return
    cfg = {
        "version":"2.0.0",
        "branding":{"product_name":"MAX AI","developer":"LEREON Technologies",
                    "copyright":"MAX AI 2026 LEREON Technologies. All rights reserved."},
        "assistant":{"name":"MAX","full_name":"Modular Autonomous eXecutive",
                     "wake_word":"hey max","wake_word_enabled":False,
                     "voice_input_enabled":False,"voice_output_enabled":False,"language":"en-US"},
        "personality":{"mode":"sarcastic","sarcasm_level":60,"enable_jokes":True,
                       "enable_roasting":True,"force_serious":False},
        "providers":{"default":"","fallback_order":["openai","anthropic","gemini","groq","deepseek","mistral","openrouter","ollama"],
                     "openai":{"enabled":False,"api_key":"","model":"gpt-4o"},
                     "anthropic":{"enabled":False,"api_key":"","model":"claude-opus-4-5"},
                     "gemini":{"enabled":False,"api_key":"","model":"gemini-1.5-pro"},
                     "groq":{"enabled":False,"api_key":"","model":"llama3-70b-8192"},
                     "deepseek":{"enabled":False,"api_key":"","model":"deepseek-chat"},
                     "mistral":{"enabled":False,"api_key":"","model":"mistral-large-latest"},
                     "openrouter":{"enabled":False,"api_key":"","model":"openai/gpt-4o"},
                     "ollama":{"enabled":False,"base_url":"http://localhost:11434","model":"llama3"}},
        "permissions":{"web_browsing":True,"file_read":True,"file_write":False,
                       "screen_capture":True,"pc_control":False,"microphone":False,
                       "camera":False,"notifications":True,"automation":False,"memory":True},
        "memory":{"enabled":True,"max_history":50},
        "ui":{"theme":"dark","accent":"#00BFFF","animation_speed":1.0},
        "tasks":{"max_concurrent":5,"default_timeout":60,"max_retries":3},
        "logging":{"level":"INFO"}
    }
    with open(cfg_file,"w") as f:
        json.dump(cfg, f, indent=2)
    print("config/config.json created.")

def create_env_template():
    tpl = ROOT/".env.template"
    if not tpl.exists():
        tpl.write_text(
            "# MAX AI API Keys - LEREON Technologies\n"
            "# Copy to .env and fill in your keys.\n\n"
            "OPENAI_API_KEY=\nANTHROPIC_API_KEY=\nGOOGLE_API_KEY=\n"
            "GROQ_API_KEY=\nDEEPSEEK_API_KEY=\nMISTRAL_API_KEY=\n"
            "OPENROUTER_API_KEY=\nOLLAMA_BASE_URL=http://localhost:11434\n"
            "PICOVOICE_ACCESS_KEY=\n"
        )
        print(".env.template created.")

def create_gitignore():
    gi = ROOT/".gitignore"
    gi.write_text(".env\n__pycache__/\n*.pyc\nlogs/\nmemory/\nuploads/\nexports/\n.venv/\nvenv/\n")
    print(".gitignore created.")

def collect_api_keys():
    print("\nAPI Key Setup (press Enter to skip any):")
    providers = [
        ("OPENAI_API_KEY","OpenAI (GPT-4o)"),("ANTHROPIC_API_KEY","Anthropic (Claude)"),
        ("GOOGLE_API_KEY","Google Gemini"),("GROQ_API_KEY","Groq"),
        ("DEEPSEEK_API_KEY","DeepSeek"),("MISTRAL_API_KEY","Mistral"),
        ("OPENROUTER_API_KEY","OpenRouter"),
    ]
    keys = {}
    for ek, label in providers:
        v = input(f"  {label}: ").strip()
        if v: keys[ek] = v
    if not keys:
        print("No keys entered. Add them to .env or via Settings later.")
        return
    env_path = ROOT/".env"
    existing = {}
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k,_,v = line.partition("=")
                existing[k.strip()] = v.strip()
    existing.update(keys)
    with open(env_path,"w") as f:
        for k,v in existing.items():
            if v: f.write(f"{k}={v}\n")
    print(f"{len(keys)} key(s) saved to .env")
    cfg_file = ROOT/"config"/"config.json"
    if not cfg_file.exists(): return
    with open(cfg_file) as f: cfg = json.load(f)
    em = {"OPENAI_API_KEY":"openai","ANTHROPIC_API_KEY":"anthropic","GOOGLE_API_KEY":"gemini",
          "GROQ_API_KEY":"groq","DEEPSEEK_API_KEY":"deepseek","MISTRAL_API_KEY":"mistral",
          "OPENROUTER_API_KEY":"openrouter"}
    first = None
    for ek,pn in em.items():
        if ek in keys:
            cfg["providers"][pn]["enabled"] = True
            if not first: first = pn
    if first and not cfg["providers"]["default"]:
        cfg["providers"]["default"] = first
    with open(cfg_file,"w") as f: json.dump(cfg,f,indent=2)
    print(f"Config updated. Default provider: {first}")

def smoke_test():
    print("\nSmoke test...")
    sys.path.insert(0, str(ROOT))
    tests = [("PyQt6.QtWidgets","PyQt6"),("openai","OpenAI"),("anthropic","Anthropic"),
             ("aiohttp","aiohttp"),("PIL","Pillow"),("psutil","psutil")]
    for mod, name in tests:
        try:
            __import__(mod)
            print(f"  OK  {name}")
        except ImportError:
            print(f"  MISSING  {name}")

def main():
    banner()
    check_python()
    install_required()
    ans = input("\nInstall optional packages? [y/N]: ").strip().lower()
    if ans == "y": install_optional()
    create_dirs()
    create_config()
    create_env_template()
    create_gitignore()
    ans = input("\nSet up API keys now? [Y/n]: ").strip().lower()
    if ans != "n": collect_api_keys()
    smoke_test()
    print("\n"+"="*60)
    print("  MAX AI Setup Complete — LEREON Technologies")
    print("  Launch:   python main.py")
    print("  CLI:      python main.py --cli")
    print("  Diagnose: python main.py --diagnose")
    print("  Tests:    python -m pytest tests/ -v")
    print("="*60+"\n")

if __name__ == "__main__":
    main()
