"""
MAX AI — Productivity Engine
LEREON Technologies

To-do lists, notes, reminders with SQLite persistence.
"""

import logging
import sqlite3
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List
from pathlib import Path

logger = logging.getLogger("MAX.productivity")
ROOT = Path(__file__).parent.parent


class Priority(Enum):
    LOW    = "low"
    MEDIUM = "medium"
    HIGH   = "high"


@dataclass
class Todo:
    id: str
    title: str
    notes: str = ""
    priority: Priority = Priority.MEDIUM
    done: bool = False
    created_at: float = field(default_factory=time.time)
    due_at: Optional[float] = None
    tags: List[str] = field(default_factory=list)


@dataclass
class Note:
    id: str
    title: str
    content: str
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    tags: List[str] = field(default_factory=list)


@dataclass
class Reminder:
    id: str
    message: str
    remind_at: float
    done: bool = False
    created_at: float = field(default_factory=time.time)


class ProductivityEngine:
    def __init__(self):
        db_path = ROOT / "memory" / "productivity.db"
        db_path.parent.mkdir(exist_ok=True)
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._init_db()
        logger.info("Productivity engine ready.")

    def _init_db(self):
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS todos (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                notes TEXT DEFAULT '',
                priority TEXT DEFAULT 'medium',
                done INTEGER DEFAULT 0,
                created_at REAL,
                due_at REAL,
                tags TEXT DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS notes (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                content TEXT DEFAULT '',
                created_at REAL,
                updated_at REAL,
                tags TEXT DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS reminders (
                id TEXT PRIMARY KEY,
                message TEXT NOT NULL,
                remind_at REAL NOT NULL,
                done INTEGER DEFAULT 0,
                created_at REAL
            );
        """)
        self._conn.commit()

    # ── Todos ─────────────────────────────────────────────────────────────

    def add_todo(self, title: str, notes: str = "", priority: Priority = Priority.MEDIUM,
                 due_at: float = None, tags: List[str] = None) -> Todo:
        t = Todo(id=str(uuid.uuid4())[:8], title=title, notes=notes,
                 priority=priority, due_at=due_at, tags=tags or [])
        self._conn.execute(
            "INSERT INTO todos (id,title,notes,priority,done,created_at,due_at,tags) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (t.id, t.title, t.notes, t.priority.value, 0,
             t.created_at, t.due_at, ",".join(t.tags))
        )
        self._conn.commit()
        return t

    def complete_todo(self, todo_id: str) -> bool:
        cur = self._conn.execute("UPDATE todos SET done=1 WHERE id=?", (todo_id,))
        self._conn.commit()
        return cur.rowcount > 0

    def delete_todo(self, todo_id: str) -> bool:
        cur = self._conn.execute("DELETE FROM todos WHERE id=?", (todo_id,))
        self._conn.commit()
        return cur.rowcount > 0

    def list_todos(self, include_done: bool = False) -> List[Todo]:
        query = "SELECT id,title,notes,priority,done,created_at,due_at,tags FROM todos"
        if not include_done:
            query += " WHERE done=0"
        query += " ORDER BY created_at DESC"
        rows = self._conn.execute(query).fetchall()
        result = []
        for r in rows:
            try:
                pri = Priority(r[3])
            except ValueError:
                pri = Priority.MEDIUM
            result.append(Todo(
                id=r[0], title=r[1], notes=r[2], priority=pri,
                done=bool(r[4]), created_at=r[5], due_at=r[6],
                tags=r[7].split(",") if r[7] else []
            ))
        return result

    def get_overdue(self) -> List[Todo]:
        now = time.time()
        rows = self._conn.execute(
            "SELECT id,title,notes,priority,done,created_at,due_at,tags "
            "FROM todos WHERE done=0 AND due_at IS NOT NULL AND due_at < ?", (now,)
        ).fetchall()
        return [Todo(id=r[0], title=r[1], notes=r[2], priority=Priority(r[3]),
                     done=bool(r[4]), created_at=r[5], due_at=r[6],
                     tags=r[7].split(",") if r[7] else []) for r in rows]

    # ── Notes ─────────────────────────────────────────────────────────────

    def add_note(self, title: str, content: str = "", tags: List[str] = None) -> Note:
        n = Note(id=str(uuid.uuid4())[:8], title=title, content=content, tags=tags or [])
        self._conn.execute(
            "INSERT INTO notes (id,title,content,created_at,updated_at,tags) VALUES (?,?,?,?,?,?)",
            (n.id, n.title, n.content, n.created_at, n.updated_at, ",".join(n.tags))
        )
        self._conn.commit()
        return n

    def update_note(self, note_id: str, title: str = None, content: str = None) -> bool:
        updates, params = [], []
        if title is not None:
            updates.append("title=?"); params.append(title)
        if content is not None:
            updates.append("content=?"); params.append(content)
        updates.append("updated_at=?"); params.append(time.time())
        params.append(note_id)
        cur = self._conn.execute(f"UPDATE notes SET {', '.join(updates)} WHERE id=?", params)
        self._conn.commit()
        return cur.rowcount > 0

    def delete_note(self, note_id: str) -> bool:
        cur = self._conn.execute("DELETE FROM notes WHERE id=?", (note_id,))
        self._conn.commit()
        return cur.rowcount > 0

    def list_notes(self) -> List[Note]:
        rows = self._conn.execute(
            "SELECT id,title,content,created_at,updated_at,tags FROM notes ORDER BY updated_at DESC"
        ).fetchall()
        return [Note(id=r[0], title=r[1], content=r[2], created_at=r[3],
                     updated_at=r[4], tags=r[5].split(",") if r[5] else []) for r in rows]

    def search_notes(self, query: str) -> List[Note]:
        q = f"%{query.lower()}%"
        rows = self._conn.execute(
            "SELECT id,title,content,created_at,updated_at,tags FROM notes "
            "WHERE lower(title) LIKE ? OR lower(content) LIKE ? ORDER BY updated_at DESC", (q, q)
        ).fetchall()
        return [Note(id=r[0], title=r[1], content=r[2], created_at=r[3],
                     updated_at=r[4], tags=r[5].split(",") if r[5] else []) for r in rows]

    # ── Reminders ─────────────────────────────────────────────────────────

    def add_reminder(self, message: str, remind_at: float) -> Reminder:
        r = Reminder(id=str(uuid.uuid4())[:8], message=message, remind_at=remind_at)
        self._conn.execute(
            "INSERT INTO reminders (id,message,remind_at,done,created_at) VALUES (?,?,?,?,?)",
            (r.id, r.message, r.remind_at, 0, r.created_at)
        )
        self._conn.commit()
        return r

    def get_due_reminders(self) -> List[Reminder]:
        now = time.time()
        rows = self._conn.execute(
            "SELECT id,message,remind_at,done,created_at FROM reminders "
            "WHERE done=0 AND remind_at<=?", (now,)
        ).fetchall()
        return [Reminder(id=r[0], message=r[1], remind_at=r[2],
                         done=bool(r[3]), created_at=r[4]) for r in rows]

    def mark_reminder_done(self, reminder_id: str) -> bool:
        cur = self._conn.execute("UPDATE reminders SET done=1 WHERE id=?", (reminder_id,))
        self._conn.commit()
        return cur.rowcount > 0

    def close(self):
        self._conn.close()
