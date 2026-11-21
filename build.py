#!/usr/bin/env python3
"""
MAX AI — Build Script
LEREON Technologies

Produces native installers for Windows, macOS, and Linux using PyInstaller.

Usage:
  python build.py                   # Auto-detect current platform
  python build.py --platform windows
  python build.py --platform macos
  python build.py --platform linux
  python build.py --clean           # Clean dist/ and build/ first
"""

import sys
import os
import shutil
import argparse
import subprocess
from pathlib import Path

ROOT    = Path(__file__).parent
DIST    = ROOT / "dist"
BUILD   = ROOT / "build"
VERSION = os.environ.get("BUILD_VERSION", "2.0.0").lstrip("v")


def clean():
    for d in [DIST, BUILD]:
        if d.exists():
            shutil.rmtree(d)
            print(f"Cleaned: {d}")


def run(cmd: list, **kwargs):
    print(f"$ {' '.join(str(c) for c in cmd)}")
    result = subprocess.run(cmd, **kwargs)
    if result.returncode != 0:
        print(f"Command failed with exit code {result.returncode}")
        sys.exit(result.returncode)


def _base_pyinstaller_args(platform: str) -> list:
    args = [
        sys.executable, "-m", "PyInstaller",
        "--name", "MAX AI",
        "--clean",
        "--noconfirm",
        "--onefile",
        "--windowed",
        # Collect all subpackages
        "--collect-all", "openai",
        "--collect-all", "anthropic",
        "--collect-all", "aiohttp",
        # Hidden imports
        "--hidden-import", "PyQt6.sip",
        "--hidden-import", "PyQt6.QtCore",
        "--hidden-import", "PyQt6.QtGui",
        "--hidden-import", "PyQt6.QtWidgets",
        "--hidden-import", "sqlite3",
        "--hidden-import", "cryptography",
        # Add data files
        "--add-data", f"config{os.pathsep}config",
        "--add-data", f"plugins{os.pathsep}plugins",
        # Exclude heavy unused packages
        "--exclude-module", "torch",
        "--exclude-module", "tensorflow",
        "--exclude-module", "cv2",
        "--exclude-module", "mediapipe",
        "main.py",
    ]
    return args


def build_windows():
    print("\n── Building Windows installer ──────────────────────────")
    args = _base_pyinstaller_args("windows")
    args += [
        "--icon", str(ROOT / "assets" / "max_icon.ico")
        if (ROOT / "assets" / "max_icon.ico").exists() else "",
        "--version-file", _write_windows_version_file(),
    ]
    args = [a for a in args if a]  # remove empty strings
    run(args)

    exe = DIST / "MAX AI.exe"
    if not exe.exists():
        print("ERROR: Windows build failed — exe not found")
        sys.exit(1)

    # Rename to MAXSetup.exe
    final = DIST / "MAXSetup.exe"
    exe.rename(final)
    print(f"\n✅ Windows build complete: {final}")
    print(f"   Size: {final.stat().st_size:,} bytes")


def _write_windows_version_file() -> str:
    path = BUILD / "version_info.txt"
    path.parent.mkdir(exist_ok=True)
    major, minor, patch = (VERSION + ".0.0").split(".")[:3]
    content = f"""
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({major}, {minor}, {patch}, 0),
    prodvers=({major}, {minor}, {patch}, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(u'040904B0', [
        StringStruct(u'CompanyName', u'LEREON Technologies'),
        StringStruct(u'FileDescription', u'MAX AI — Modular Autonomous eXecutive'),
        StringStruct(u'FileVersion', u'{VERSION}'),
        StringStruct(u'InternalName', u'MAX AI'),
        StringStruct(u'LegalCopyright', u'MAX AI 2026 LEREON Technologies. All rights reserved.'),
        StringStruct(u'OriginalFilename', u'MAXSetup.exe'),
        StringStruct(u'ProductName', u'MAX AI'),
        StringStruct(u'ProductVersion', u'{VERSION}'),
      ])
    ]),
    VarFileInfo([VarStruct(u'Translation', [0x0409, 1200])])
  ]
)
"""
    path.write_text(content)
    return str(path)


def build_macos():
    print("\n── Building macOS DMG ──────────────────────────────────")
    args = _base_pyinstaller_args("macos")
    args += [
        "--target-arch", "universal2",  # Intel + Apple Silicon
    ]
    # Remove --onefile for macOS (use bundle)
    if "--onefile" in args:
        args.remove("--onefile")
    args.insert(args.index("main.py"), "--onedir")

    run(args)

    app = DIST / "MAX AI.app"
    if not app.exists():
        print("ERROR: macOS app bundle not found")
        sys.exit(1)

    # Create DMG
    dmg = DIST / "MAX AI.dmg"
    run(["hdiutil", "create",
         "-volname", "MAX AI",
         "-srcfolder", str(app),
         "-ov", "-format", "UDZO",
         str(dmg)])

    if dmg.exists():
        print(f"\n✅ macOS build complete: {dmg}")
        print(f"   Size: {dmg.stat().st_size:,} bytes")
        print("   NOTE: For public distribution, sign with: codesign --deep --sign 'Developer ID'")
        print("   And notarize with: xcrun notarytool submit MAX\\ AI.dmg --apple-id ...")
    else:
        print("ERROR: DMG creation failed")
        sys.exit(1)


