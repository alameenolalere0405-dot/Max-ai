# MAX AI — Release Guide
**LEREON Technologies — MAX AI © 2026 LEREON Technologies. All rights reserved.**

---

## Release Checklist

Before tagging a release, complete every item:

### Code Quality
- [ ] `python tests/test_max.py` — all tests pass (currently 124/124)
- [ ] `python -c "import ast,os; [ast.parse(open(p).read()) for r,d,f in os.walk('.') for p in [os.path.join(r,n)] if n.endswith('.py') and '__pycache__' not in p]"` — zero syntax errors
- [ ] No hardcoded API keys: `grep -r "sk-[a-zA-Z0-9]\{20,\}" --include="*.py" .` returns nothing
- [ ] `config/config.json` has no API keys stored
- [ ] `.env` is in `.gitignore` and not committed

### Documentation
- [ ] `CHANGELOG.md` updated with all changes
- [ ] `README.md` version number updated
- [ ] New features documented in `USER_GUIDE.md`
- [ ] Known limitations listed below

### Build
- [ ] `python build.py --platform windows` succeeds on Windows runner
- [ ] `python build.py --platform macos` succeeds on macOS runner
- [ ] `python build.py --platform linux` succeeds on Ubuntu runner
- [ ] SHA-256 checksums generated for all artifacts
- [ ] Artifact file sizes are reasonable (< 200 MB each)

---

## Tagging a Release

```bash
git tag -a v2.0.0 -m "MAX AI v2.0.0 — LEREON Technologies"
git push origin v2.0.0
```

The GitHub Actions workflow (`ci.yml`) triggers automatically on a published release and builds all three platform artifacts.

---

## Publishing to lereontech.netlify.app

The product page will be at: `https://lereontech.netlify.app/products/max-ai`

Once release artifacts are built and checksums verified, update the website with:

1. **Version number** — update displayed version
2. **Download links** — link to GitHub Release assets:
   - `MAXSetup.exe` (Windows)
   - `MAX AI.dmg` (macOS)
   - `MAX_AI.AppImage` (Linux)
3. **Checksums** — publish SHA-256 hashes alongside downloads
4. **Release notes** — copy from `CHANGELOG.md`
5. **System requirements** — from `INSTALLATION.md`

**Do not publish download links until artifacts are verified** — run each installer on a clean machine before linking.

---

## Code Signing (Future)

For public distribution without OS security warnings:

**Windows:**
```bash
# Sign with EV certificate
signtool sign /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 /a MAXSetup.exe
```

**macOS:**
```bash
# Sign
codesign --deep --force --verify --verbose \
  --sign "Developer ID Application: LEREON Technologies" \
  "MAX AI.app"

# Notarize
xcrun notarytool submit "MAX AI.dmg" \
  --apple-id "your@apple.id" \
  --team-id "YOUR_TEAM_ID" \
  --password "@keychain:notarytool-password" \
  --wait

# Staple
xcrun stapler staple "MAX AI.dmg"
```

**Linux:** AppImage signing with GPG:
```bash
gpg --armor --detach-sign MAX_AI.AppImage
```

---

## Version Numbering

MAX AI follows semantic versioning: `MAJOR.MINOR.PATCH`

- **MAJOR** — breaking changes or complete redesigns
- **MINOR** — new features, backward compatible
- **PATCH** — bug fixes, security fixes

Current version: `2.0.0`

---

## Known Limitations (v2.0.0)

| Limitation | Workaround |
|------------|------------|
| Native installers require separate build machines per OS | Use GitHub Actions with native runners |
| Wake word detection requires paid Picovoice key for custom keywords | Free key available at picovoice.ai |
| Gesture control requires opencv + mediapipe (heavy install) | Optional — not in default requirements |
| Local Whisper STT requires torch (~1 GB) | Optional — Google STT works without it |
| Multi-conversation switching (full history per conversation) | Planned for v2.1.0 |
| Cloud sync / backup | Planned for future release |
| Mobile companion app | Planned for future release |
| macOS code signing requires paid Apple Developer account ($99/year) | Distribute unsigned with Gatekeeper bypass instructions |
| Windows EV code signing certificate (~$300/year) | Distribute with SmartScreen warning until signed |

---

## Support

**Website:** https://lereontech.netlify.app
**MAX AI © 2026 LEREON Technologies. All rights reserved.**
