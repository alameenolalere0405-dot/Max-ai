"""
MAX AI — Secure Storage
LEREON Technologies

API keys and secrets stored with OS-level protection:
  Priority 1: OS keyring (Windows Credential Manager / macOS Keychain / SecretService)
  Priority 2: Fernet-encrypted local file (cryptography package)
  Priority 3: Plaintext .env fallback (with clear warning to user)

Keys are NEVER written to config.json, logs, or crash reports.
"""

import os
import sys
import logging
import base64
import json
from pathlib import Path
from typing import Optional

logger = logging.getLogger("MAX.secure_storage")
ROOT = Path(__file__).parent.parent

SERVICE_NAME = "MAX_AI_LEREON"
_KEYRING_AVAILABLE = None
_FERNET_AVAILABLE = None


def _check_keyring() -> bool:
    global _KEYRING_AVAILABLE
    if _KEYRING_AVAILABLE is None:
        try:
            import keyring
            # Test it actually works (some Linux systems have keyring installed but no backend)
            keyring.get_password(SERVICE_NAME, "_test_")
            _KEYRING_AVAILABLE = True
        except Exception:
            _KEYRING_AVAILABLE = False
    return _KEYRING_AVAILABLE


def _check_fernet() -> bool:
    global _FERNET_AVAILABLE
    if _FERNET_AVAILABLE is None:
        try:
            from cryptography.fernet import Fernet
            _FERNET_AVAILABLE = True
        except ImportError:
            _FERNET_AVAILABLE = False
    return _FERNET_AVAILABLE


def _get_machine_key() -> bytes:
    """
    Derive a machine-specific encryption key from stable OS identifiers.
    Not perfect but far better than plaintext.
    """
    import hashlib
    seeds = []
    # Platform identifier
    seeds.append(sys.platform)
    # Username
    seeds.append(os.environ.get("USERNAME") or os.environ.get("USER") or "max_user")
    # Machine-specific path
    seeds.append(str(Path.home()))
    # App-specific salt
    seeds.append("LEREON_MAX_AI_2026")

    combined = "|".join(seeds).encode()
    digest = hashlib.sha256(combined).digest()
    return base64.urlsafe_b64encode(digest)


def _encrypted_file_path() -> Path:
    p = ROOT / "config" / ".keystore"
    p.parent.mkdir(exist_ok=True)
    return p


def _load_encrypted_store() -> dict:
    path = _encrypted_file_path()
    if not path.exists():
        return {}
    try:
        from cryptography.fernet import Fernet
        f = Fernet(_get_machine_key())
        raw = path.read_bytes()
        decrypted = f.decrypt(raw)
        return json.loads(decrypted.decode())
    except Exception as e:
        logger.warning(f"Could not read encrypted keystore: {e}")
        return {}


def _save_encrypted_store(store: dict):
    path = _encrypted_file_path()
    try:
        from cryptography.fernet import Fernet
        f = Fernet(_get_machine_key())
        encrypted = f.encrypt(json.dumps(store).encode())
        path.write_bytes(encrypted)
    except Exception as e:
        logger.error(f"Could not write encrypted keystore: {e}")


# ── Public API ────────────────────────────────────────────────────────────

def set_secret(key: str, value: str) -> str:
    """
    Store a secret. Returns the storage method used:
    'keyring', 'encrypted_file', or 'env_file'
    """
    if not value:
        return "skipped"

    # Try OS keyring first
    if _check_keyring():
        try:
            import keyring
            keyring.set_password(SERVICE_NAME, key, value)
            logger.info(f"Stored '{key}' in OS keyring")
            return "keyring"
        except Exception as e:
            logger.warning(f"Keyring write failed for '{key}': {e}")

    # Try Fernet-encrypted file
    if _check_fernet():
        try:
            store = _load_encrypted_store()
            store[key] = value
            _save_encrypted_store(store)
            logger.info(f"Stored '{key}' in encrypted file")
            return "encrypted_file"
        except Exception as e:
            logger.warning(f"Encrypted file write failed for '{key}': {e}")

    # Fallback: .env file (plaintext)
    logger.warning(
        f"Storing '{key}' in plaintext .env — "
        "install 'keyring' or 'cryptography' for secure storage"
    )
    _write_env_key(key, value)
    return "env_file"


def get_secret(key: str) -> Optional[str]:
    """
    Retrieve a secret. Checks all storage backends in priority order.
    Returns None if not found.
    """
    # 1. OS keyring
    if _check_keyring():
        try:
            import keyring
            val = keyring.get_password(SERVICE_NAME, key)
            if val:
                return val
        except Exception:
            pass

    # 2. Encrypted file
    if _check_fernet():
        try:
            store = _load_encrypted_store()
            val = store.get(key)
            if val:
                return val
        except Exception:
            pass

    # 3. Environment variable (set from .env on startup)
    val = os.environ.get(key, "").strip()
    if val:
        return val

    return None


def delete_secret(key: str) -> bool:
    """Delete a secret from all backends."""
    deleted = False
    if _check_keyring():
        try:
            import keyring
            keyring.delete_password(SERVICE_NAME, key)
            deleted = True
        except Exception:
            pass

    if _check_fernet():
        try:
            store = _load_encrypted_store()
            if key in store:
                del store[key]
                _save_encrypted_store(store)
                deleted = True
        except Exception:
            pass

    # Remove from .env
    _remove_env_key(key)
    deleted = True

    logger.info(f"Deleted secret '{key}'")
    return deleted


def list_stored_keys() -> list:
    """Return list of key names (not values) across all backends."""
    keys = set()
    if _check_keyring():
        pass  # keyring doesn't support listing without iteration
    if _check_fernet():
        try:
            store = _load_encrypted_store()
            keys.update(store.keys())
        except Exception:
            pass
    return sorted(keys)


def storage_method() -> str:
    """Return current storage method description."""
    if _check_keyring():
        return "OS Keyring (Windows Credential Manager / macOS Keychain / SecretService)"
    if _check_fernet():
        return "Fernet-encrypted local file (config/.keystore)"
    return "Plaintext .env file (install 'keyring' or 'cryptography' for encryption)"


def _write_env_key(env_var: str, value: str):
    env_path = ROOT / ".env"
    existing = {}
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.startswith("#"):
                k, _, v = line.partition("=")
                existing[k.strip()] = v.strip()
    existing[env_var] = value
    with open(env_path, "w", encoding="utf-8") as f:
        f.write("# MAX AI secrets — do not commit this file\n")
        for k, v in existing.items():
            if v:
                f.write(f"{k}={v}\n")


def _remove_env_key(env_var: str):
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    lines = []
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith(f"{env_var}="):
            continue
        lines.append(line)
    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ── Convenience wrappers for provider keys ────────────────────────────────

PROVIDER_KEY_MAP = {
    "openai":     "OPENAI_API_KEY",
    "anthropic":  "ANTHROPIC_API_KEY",
    "gemini":     "GOOGLE_API_KEY",
    "groq":       "GROQ_API_KEY",
    "deepseek":   "DEEPSEEK_API_KEY",
    "mistral":    "MISTRAL_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
    "picovoice":  "PICOVOICE_ACCESS_KEY",
}


def set_provider_key(provider: str, api_key: str) -> str:
    env_var = PROVIDER_KEY_MAP.get(provider.lower(), f"{provider.upper()}_API_KEY")
    return set_secret(env_var, api_key)


def get_provider_key(provider: str) -> Optional[str]:
    env_var = PROVIDER_KEY_MAP.get(provider.lower(), f"{provider.upper()}_API_KEY")
    return get_secret(env_var)
