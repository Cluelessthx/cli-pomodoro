#!/usr/bin/env python3
"""
CLI Pomodoro Timer - A beautiful command-line pomodoro timer with Rich progress bar
Supports multiple parallel timers, todo management, and system notifications
"""

import asyncio
import sys
import os
from typing import Optional
from pathlib import Path

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    os.system("")  # Enable ANSI escape sequences

import typer
from rich.console import Console
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.live import Live

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from storage import Storage
from todo import TodoManager
from timer import TimerManager
from ui import PomodoroUI, send_notification, SYMBOLS

app = typer.Typer(help="CLI Pomodoro Timer - Focus like a pro!")
todo_app = typer.Typer(help="Manage todo items")
app.add_typer(todo_app, name="todo")

console = Console(force_terminal=True)

# Global instances
DATA_DIR = Path(__file__).parent / "data"
storage = Storage(str(DATA_DIR))
todo_manager = TodoManager(storage)
timer_manager = TimerManager()
ui = PomodoroUI()


def on_timer_complete(timer):
    """Callback when a timer completes"""
    ui.print_timer_complete(timer)
    send_notification(
        "Pomodoro Complete!",
        f"'{timer.title}' finished! Time for a break."
    )
    # If timer has associated todo, mark it complete
    if timer.todo_id:
        todo = todo_manager.get(timer.todo_id)
        if todo and not todo.completed:
            todo_manager.complete(timer.todo_id)
            ui.print_info(f"Todo '{todo.title}' marked as complete")


async def handle_command(cmd: str) -> bool:
    """Handle interactive commands. Returns False to quit."""
    cmd = cmd.strip()
    if not cmd:
        return True

    parts = cmd.split(maxsplit=2)
    command = parts[0].lower()

    if command in ("quit", "q", "exit"):
        return False

    elif command == "help":
        console.print()
        console.print("[bold cyan]Available Commands:[/bold cyan]")
        console.print("  [green]add <minutes> [title][/green] - Add a new timer")
        console.print("  [green]todo <title>[/green]         - Add a new todo (asks for timer)")
        console.print("  [green]list[/green]                 - Show all todos")
        console.print("  [green]done <id>[/green]            - Mark todo as complete")
        console.print("  [green]del <id>[/green]             - Delete a todo or timer")
        console.print("  [green]pause <id>[/green]           - Pause a timer")
        console.print("  [green]resume <id>[/green]          - Resume a paused timer")
        console.print("  [green]clear[/green]                - Clear completed todos")
        console.print("  [green]quit / q[/green]             - Exit the application")
        console.print()

    elif command == "add":
        # Add a timer
        if len(parts) < 2:
            ui.print_error("Usage: add <minutes> [title]")
            return True

        try:
            minutes = int(parts[1])
            title = parts[2] if len(parts) > 2 else "Focus Session"

            timer = timer_manager.add_timer(title, minutes)
            timer_manager.start_timer(timer.id)
            ui.print_success(f"Timer '{title}' ({minutes}m) started [ID: {timer.id[:6]}]")
        except ValueError:
            ui.print_error("Minutes must be a number")

    elif command == "todo":
        # Add a todo
        if len(parts) < 2:
            ui.print_error("Usage: todo <title>")
            return True

        title = " ".join(parts[1:])

        # Ask if they want to create a timer
        console.print()
        want_timer = Confirm.ask("Create a timer for this todo?", default=True)

        if want_timer:
            minutes = IntPrompt.ask("Timer duration (minutes)", default=25)
            todo = todo_manager.add(title, timer_minutes=minutes)
            timer = timer_manager.add_timer(title, minutes, todo_id=todo.id)
            timer_manager.start_timer(timer.id)
            ui.print_success(f"Todo '{title}' created with {minutes}m timer [ID: {todo.id[:6]}]")
        else:
            todo = todo_manager.add(title)
            ui.print_success(f"Todo '{title}' created [ID: {todo.id[:6]}]")

    elif command == "list":
        # Show all todos
        console.print()
        todos = todo_manager.list_all()
        console.print(ui.create_todo_table(todos, show_completed=True))
        console.print()

    elif command == "done":
        # Mark todo as complete
        if len(parts) < 2:
            ui.print_error("Usage: done <id>")
            return True

        todo_id = parts[1]
        todo = todo_manager.complete(todo_id)
        if todo:
            ui.print_success(f"Todo '{todo.title}' marked as complete")
        else:
            ui.print_error(f"Todo with ID '{todo_id}' not found")

    elif command == "del":
        # Delete todo or timer
        if len(parts) < 2:
            ui.print_error("Usage: del <id>")
            return True

        item_id = parts[1]

        # Try to delete as timer first
        if timer_manager.remove_timer(item_id):
            ui.print_success(f"Timer removed")
        elif todo_manager.delete(item_id):
            ui.print_success(f"Todo deleted")
        else:
            ui.print_error(f"Item with ID '{item_id}' not found")

    elif command == "pause":
        if len(parts) < 2:
            ui.print_error("Usage: pause <id>")
            return True

        timer_id = parts[1]
        if timer_manager.pause_timer(timer_id):
            ui.print_success("Timer paused")
        else:
            ui.print_error(f"Timer with ID '{timer_id}' not found")

    elif command == "resume":
        if len(parts) < 2:
            ui.print_error("Usage: resume <id>")
            return True

        timer_id = parts[1]
        if timer_manager.resume_timer(timer_id):
            ui.print_success("Timer resumed")
        else:
            ui.print_error(f"Timer with ID '{timer_id}' not found")

    elif command == "clear":
        count = todo_manager.clear_completed()
        ui.print_success(f"Cleared {count} completed todo(s)")

    else:
        ui.print_error(f"Unknown command: {command}. Type 'help' for available commands.")

    return True


