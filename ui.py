"""
UI module - Rich UI components for terminal display
"""

import sys
import os

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    os.system("")  # Enable ANSI escape sequences

from typing import List, Optional
from rich.console import Console, Group
from rich.table import Table
from rich.panel import Panel
from rich.progress import (
    Progress,
    BarColumn,
    TextColumn,
    TimeRemainingColumn,
    TaskProgressColumn,
    SpinnerColumn,
)
from rich.layout import Layout
from rich.align import Align
from rich.text import Text
from rich.live import Live

from storage import Timer, Todo


# ASCII symbols for cross-platform compatibility
SYMBOLS = {
    "tomato": "[red]<*>[/red]",
    "clock": "[yellow][@][/yellow]",
    "fire": "[red](!)[/red]",
    "check": "[green][v][/green]",
    "bell": "[yellow][!][/yellow]",
    "coffee": "[yellow]c[_][/yellow]",
    "party": "[magenta]***[/magenta]",
    "box_empty": "[ ]",
    "box_checked": "[green]\\[v][/green]",
    "arrow": "->",
}


class PomodoroUI:
    """Rich UI components for the pomodoro application"""

    def __init__(self):
        self.console = Console(force_terminal=True)

    def create_timer_table(self, timers: List[Timer]) -> Table:
        """Create a table displaying all active timers"""
        table = Table(
            title=f"{SYMBOLS['tomato']} Active Timers",
            show_header=True,
            header_style="bold cyan",
            border_style="red",
            expand=True,
        )

        table.add_column("ID", style="dim", width=8)
        table.add_column("Title", style="bold")
        table.add_column("Progress", justify="center", width=25)
        table.add_column("Time", justify="right", width=8)
        table.add_column("Status", justify="center", width=12)

        if not timers:
            table.add_row(
                "-", "[dim]No active timers[/dim]", "-", "-", "-"
            )
        else:
            for timer in timers:
                # Create progress bar
                progress_pct = timer.progress * 100
                bar_width = 20
                filled = int(bar_width * timer.progress)
                empty = bar_width - filled
                progress_bar = f"[red]{'=' * filled}[/red][dim]{'.' * empty}[/dim]"

                # Status indicator
                if timer.paused:
                    status = "[yellow]PAUSED[/yellow]"
                elif timer.remaining_seconds <= 10:
                    status = f"{SYMBOLS['clock']} [blink]ENDING[/blink]"
                elif timer.remaining_seconds <= 60:
                    status = f"{SYMBOLS['fire']} FINAL"
                else:
                    status = "[green]RUNNING[/green]"

                table.add_row(
                    timer.id[:6],
                    timer.title,
                    progress_bar,
                    timer.format_remaining(),
                    status,
                )

        return table

    def create_todo_table(self, todos: List[Todo], show_completed: bool = False) -> Table:
        """Create a table displaying todos"""
        title = "Pending Todos" if not show_completed else "All Todos"
        table = Table(
            title=title,
            show_header=True,
            header_style="bold cyan",
            border_style="blue",
            expand=True,
        )

        table.add_column("ID", style="dim", width=8)
        table.add_column("Status", justify="center", width=5)
        table.add_column("Title", style="bold")
        table.add_column("Timer", justify="center", width=8)

        display_todos = todos if show_completed else [t for t in todos if not t.completed]

        if not display_todos:
            table.add_row(
                "-", "-", "[dim]No todos[/dim]", "-"
            )
        else:
            for todo in display_todos:
                status = SYMBOLS["box_checked"] if todo.completed else SYMBOLS["box_empty"]
                title_style = "[dim strike]" if todo.completed else ""
                title_end = "[/dim strike]" if todo.completed else ""
                timer_info = f"{todo.timer_minutes}m" if todo.timer_minutes else "-"

                table.add_row(
                    todo.id[:6],
                    status,
                    f"{title_style}{todo.title}{title_end}",
                    timer_info,
                )

        return table

    def create_help_panel(self) -> Panel:
        """Create a help panel showing available commands"""
        help_text = Text()
        help_text.append("Commands: ", style="bold cyan")
        help_text.append("add <min> [title] ", style="green")
        help_text.append("| ", style="dim")
        help_text.append("todo <title> ", style="green")
        help_text.append("| ", style="dim")
        help_text.append("list ", style="green")
        help_text.append("| ", style="dim")
        help_text.append("done <id> ", style="green")
        help_text.append("| ", style="dim")
        help_text.append("del <id> ", style="green")
        help_text.append("| ", style="dim")
        help_text.append("quit", style="red")

        return Panel(
            Align.center(help_text),
            border_style="dim",
            padding=(0, 1),
        )

    def create_main_display(
        self,
        timers: List[Timer],
        todos: List[Todo],
    ) -> Group:
        """Create the main display combining timers and todos"""
        timer_table = self.create_timer_table(timers)
        todo_table = self.create_todo_table(todos)
        help_panel = self.create_help_panel()

        return Group(
            timer_table,
            "",
            todo_table,
            "",
            help_panel,
        )

    def print_welcome(self) -> None:
        """Print welcome message"""
        self.console.clear()
        self.console.print(Panel(
            Align.center(
                f"[bold red]{SYMBOLS['tomato']} CLI Pomodoro Timer[/bold red]\n\n"
                "[cyan]Interactive Mode[/cyan]\n"
                "[dim]Type 'help' for commands, 'quit' to exit[/dim]"
            ),
            border_style="red",
        ))
        self.console.print()

    def print_timer_complete(self, timer: Timer) -> None:
        """Print timer completion message"""
        self.console.print()
        self.console.print(Panel(
            Align.center(
                f"[bold green]{SYMBOLS['party']} Timer Complete! {SYMBOLS['party']}[/bold green]\n\n"
                f"[cyan]Session:[/cyan] {timer.title}\n"
                f"[cyan]Duration:[/cyan] {timer.total_seconds // 60} minutes\n\n"
                f"[bold yellow]Great work! Take a break! {SYMBOLS['coffee']}[/bold yellow]"
            ),
            title="[bold green]Complete[/bold green]",
            border_style="green",
        ))

    def print_error(self, message: str) -> None:
        """Print error message"""
        self.console.print(f"[bold red]Error:[/bold red] {message}")

    def print_success(self, message: str) -> None:
        """Print success message"""
        self.console.print(f"[bold green]{SYMBOLS['check']}[/bold green] {message}")

    def print_info(self, message: str) -> None:
        """Print info message"""
        self.console.print(f"[cyan]{SYMBOLS['arrow']}[/cyan] {message}")


def send_notification(title: str, message: str) -> None:
    """Send system notification when timer completes"""
    try:
        from plyer import notification
        notification.notify(
            title=title,
            message=message,
            app_name="Pomodoro Timer",
            timeout=10,
        )
    except Exception:
        # Silently fail if notification doesn't work
        pass
