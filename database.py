"""
MAX AI — Unified Database Manager
LEREON Technologies

Single SQLite database with schema versioning and migrations.
Replaces scattered per-module databases.
"""

import sqlite3
import logging
import time
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger("MAX.database")
ROOT = Path(__file__).parent.parent

SCHEMA_VERSION = 4


class Database:
    """
    Thread-safe SQLite database manager for MAX AI.
    Handles all persistent data except secrets (see secure_storage.py).
    """

    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            db_path = ROOT / "memory" / "max.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._path = db_path
        self._conn = sqlite3.connect(
            str(db_path),
            check_same_thread=False,
            timeout=30,
        )
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._migrate()
        logger.info(f"Database ready: {db_path} (schema v{SCHEMA_VERSION})")

    # ── Migrations ────────────────────────────────────────────────────────

    def _get_version(self) -> int:
        try:
            row = self._conn.execute(
                "SELECT value FROM meta WHERE key='schema_version'"
            ).fetchone()
            return int(row["value"]) if row else 0
        except Exception:
            return 0

    def _set_version(self, v: int):
        self._conn.execute(
            "INSERT OR REPLACE INTO meta (key, value) VALUES ('schema_version', ?)",
            (str(v),)
        )

    def _migrate(self):
        # Ensure meta table exists first
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS meta (
                key   TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        self._conn.commit()

        v = self._get_version()
        if v < 1:
            self._migrate_v1()
        if v < 2:
            self._migrate_v2()
        if v < 3:
            self._migrate_v3()
        if v < 4:
            self._migrate_v4()

    def _migrate_v1(self):
        """Initial schema: conversations, messages, preferences."""
        logger.info("Applying DB migration v1")
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS conversations (
                id          TEXT PRIMARY KEY,
                title       TEXT NOT NULL DEFAULT 'New conversation',
                provider    TEXT NOT NULL DEFAULT '',
                model       TEXT NOT NULL DEFAULT '',
                created_at  REAL NOT NULL,
                updated_at  REAL NOT NULL,
                archived    INTEGER NOT NULL DEFAULT 0,
                pinned      INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS messages (
                id              TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
                role            TEXT NOT NULL,
                content         TEXT NOT NULL,
                provider        TEXT NOT NULL DEFAULT '',
                model           TEXT NOT NULL DEFAULT '',
                tokens          INTEGER NOT NULL DEFAULT 0,
                duration_ms     REAL NOT NULL DEFAULT 0,
                created_at      REAL NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_messages_conv
                ON messages(conversation_id, created_at);

            CREATE TABLE IF NOT EXISTS preferences (
                key   TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
        """)
        self._set_version(1)
        self._conn.commit()

    def _migrate_v2(self):
        """Add memory facts and knowledge documents."""
        logger.info("Applying DB migration v2")
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS memory_facts (
                id         TEXT PRIMARY KEY,
                key        TEXT NOT NULL,
                value      TEXT NOT NULL,
                source     TEXT NOT NULL DEFAULT 'user',
                created_at REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS knowledge_documents (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                hash       TEXT UNIQUE NOT NULL,
                name       TEXT NOT NULL,
                path       TEXT NOT NULL,
                ext        TEXT NOT NULL,
                size_kb    REAL NOT NULL,
                added_at   REAL NOT NULL,
                content    TEXT NOT NULL,
                tags       TEXT NOT NULL DEFAULT ''
            );

            CREATE INDEX IF NOT EXISTS idx_knowledge_hash
                ON knowledge_documents(hash);
        """)
        self._set_version(2)
        self._conn.commit()

    def _migrate_v3(self):
        """Add productivity tables."""
        logger.info("Applying DB migration v3")
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS todos (
                id         TEXT PRIMARY KEY,
                title      TEXT NOT NULL,
                notes      TEXT NOT NULL DEFAULT '',
                priority   TEXT NOT NULL DEFAULT 'medium',
                done       INTEGER NOT NULL DEFAULT 0,
                created_at REAL NOT NULL,
                due_at     REAL,
                tags       TEXT NOT NULL DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS notes (
                id         TEXT PRIMARY KEY,
                title      TEXT NOT NULL,
                content    TEXT NOT NULL DEFAULT '',
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL,
                tags       TEXT NOT NULL DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS reminders (
                id         TEXT PRIMARY KEY,
                message    TEXT NOT NULL,
                remind_at  REAL NOT NULL,
                done       INTEGER NOT NULL DEFAULT 0,
                created_at REAL NOT NULL
            );
        """)
        self._set_version(3)
        self._conn.commit()

    def _migrate_v4(self):
        """Add conversation search index and audit log."""
        logger.info("Applying DB migration v4")
        self._conn.executescript("""
            CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts
                USING fts5(content, content_rowid=rowid,
                           content='messages', tokenize='porter unicode61');

            CREATE TABLE IF NOT EXISTS audit_log (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                ts         REAL NOT NULL,
                action     TEXT NOT NULL,
                detail     TEXT NOT NULL DEFAULT '',
                success    INTEGER NOT NULL DEFAULT 1
            );
        """)
        self._set_version(4)
        self._conn.commit()

    # ── Conversations ─────────────────────────────────────────────────────

    def create_conversation(self, conv_id: str, title: str = "New conversation",
                            provider: str = "", model: str = "") -> dict:
        now = time.time()
        self._conn.execute(
            "INSERT INTO conversations (id, title, provider, model, created_at, updated_at) "
            "VALUES (?,?,?,?,?,?)",
            (conv_id, title, provider, model, now, now)
        )
        self._conn.commit()
        return {"id": conv_id, "title": title, "created_at": now}

    def get_conversation(self, conv_id: str) -> Optional[dict]:
        row = self._conn.execute(
            "SELECT * FROM conversations WHERE id=?", (conv_id,)
        ).fetchone()
        return dict(row) if row else None

    def list_conversations(self, limit: int = 100, archived: bool = False) -> list:
        rows = self._conn.execute(
            "SELECT id, title, provider, model, created_at, updated_at, pinned "
            "FROM conversations WHERE archived=? "
            "ORDER BY pinned DESC, updated_at DESC LIMIT ?",
            (1 if archived else 0, limit)
        ).fetchall()
        return [dict(r) for r in rows]

    def update_conversation_title(self, conv_id: str, title: str):
        self._conn.execute(
            "UPDATE conversations SET title=?, updated_at=? WHERE id=?",
            (title, time.time(), conv_id)
        )
        self._conn.commit()

    def touch_conversation(self, conv_id: str, provider: str = "", model: str = ""):
        self._conn.execute(
            "UPDATE conversations SET updated_at=?, provider=?, model=? WHERE id=?",
            (time.time(), provider, model, conv_id)
        )
        self._conn.commit()

    def archive_conversation(self, conv_id: str):
        self._conn.execute(
            "UPDATE conversations SET archived=1 WHERE id=?", (conv_id,)
        )
        self._conn.commit()

    def delete_conversation(self, conv_id: str):
        self._conn.execute("DELETE FROM conversations WHERE id=?", (conv_id,))
        self._conn.commit()

    def search_conversations(self, query: str) -> list:
        q = f"%{query.lower()}%"
        rows = self._conn.execute(
            "SELECT DISTINCT c.id, c.title, c.updated_at FROM conversations c "
            "JOIN messages m ON m.conversation_id = c.id "
            "WHERE lower(m.content) LIKE ? OR lower(c.title) LIKE ? "
            "ORDER BY c.updated_at DESC LIMIT 50",
            (q, q)
        ).fetchall()
        return [dict(r) for r in rows]

    # ── Messages ──────────────────────────────────────────────────────────

    def add_message(self, msg_id: str, conv_id: str, role: str, content: str,
                    provider: str = "", model: str = "",
                    tokens: int = 0, duration_ms: float = 0.0) -> dict:
        now = time.time()
        self._conn.execute(
            "INSERT INTO messages "
            "(id, conversation_id, role, content, provider, model, tokens, duration_ms, created_at) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (msg_id, conv_id, role, content, provider, model, tokens, duration_ms, now)
        )
        self._conn.commit()
        self.touch_conversation(conv_id, provider, model)
        return {"id": msg_id, "role": role, "content": content, "created_at": now}

    def get_messages(self, conv_id: str, limit: int = 200) -> list:
        rows = self._conn.execute(
            "SELECT * FROM messages WHERE conversation_id=? "
            "ORDER BY created_at ASC LIMIT ?",
            (conv_id, limit)
        ).fetchall()
        return [dict(r) for r in rows]

    def get_last_messages(self, conv_id: str, n: int = 20) -> list:
        rows = self._conn.execute(
            "SELECT * FROM messages WHERE conversation_id=? "
            "ORDER BY created_at DESC LIMIT ?",
            (conv_id, n)
        ).fetchall()
        return [dict(r) for r in reversed(rows)]

    def count_messages(self, conv_id: str) -> int:
        return self._conn.execute(
            "SELECT COUNT(*) FROM messages WHERE conversation_id=?", (conv_id,)
        ).fetchone()[0]

    # ── Preferences ───────────────────────────────────────────────────────

    def set_pref(self, key: str, value: str):
        self._conn.execute(
            "INSERT OR REPLACE INTO preferences (key, value) VALUES (?,?)",
            (key, str(value))
        )
        self._conn.commit()

    def get_pref(self, key: str, default: str = "") -> str:
        row = self._conn.execute(
            "SELECT value FROM preferences WHERE key=?", (key,)
        ).fetchone()
        return row["value"] if row else default

    def all_prefs(self) -> dict:
        rows = self._conn.execute("SELECT key, value FROM preferences").fetchall()
        return {r["key"]: r["value"] for r in rows}

    # ── Memory Facts ──────────────────────────────────────────────────────

    def save_fact(self, fact_id: str, key: str, value: str, source: str = "user"):
        self._conn.execute(
            "INSERT OR REPLACE INTO memory_facts (id, key, value, source, created_at) "
            "VALUES (?,?,?,?,?)",
            (fact_id, key, value, source, time.time())
        )
        self._conn.commit()

    def get_facts(self) -> list:
        rows = self._conn.execute(
            "SELECT * FROM memory_facts ORDER BY created_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]

    def delete_fact(self, fact_id: str) -> bool:
        cur = self._conn.execute(
            "DELETE FROM memory_facts WHERE id=?", (fact_id,)
        )
        self._conn.commit()
        return cur.rowcount > 0

    # ── Audit ─────────────────────────────────────────────────────────────

    def audit(self, action: str, detail: str = "", success: bool = True):
        self._conn.execute(
            "INSERT INTO audit_log (ts, action, detail, success) VALUES (?,?,?,?)",
            (time.time(), action, detail[:500], 1 if success else 0)
        )
        self._conn.commit()

    def get_audit_log(self, limit: int = 100) -> list:
        rows = self._conn.execute(
            "SELECT * FROM audit_log ORDER BY ts DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]

    # ── Backup / restore ──────────────────────────────────────────────────

    def backup(self, dest: Path) -> bool:
        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            backup_conn = sqlite3.connect(str(dest))
            self._conn.backup(backup_conn)
            backup_conn.close()
            logger.info(f"Database backed up to {dest}")
            return True
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return False

    # ── Close ─────────────────────────────────────────────────────────────

    def close(self):
        try:
            self._conn.close()
        except Exception:
            pass

    @property
    def path(self) -> Path:
        return self._path


# Singleton
_db: Optional[Database] = None

def get_db() -> Database:
    global _db
    if _db is None:
        _db = Database()
    return _db