async def input_loop():
    """Async input loop that reads user commands"""
    loop = asyncio.get_event_loop()

    while True:
        try:
            # Read input in a thread to not block
            cmd = await loop.run_in_executor(None, lambda: input("> "))
            should_continue = await handle_command(cmd)
            if not should_continue:
                break
        except EOFError:
            break
        except KeyboardInterrupt:
            break


async def display_loop(live: Live):
    """Update the display periodically"""
    while True:
        display = ui.create_main_display(
            timer_manager.get_active_timers(),
            todo_manager.list_pending(),
        )
        live.update(display)
        await asyncio.sleep(0.5)


async def interactive_mode():
    """Run the interactive mode with live display and input"""
    ui.print_welcome()

    # Set up timer callbacks
    timer_manager.set_callbacks(on_complete=on_timer_complete)

    # Start any existing timers
    await timer_manager.start_all()

    console.print()
    console.print(ui.create_main_display(
        timer_manager.get_active_timers(),
        todo_manager.list_pending(),
    ))
    console.print()

    # Run input loop
    try:
        await input_loop()
    except KeyboardInterrupt:
        pass
    finally:
        timer_manager.stop_all()
        console.print("\n[bold yellow]Goodbye![/bold yellow]")


@app.command()
def start(
    minutes: int = typer.Argument(25, help="Duration in minutes (default: 25)"),
    title: str = typer.Option("Focus Session", "--title", "-t", help="Session title"),
):
    """Start a single pomodoro timer (classic mode)."""
    if minutes <= 0:
        console.print("[bold red]Error:[/bold red] Duration must be positive!")
        raise typer.Exit(1)

    timer = timer_manager.add_timer(title, minutes)
    timer_manager.set_callbacks(on_complete=on_timer_complete)

    console.clear()
    console.print(f"\n{SYMBOLS['tomato']} Starting timer: [bold]{title}[/bold] ({minutes} minutes)")
    console.print("[dim]Press Ctrl+C to cancel[/dim]\n")

    async def run_single_timer():
        timer_manager.start_timer(timer.id)
        while not timer.is_complete:
            console.print(
                f"\r{SYMBOLS['tomato']} {timer.format_remaining()} remaining...  ",
                end=""
            )
            await asyncio.sleep(1)
        console.print()

    try:
        asyncio.run(run_single_timer())
    except KeyboardInterrupt:
        console.print("\n[bold yellow]Timer cancelled.[/bold yellow]")


@app.command(name="run")
def run_interactive():
    """Start interactive mode with multiple timers and todos."""
    asyncio.run(interactive_mode())


# Todo subcommands
@todo_app.command("add")
def todo_add(
    title: str = typer.Argument(..., help="Todo title"),
    timer: Optional[int] = typer.Option(None, "--timer", "-t", help="Associated timer in minutes"),
):
    """Add a new todo item."""
    if timer:
        todo = todo_manager.add(title, timer_minutes=timer)
        ui.print_success(f"Todo '{title}' created with {timer}m timer [ID: {todo.id[:6]}]")

        # Ask if they want to start the timer now
        if Confirm.ask("Start the timer now?", default=True):
            new_timer = timer_manager.add_timer(title, timer, todo_id=todo.id)
            timer_manager.set_callbacks(on_complete=on_timer_complete)

            async def run_timer():
                timer_manager.start_timer(new_timer.id)
                while not new_timer.is_complete:
                    console.print(
                        f"\r{SYMBOLS['tomato']} {new_timer.format_remaining()} remaining...  ",
                        end=""
                    )
                    await asyncio.sleep(1)
                console.print()

            try:
                asyncio.run(run_timer())
            except KeyboardInterrupt:
                console.print("\n[bold yellow]Timer cancelled.[/bold yellow]")
    else:
        todo = todo_manager.add(title)
        ui.print_success(f"Todo '{title}' created [ID: {todo.id[:6]}]")


@todo_app.command("list")
def todo_list(
    all: bool = typer.Option(False, "--all", "-a", help="Show all todos including completed"),
):
    """List all todos."""
    todos = todo_manager.list_all()
    console.print()
    console.print(ui.create_todo_table(todos, show_completed=all))
    console.print()

    counts = todo_manager.count()
    console.print(f"[dim]Total: {counts['total']} | Pending: {counts['pending']} | Completed: {counts['completed']}[/dim]")


@todo_app.command("done")
def todo_done(
    todo_id: str = typer.Argument(..., help="Todo ID to mark as complete"),
):
    """Mark a todo as complete."""
    todo = todo_manager.complete(todo_id)
    if todo:
        ui.print_success(f"Todo '{todo.title}' marked as complete")
    else:
        ui.print_error(f"Todo with ID '{todo_id}' not found")


@todo_app.command("delete")
def todo_delete(
    todo_id: str = typer.Argument(..., help="Todo ID to delete"),
):
    """Delete a todo."""
    if todo_manager.delete(todo_id):
        ui.print_success("Todo deleted")
    else:
        ui.print_error(f"Todo with ID '{todo_id}' not found")


@todo_app.command("clear")
def todo_clear():
    """Clear all completed todos."""
    count = todo_manager.clear_completed()
    ui.print_success(f"Cleared {count} completed todo(s)")


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """
    CLI Pomodoro Timer

    A beautiful command-line pomodoro timer with Rich progress bar.
    Supports multiple parallel timers and todo management.
    """
    if ctx.invoked_subcommand is None:
        # Default to interactive mode
        asyncio.run(interactive_mode())


if __name__ == "__main__":
    app()
