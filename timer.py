"""
Timer module - Async timer management for parallel timers
"""

import asyncio
from typing import Dict, List, Optional, Callable, Any
from storage import Timer


class TimerManager:
    """Manages multiple timers running in parallel"""

    def __init__(self):
        self.timers: Dict[str, Timer] = {}
        self.tasks: Dict[str, asyncio.Task] = {}
        self._on_tick: Optional[Callable[[], None]] = None
        self._on_complete: Optional[Callable[[Timer], None]] = None
        self._running = False

    def set_callbacks(
        self,
        on_tick: Optional[Callable[[], None]] = None,
        on_complete: Optional[Callable[[Timer], None]] = None,
    ) -> None:
        """Set callback functions for timer events"""
        self._on_tick = on_tick
        self._on_complete = on_complete

    def add_timer(
        self,
        title: str,
        minutes: int,
        todo_id: Optional[str] = None,
    ) -> Timer:
        """Add a new timer and start it if manager is running"""
        timer = Timer.create(title=title, minutes=minutes, todo_id=todo_id)
        self.timers[timer.id] = timer
        return timer

    def remove_timer(self, timer_id: str) -> bool:
        """Remove a timer by ID"""
        # Find timer with matching ID or prefix
        target_id = None
        for tid in self.timers:
            if tid == timer_id or tid.startswith(timer_id):
                target_id = tid
                break

        if target_id is None:
            return False

        # Cancel the task if running
        if target_id in self.tasks:
            self.tasks[target_id].cancel()
            del self.tasks[target_id]

        del self.timers[target_id]
        return True

    def get_timer(self, timer_id: str) -> Optional[Timer]:
        """Get a timer by ID"""
        for tid, timer in self.timers.items():
            if tid == timer_id or tid.startswith(timer_id):
                return timer
        return None

    def get_active_timers(self) -> List[Timer]:
        """Get all active (not completed) timers"""
        return [t for t in self.timers.values() if not t.is_complete]

    def get_all_timers(self) -> List[Timer]:
        """Get all timers"""
        return list(self.timers.values())

    def has_active_timers(self) -> bool:
        """Check if there are any active timers"""
        return len(self.get_active_timers()) > 0

    async def _run_timer(self, timer: Timer) -> None:
        """Run a single timer coroutine"""
        while timer.remaining_seconds > 0 and not timer.paused:
            await asyncio.sleep(1)
            timer.tick()

            if self._on_tick:
                self._on_tick()

        # Timer completed
        if timer.is_complete and self._on_complete:
            self._on_complete(timer)

    def start_timer(self, timer_id: str) -> bool:
        """Start a specific timer"""
        timer = self.get_timer(timer_id)
        if timer is None:
            return False

        # Don't start if already running
        if timer_id in self.tasks and not self.tasks[timer_id].done():
            return False

        task = asyncio.create_task(self._run_timer(timer))
        self.tasks[timer.id] = task
        return True

    def pause_timer(self, timer_id: str) -> bool:
        """Pause a timer"""
        timer = self.get_timer(timer_id)
        if timer:
            timer.paused = True
            return True
        return False

    def resume_timer(self, timer_id: str) -> bool:
        """Resume a paused timer"""
        timer = self.get_timer(timer_id)
        if timer and timer.paused:
            timer.paused = False
            # Restart the timer task
            self.start_timer(timer.id)
            return True
        return False

    async def start_all(self) -> None:
        """Start all timers"""
        self._running = True
        for timer_id in self.timers:
            if timer_id not in self.tasks or self.tasks[timer_id].done():
                self.start_timer(timer_id)

    async def wait_all(self) -> None:
        """Wait for all timers to complete"""
        if self.tasks:
            await asyncio.gather(*self.tasks.values(), return_exceptions=True)

    def stop_all(self) -> None:
        """Stop all timers"""
        self._running = False
        for task in self.tasks.values():
            task.cancel()
        self.tasks.clear()

    def cleanup_completed(self) -> int:
        """Remove completed timers, return count removed"""
        completed_ids = [tid for tid, t in self.timers.items() if t.is_complete]
        for tid in completed_ids:
            if tid in self.tasks:
                del self.tasks[tid]
            del self.timers[tid]
        return len(completed_ids)