def build_linux():
    print("\n── Building Linux AppImage ─────────────────────────────")
    args = _base_pyinstaller_args("linux")
    run(args)

    exe = DIST / "MAX AI"
    if not exe.exists():
        print("ERROR: Linux binary not found")
        sys.exit(1)

    # Attempt AppImage creation if appimagetool is available
    appimage_tool = shutil.which("appimagetool")
    if appimage_tool:
        appdir = DIST / "MAX_AI.AppDir"
        appdir.mkdir(exist_ok=True)
        (appdir / "usr" / "bin").mkdir(parents=True, exist_ok=True)
        shutil.copy(exe, appdir / "usr" / "bin" / "max-ai")

        # Desktop entry
        (appdir / "max-ai.desktop").write_text(
            "[Desktop Entry]\n"
            "Name=MAX AI\n"
            "Comment=Modular Autonomous eXecutive\n"
            "Exec=max-ai\n"
            "Icon=max-ai\n"
            "Type=Application\n"
            "Categories=Utility;AI;\n"
        )
        # AppRun
        apprun = appdir / "AppRun"
        apprun.write_text("#!/bin/sh\nexec \"$(dirname \"$0\")/usr/bin/max-ai\" \"$@\"\n")
        apprun.chmod(0o755)

        appimage = DIST / "MAX_AI.AppImage"
        run([appimage_tool, str(appdir), str(appimage)])
        if appimage.exists():
            print(f"\n✅ Linux AppImage complete: {appimage}")
        else:
            print("appimagetool failed — distributing raw binary instead")
    else:
        # Rename to AppImage convention even without tool
        final = DIST / "MAX_AI.AppImage"
        exe.rename(final)
        final.chmod(0o755)
        print(f"\n✅ Linux build complete: {final}")
        print("   NOTE: For true AppImage, install appimagetool and re-run")

    # Also build .deb if on Debian/Ubuntu
    if shutil.which("dpkg-deb"):
        _build_deb()


def _build_deb():
    """Build a .deb package (Debian/Ubuntu)."""
    print("Building .deb package…")
    pkg_dir = BUILD / "max-ai_deb"
    bin_dir = pkg_dir / "usr" / "bin"
    desktop_dir = pkg_dir / "usr" / "share" / "applications"
    control_dir = pkg_dir / "DEBIAN"
    for d in [bin_dir, desktop_dir, control_dir]:
        d.mkdir(parents=True, exist_ok=True)

    shutil.copy(DIST / "MAX_AI.AppImage", bin_dir / "max-ai")
    (bin_dir / "max-ai").chmod(0o755)

    (desktop_dir / "max-ai.desktop").write_text(
        "[Desktop Entry]\nName=MAX AI\nExec=/usr/bin/max-ai\n"
        "Icon=utilities-terminal\nType=Application\nCategories=Utility;\n"
    )
    (control_dir / "control").write_text(
        f"Package: max-ai\nVersion: {VERSION}\nSection: utils\n"
        "Priority: optional\nArchitecture: amd64\nMaintainer: LEREON Technologies\n"
        "Description: MAX AI — Modular Autonomous eXecutive\n"
        " Intelligent personal AI assistant by LEREON Technologies.\n"
    )
    deb_path = DIST / f"max-ai_{VERSION}_amd64.deb"
    run(["dpkg-deb", "--build", str(pkg_dir), str(deb_path)])
    if deb_path.exists():
        print(f"✅ .deb package: {deb_path}")


def auto_detect_platform() -> str:
    if sys.platform == "win32":
        return "windows"
    if sys.platform == "darwin":
        return "macos"
    return "linux"


def main():
    parser = argparse.ArgumentParser(description="MAX AI Build Script — LEREON Technologies")
    parser.add_argument("--platform", choices=["windows", "macos", "linux"],
                        default=auto_detect_platform())
    parser.add_argument("--clean", action="store_true")
    args = parser.parse_args()

    print(f"\n{'='*55}")
    print(f"  MAX AI v{VERSION} — Build Script")
    print(f"  LEREON Technologies")
    print(f"  Platform: {args.platform}")
    print(f"{'='*55}\n")

    # Verify PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller not found. Install with: pip install pyinstaller")
        sys.exit(1)

    if args.clean:
        clean()

    DIST.mkdir(exist_ok=True)
    BUILD.mkdir(exist_ok=True)

    builders = {
        "windows": build_windows,
        "macos":   build_macos,
        "linux":   build_linux,
    }
    builders[args.platform]()

    print(f"\n{'='*55}")
    print(f"  Build complete.")
    print(f"  Output: {DIST}/")
    print(f"  MAX AI © 2026 LEREON Technologies.")
    print(f"{'='*55}\n")


if __name__ == "__main__":
    main()
