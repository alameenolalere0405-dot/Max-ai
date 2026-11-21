"""
MAX AI — Knowledge Base
LEREON Technologies

Allows users to import documents (PDF, DOCX, TXT, MD) that MAX can reference.
Stores extracted text in SQLite. Supports keyword search and context retrieval.
"""

import logging
import sqlite3
import time
import os
import hashlib
from pathlib import Path
from typing import Optional

logger = logging.getLogger("MAX.knowledge")
ROOT = Path(__file__).parent.parent


class KnowledgeBase:
    """
    User-controlled document store. MAX can search imported docs to answer questions.
    All files remain under user control — nothing is sent anywhere automatically.
    """

    SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md", ".docx", ".py", ".json", ".csv", ".html"}

    def __init__(self):
        db_path = ROOT / "memory" / "knowledge.db"
        db_path.parent.mkdir(exist_ok=True)
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._init_db()
        logger.info("Knowledge base ready.")

    def _init_db(self):
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                hash    TEXT UNIQUE NOT NULL,
                name    TEXT NOT NULL,
                path    TEXT NOT NULL,
                ext     TEXT NOT NULL,
                size_kb REAL NOT NULL,
                added   REAL NOT NULL,
                content TEXT NOT NULL,
                tags    TEXT DEFAULT ''
            )
        """)
        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_name ON documents(name)"
        )
        self._conn.commit()

    # ── Import ────────────────────────────────────────────────────────────

    def import_file(self, file_path: str) -> dict:
        """
        Import a document. Returns {"ok": bool, "message": str, "id": int|None}.
        """
        p = Path(file_path)
        if not p.exists():
            return {"ok": False, "message": f"File not found: {file_path}", "id": None}
        if not p.is_file():
            return {"ok": False, "message": f"Not a file: {file_path}", "id": None}
        if p.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            return {"ok": False,
                    "message": f"Unsupported type '{p.suffix}'. Supported: {', '.join(self.SUPPORTED_EXTENSIONS)}",
                    "id": None}

        # Compute hash to avoid duplicates
        file_hash = self._hash_file(p)
        existing = self._conn.execute(
            "SELECT id, name FROM documents WHERE hash=?", (file_hash,)
        ).fetchone()
        if existing:
            return {"ok": False,
                    "message": f"Already imported as '{existing[1]}' (id={existing[0]})",
                    "id": existing[0]}

        # Extract text
        try:
            content = self._extract_text(p)
        except Exception as e:
            return {"ok": False, "message": f"Extraction failed: {e}", "id": None}

        if not content.strip():
            return {"ok": False, "message": "File appears to be empty or unreadable.", "id": None}

        size_kb = p.stat().st_size / 1024
        cur = self._conn.execute(
            "INSERT INTO documents (hash, name, path, ext, size_kb, added, content) "
            "VALUES (?,?,?,?,?,?,?)",
            (file_hash, p.name, str(p), p.suffix.lower(), size_kb, time.time(), content)
        )
        self._conn.commit()
        logger.info(f"Imported: {p.name} ({size_kb:.1f} KB, {len(content)} chars)")
        return {"ok": True, "message": f"Imported '{p.name}' successfully.", "id": cur.lastrowid}

    def _hash_file(self, p: Path) -> str:
        h = hashlib.sha256()
        with open(p, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()

    def _extract_text(self, p: Path) -> str:
        ext = p.suffix.lower()
        if ext == ".pdf":
            return self._extract_pdf(p)
        if ext == ".docx":
            return self._extract_docx(p)
        # Plain text types
        return p.read_text(encoding="utf-8", errors="replace")[:500_000]

    def _extract_pdf(self, p: Path) -> str:
        try:
            import PyPDF2
            reader = PyPDF2.PdfReader(str(p))
            pages = []
            for i, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                if text.strip():
                    pages.append(f"[Page {i+1}]\n{text}")
            return "\n\n".join(pages)
        except ImportError:
            return f"[PDF: PyPDF2 not installed — install with: pip install PyPDF2]"

    def _extract_docx(self, p: Path) -> str:
        try:
            from docx import Document
            doc = Document(str(p))
            return "\n".join(para.text for para in doc.paragraphs if para.text.strip())
        except ImportError:
            return "[DOCX: python-docx not installed — install with: pip install python-docx]"

    # ── Search ────────────────────────────────────────────────────────────

    def search(self, query: str, max_results: int = 3, snippet_len: int = 800) -> list:
        """
        Keyword search across all documents.
        Returns list of {"id", "name", "snippet", "relevance"}.
        """
        if not query.strip():
            return []
        terms = query.lower().split()
        rows = self._conn.execute(
            "SELECT id, name, content FROM documents"
        ).fetchall()

        results = []
        for doc_id, name, content in rows:
            content_lower = content.lower()
            score = sum(content_lower.count(t) for t in terms)
            if score > 0:
                # Find best snippet
                best_pos = 0
                best_count = 0
                window = snippet_len
                for i in range(0, len(content) - window, window // 2):
                    chunk = content_lower[i:i + window]
                    count = sum(chunk.count(t) for t in terms)
                    if count > best_count:
                        best_count = count
                        best_pos = i
                snippet = content[best_pos:best_pos + snippet_len].strip()
                results.append({
                    "id": doc_id,
                    "name": name,
                    "snippet": snippet,
                    "relevance": score
                })

        results.sort(key=lambda x: x["relevance"], reverse=True)
        return results[:max_results]

    def get_context_for_query(self, query: str) -> str:
        """Return formatted context string for injection into AI prompt."""
        results = self.search(query)
        if not results:
            return ""
        parts = ["[Knowledge Base Context]"]
        for r in results:
            parts.append(f"\nSource: {r['name']}\n{r['snippet']}")
        return "\n".join(parts)

    # ── Management ────────────────────────────────────────────────────────

    def list_documents(self) -> list:
        rows = self._conn.execute(
            "SELECT id, name, ext, size_kb, added, tags FROM documents ORDER BY added DESC"
        ).fetchall()
        return [
            {"id": r[0], "name": r[1], "ext": r[2],
             "size_kb": r[3], "added": r[4], "tags": r[5]}
            for r in rows
        ]

    def delete_document(self, doc_id: int) -> bool:
        try:
            self._conn.execute("DELETE FROM documents WHERE id=?", (doc_id,))
            self._conn.commit()
            logger.info(f"Deleted document id={doc_id}")
            return True
        except Exception as e:
            logger.error(f"Delete failed: {e}")
            return False

    def get_document(self, doc_id: int) -> Optional[dict]:
        row = self._conn.execute(
            "SELECT id, name, path, ext, size_kb, added, content, tags FROM documents WHERE id=?",
            (doc_id,)
        ).fetchone()
        if not row:
            return None
        return {"id": row[0], "name": row[1], "path": row[2], "ext": row[3],
                "size_kb": row[4], "added": row[5], "content": row[6], "tags": row[7]}

    def document_count(self) -> int:
        return self._conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]

    def close(self):
        self._conn.close()
