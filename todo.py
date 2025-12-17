"""
Todo module - Todo item management
"""

from typing import List, Optional
from storage import Todo, Storage


class TodoManager:
    """Manages todo items with persistence"""

    def __init__(self, storage: Optional[Storage] = None):
        self.storage = storage or Storage()
        self.todos: List[Todo] = []
        self.load()

    def load(self) -> None:
        """Load todos from storage"""
        self.todos = self.storage.load_todos()

    def save(self) -> None:
        """Save todos to storage"""
        self.storage.save_todos(self.todos)

    def add(self, title: str, timer_minutes: Optional[int] = None) -> Todo:
        """Add a new todo item"""
        todo = Todo.create(title=title, timer_minutes=timer_minutes)
        self.todos.append(todo)
        self.save()
        return todo

    def complete(self, todo_id: str) -> Optional[Todo]:
        """Mark a todo as completed by ID"""
        for todo in self.todos:
            if todo.id == todo_id or todo.id.startswith(todo_id):
                todo.mark_complete()
                self.save()
                return todo
        return None

    def delete(self, todo_id: str) -> bool:
        """Delete a todo by ID"""
        for i, todo in enumerate(self.todos):
            if todo.id == todo_id or todo.id.startswith(todo_id):
                self.todos.pop(i)
                self.save()
                return True
        return False

    def get(self, todo_id: str) -> Optional[Todo]:
        """Get a todo by ID"""
        for todo in self.todos:
            if todo.id == todo_id or todo.id.startswith(todo_id):
                return todo
        return None

    def list_all(self) -> List[Todo]:
        """Get all todos"""
        return self.todos

    def list_pending(self) -> List[Todo]:
        """Get all pending (not completed) todos"""
        return [todo for todo in self.todos if not todo.completed]

    def list_completed(self) -> List[Todo]:
        """Get all completed todos"""
        return [todo for todo in self.todos if todo.completed]

    def clear_completed(self) -> int:
        """Remove all completed todos, return count removed"""
        original_count = len(self.todos)
        self.todos = [todo for todo in self.todos if not todo.completed]
        self.save()
        return original_count - len(self.todos)

    def count(self) -> dict:
        """Get todo counts"""
        pending = len(self.list_pending())
        completed = len(self.list_completed())
        return {
            "total": len(self.todos),
            "pending": pending,
            "completed": completed,
        }
