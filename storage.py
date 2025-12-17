"""
Storage module - Data models and JSON persistence
"""

import json
import os
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path


@dataclass
class Todo:
    """Todo item data model"""
    id: str
    title: str
    completed: bool = False
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    timer_minutes: Optional[int] = None  # Associated timer duration

    @classmethod
    def create(cls, title: str, timer_minutes: Optional[int] = None) -> "Todo":
        """Create a new todo item with auto-generated ID"""
        return cls(
            id=str(uuid.uuid4())[:8],
            title=title,
            timer_minutes=timer_minutes,
        )

    def mark_complete(self) -> None:
        """Mark this todo as completed"""
        self.completed = True
        self.completed_at = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Todo":
        """Create Todo from dictionary"""
        return cls(**data)


@dataclass
class Timer:
    """Timer data model for active timers"""
    id: str
    title: str
    total_seconds: int
    remaining_seconds: int
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    todo_id: Optional[str] = None  # Associated todo ID
    paused: bool = False

    @classmethod
    def create(cls, title: str, minutes: int, todo_id: Optional[str] = None) -> "Timer":
        """Create a new timer with auto-generated ID"""
        total_seconds = minutes * 60
        return cls(
            id=str(uuid.uuid4())[:8],
            title=title,
            total_seconds=total_seconds,
            remaining_seconds=total_seconds,
            todo_id=todo_id,
        )

    @property
    def progress(self) -> float:
        """Get progress percentage (0.0 to 1.0)"""
        if self.total_seconds == 0:
            return 1.0
        return (self.total_seconds - self.remaining_seconds) / self.total_seconds

    @property
    def elapsed_seconds(self) -> int:
        """Get elapsed seconds"""
        return self.total_seconds - self.remaining_seconds

    @property
    def is_complete(self) -> bool:
        """Check if timer is complete"""
        return self.remaining_seconds <= 0

    def format_remaining(self) -> str:
        """Format remaining time as MM:SS"""
        mins, secs = divmod(self.remaining_seconds, 60)
        return f"{mins:02d}:{secs:02d}"

    def tick(self) -> bool:
        """Decrease remaining time by 1 second. Returns True if still running."""
        if self.remaining_seconds > 0 and not self.paused:
            self.remaining_seconds -= 1
        return self.remaining_seconds > 0


class Storage:
    """JSON file storage for todos"""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.todos_file = self.data_dir / "todos.json"
        self._ensure_data_dir()

    def _ensure_data_dir(self) -> None:
        """Create data directory if it doesn't exist"""
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def load_todos(self) -> List[Todo]:
        """Load todos from JSON file"""
        if not self.todos_file.exists():
            return []

        try:
            with open(self.todos_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return [Todo.from_dict(item) for item in data]
        except (json.JSONDecodeError, KeyError) as e:
            # Return empty list if file is corrupted
            return []

    def save_todos(self, todos: List[Todo]) -> None:
        """Save todos to JSON file"""
        self._ensure_data_dir()
        with open(self.todos_file, "w", encoding="utf-8") as f:
            json.dump([todo.to_dict() for todo in todos], f, ensure_ascii=False, indent=2)

    def clear_todos(self) -> None:
        """Clear all todos"""
        self.save_todos([])
