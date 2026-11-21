"""
MAX AI — Studio Engine
LEREON Technologies

Productivity and content-generation workspace.
Writing, coding, document analysis, PDF reading, report generation.
"""

import logging
import asyncio
from pathlib import Path
from typing import Optional

logger = logging.getLogger("MAX.studio")
ROOT = Path(__file__).parent.parent


class StudioEngine:
    """
    Assists with writing, code generation, document reading,
    summarization, and structured output creation.
    """

    # Prompt templates for different studio tasks
    TEMPLATES = {
        "summarize": (
            "Summarize the following content clearly and concisely. "
            "Preserve the key points, main arguments, and important details:\n\n{content}"
        ),
        "code_review": (
            "Review the following code. Identify bugs, security issues, "
            "performance problems, and style violations. Provide specific, "
            "actionable suggestions:\n\n```\n{content}\n```"
        ),
        "write_docs": (
            "Generate professional documentation for the following code. "
            "Include: purpose, parameters, return values, usage examples, "
            "and any important notes:\n\n```\n{content}\n```"
        ),
        "readme": (
            "Generate a professional README.md for the following project/code. "
            "Include: title, description, features, installation, usage, "
            "configuration, and contributing sections:\n\n{content}"
        ),
        "explain": (
            "Explain the following code or concept clearly. "
            "Use simple language, concrete examples, and analogies where helpful:\n\n{content}"
        ),
        "refactor": (
            "Refactor the following code to improve readability, efficiency, "
            "and maintainability. Explain each change made:\n\n```\n{content}\n```"
        ),
        "unit_tests": (
            "Write comprehensive unit tests for the following code. "
            "Cover: happy paths, edge cases, error cases, and boundary conditions:\n\n"
            "```\n{content}\n```"
        ),
        "presentation_outline": (
            "Create a detailed presentation outline for the following topic. "
            "Include: title slide, agenda, key sections with bullet points, "
            "and a conclusion slide:\n\n{content}"
        ),
        "report": (
            "Generate a professional structured report on the following topic or data. "
            "Include: executive summary, key findings, analysis, recommendations:\n\n{content}"
        ),
        "email_draft": (
            "Draft a professional email based on the following context. "
            "Be clear, concise, and appropriate in tone:\n\n{content}"
        ),
        "meeting_summary": (
            "Summarize the following meeting notes or transcript into a structured summary. "
            "Include: key decisions, action items (with owners if mentioned), "
            "and follow-up items:\n\n{content}"
        ),
    }

    def __init__(self, core=None):
        self._core = core
        logger.info("Studio engine ready.")

    async def run_task(
        self,
        task_type: str,
        content: str,
        custom_instruction: str = "",
        provider_name: Optional[str] = None,
    ) -> str:
        """
        Run a studio task.
        task_type: one of TEMPLATES keys, or 'custom'
        Returns the generated text.
        """
        if not content.strip():
            return "No content provided."

        if task_type == "custom":
            if not custom_instruction:
                return "No instruction provided for custom task."
            prompt = f"{custom_instruction}\n\n{content}"
        else:
            template = self.TEMPLATES.get(task_type)
            if not template:
                available = ", ".join(self.TEMPLATES.keys())
                return f"Unknown task type '{task_type}'. Available: {available}"
            prompt = template.format(content=content[:50_000])  # Cap at 50k chars

        if self._core is None:
            return "Studio: no AI core connected."

        # Use core's chat method directly with a targeted system prompt
        old_conv = list(self._core.conversation)
        try:
            resp = await self._core.chat(prompt, force_provider=provider_name)
            return resp.text
        finally:
            # Restore conversation - studio tasks don't pollute main history
            self._core.conversation = old_conv

    def run_task_sync(self, task_type: str, content: str, **kwargs) -> str:
        """Synchronous wrapper."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.run_task(task_type, content, **kwargs))
        finally:
            loop.close()

    # ── Document reading ──────────────────────────────────────────────────

    def read_file(self, path: str) -> str:
        """Read a file and return its text content."""
        p = Path(path)
        if not p.exists():
            return f"File not found: {path}"
        if not p.is_file():
            return f"Not a file: {path}"
        if p.stat().st_size > 5_000_000:
            return f"File too large (>5 MB): {path}"

        suffix = p.suffix.lower()
        try:
            if suffix == ".pdf":
                return self._read_pdf(p)
            if suffix == ".docx":
                return self._read_docx(p)
            if suffix in (".xlsx", ".xls"):
                return self._read_xlsx(p)
            # Plain text
            return p.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            return f"Read error: {e}"

    def _read_pdf(self, p: Path) -> str:
        try:
            import PyPDF2
            reader = PyPDF2.PdfReader(str(p))
            pages = []
            for i, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                if text.strip():
                    pages.append(f"[Page {i+1}]\n{text}")
            return "\n\n".join(pages) or "(No extractable text in PDF)"
        except ImportError:
            return "PDF reading requires PyPDF2: pip install PyPDF2"
        except Exception as e:
            return f"PDF error: {e}"

    def _read_docx(self, p: Path) -> str:
        try:
            from docx import Document
            doc = Document(str(p))
            paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
            return "\n".join(paragraphs) or "(Empty document)"
        except ImportError:
            return "DOCX reading requires python-docx: pip install python-docx"
        except Exception as e:
            return f"DOCX error: {e}"

    def _read_xlsx(self, p: Path) -> str:
        try:
            import openpyxl
            wb = openpyxl.load_workbook(str(p), read_only=True, data_only=True)
            lines = []
            for sheet in wb.sheetnames:
                ws = wb[sheet]
                lines.append(f"[Sheet: {sheet}]")
                for row in ws.iter_rows(values_only=True):
                    row_text = "\t".join(str(c) if c is not None else "" for c in row)
                    if row_text.strip():
                        lines.append(row_text)
            return "\n".join(lines)
        except ImportError:
            return "XLSX reading requires openpyxl: pip install openpyxl"
        except Exception as e:
            return f"XLSX error: {e}"

    def save_output(self, content: str, path: str) -> dict:
        """Save generated content to a file."""
        try:
            p = Path(path)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
            return {"ok": True, "path": str(p), "size": p.stat().st_size}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @property
    def task_types(self) -> list:
        return list(self.TEMPLATES.keys()) + ["custom"]
