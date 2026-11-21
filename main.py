#!/usr/bin/env python3
"""
MAX AI — Main Entry Point v2
LEREON Technologies
MAX AI 2026 LEREON Technologies. All rights reserved.
"""

import sys
import os
import argparse
import logging
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))


def parse_args():
    p = argparse.ArgumentParser(
        description="MAX AI — Modular Autonomous eXecutive | LEREON Technologies",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                       # Launch GUI (default)
  python main.py --setup               # Run first-time setup wizard
  python main.py --cli                 # Terminal / CLI mode
  python main.py --diagnose            # System diagnostics
  python main.py --provider anthropic  # Force a specific AI provider
  python main.py --voice               # Start with voice listening active
  python main.py --debug               # Verbose logging
  python main.py --test                # Run automated test suite
        """
    )
    p.add_argument("--setup",    action="store_true", help="Run setup wizard")
    p.add_argument("--cli",      action="store_true", help="Run in CLI mode (no GUI)")
    p.add_argument("--voice",    action="store_true", help="Start with voice active")
    p.add_argument("--diagnose", action="store_true", help="Run diagnostics and exit")
    p.add_argument("--test",     action="store_true", help="Run test suite and exit")
    p.add_argument("--debug",    action="store_true", help="Enable verbose debug logging")
    p.add_argument("--version",  action="store_true", help="Print version and exit")
    p.add_argument("--provider", default=None,
                   choices=["openai","anthropic","gemini","groq",
                            "deepseek","mistral","openrouter","ollama"],
                   help="Force a specific AI provider")
    return p.parse_args()


def setup_logging(debug: bool):
    level = logging.DEBUG if debug else logging.INFO
    log_dir = ROOT / "logs"
    log_dir.mkdir(exist_ok=True)
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_dir / "max.log", encoding="utf-8"),
        ]
    )


def ensure_config():
    """Create default config if missing."""
    cfg = ROOT / "config" / "config.json"
    if not cfg.exists():
        logging.warning("config.json missing — running setup...")
        import subprocess
        subprocess.run([sys.executable, str(ROOT / "setup.py")], check=False)
    return cfg.exists()


def run_gui(force_provider=None, start_voice=False, debug=False):
    try:
        from PyQt6.QtWidgets import QApplication
    except ImportError:
        print("PyQt6 not installed. Run:  python setup.py")
        print("Or use CLI mode:          python main.py --cli")
        sys.exit(1)

    os.environ.setdefault("QT_AUTO_SCREEN_SCALE_FACTOR", "1")

    app = QApplication(sys.argv)
    app.setApplicationName("MAX AI")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("LEREON Technologies")

    from ui.theme import apply_global_theme
    apply_global_theme(app)

    from ui.main_window import MainWindow
    win = MainWindow(
        force_provider=force_provider,
        start_voice=start_voice,
        debug=debug
    )
    win.show()

    logging.getLogger("MAX").info("MAX AI GUI launched — LEREON Technologies")
    sys.exit(app.exec())


def run_cli(force_provider=None, start_voice=False):
    from core.cli_mode import CLIMode
    cli = CLIMode(force_provider=force_provider, start_voice=start_voice)
    cli.run()


def run_tests():
    import unittest
    loader = unittest.TestLoader()
    suite = loader.discover(str(ROOT / "tests"), pattern="test_*.py")
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)


def main():
    args = parse_args()
    setup_logging(args.debug)
    log = logging.getLogger("MAX")

    if args.version:
        print("MAX AI v2.0.0 — LEREON Technologies")
        print("MAX AI 2026 LEREON Technologies. All rights reserved.")
        sys.exit(0)

    if args.setup:
        log.info("Running setup wizard...")
        import runpy
        runpy.run_path(str(ROOT / "setup.py"), run_name="__main__")
        sys.exit(0)

    if args.diagnose:
        from core.diagnostics import Diagnostics
        diag = Diagnostics()
        ok = diag.run_full_check()
        sys.exit(0 if ok else 1)

    if args.test:
        run_tests()

    # Ensure config exists
    if not ensure_config():
        print("Config missing and setup could not complete. Exiting.")
        sys.exit(1)

    log.info("=" * 55)
    log.info("MAX AI v2.0.0 — LEREON Technologies")
    log.info("=" * 55)

    if args.cli:
        run_cli(force_provider=args.provider, start_voice=args.voice)
    else:
        run_gui(
            force_provider=args.provider,
            start_voice=args.voice,
            debug=args.debug
        )


if __name__ == "__main__":
    main()
