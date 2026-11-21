"""MAX AI — Task Manager"""

import logging
import time
import uuid
import threading
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Callable

logger = logging.getLogger("MAX.tasks")


class TaskStatus(Enum):
    QUEUED    = "queued"
    RUNNING   = "running"
    PAUSED    = "paused"
    COMPLETED = "completed"
    FAILED    = "failed"
    CANCELLED = "cancelled"


@dataclass
class Task:
    id: str
    title: str
    description: str
    status: TaskStatus = TaskStatus.QUEUED
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    finished_at: Optional[float] = None
    result: Optional[str] = None
    error: Optional[str] = None
    progress: float = 0.0  # 0.0 – 1.0


class TaskManager:
    def __init__(self):
        self._tasks: dict[str, Task] = {}
        self._lock = threading.Lock()
        self._callbacks: list[Callable] = []

    def on_update(self, cb: Callable):
        self._callbacks.append(cb)

    def _notify(self, task: Task):
        for cb in self._callbacks:
            try:
                cb(task)
            except Exception:
                pass

    def create(self, title: str, description: str = "") -> Task:
        task = Task(id=str(uuid.uuid4())[:8], title=title, description=description)
        with self._lock:
            self._tasks[task.id] = task
        logger.info(f"Task created: [{task.id}] {title}")
        self._notify(task)
        return task

    def update(self, task_id: str, status: TaskStatus = None,
               progress: float = None, result: str = None, error: str = None):
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return
            if status:
                task.status = status
                if status == TaskStatus.RUNNING and not task.started_at:
                    task.started_at = time.time()
                if status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
                    task.finished_at = time.time()
            if progress is not None:
                task.progress = max(0.0, min(1.0, progress))
            if result:
                task.result = result
            if error:
                task.error = error
        self._notify(task)

    def cancel(self, task_id: str):
        self.update(task_id, status=TaskStatus.CANCELLED)

    def get(self, task_id: str) -> Optional[Task]:
        return self._tasks.get(task_id)

    def all(self) -> list:
        with self._lock:
            return sorted(self._tasks.values(), key=lambda t: t.created_at, reverse=True)

    def active(self) -> list:
        return [t for t in self.all()
                if t.status in (TaskStatus.QUEUED, TaskStatus.RUNNING, TaskStatus.PAUSED)]

    def clear_completed(self):
        with self._lock:
            to_remove = [tid for tid, t in self._tasks.items()
                         if t.status in (TaskStatus.COMPLETED, TaskStatus.CANCELLED, TaskStatus.FAILED)]
            for tid in to_remove:
                del self._tasks[tid]
        logger.info(f"Cleared {len(to_remove)} completed tasks.")

    def shutdown(self):
        logger.info("Task manager shutting down.")
