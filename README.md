# CLI Pomodoro Timer

A beautiful command-line pomodoro timer with Rich progress bar, multiple parallel timers, and todo management.

## Features

- **Multiple Parallel Timers** - Run multiple countdown timers simultaneously
- **Todo Management** - Create, complete, and track todo items with persistence
- **Timer-Todo Association** - Link timers to todos for automatic completion
- **Beautiful UI** - Rich progress bars, tables, and colored output
- **System Notifications** - Desktop notifications when timers complete
- **Data Persistence** - Todos saved to JSON file automatically
- **Cross-Platform** - Works on Windows, macOS, and Linux

## Tech Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| CLI Framework | [Typer](https://typer.tiangolo.com/) | Command-line interface and argument parsing |
| Terminal UI | [Rich](https://rich.readthedocs.io/) | Progress bars, tables, panels, and styled output |
| Notifications | [Plyer](https://plyer.readthedocs.io/) | Cross-platform desktop notifications |
| Async Runtime | asyncio | Parallel timer execution |
| Data Storage | JSON | Todo persistence |
| Language | Python 3.9+ | Core implementation |

## Project Structure

```
cli-pomodoro/
├── pomodoro.py    # Main entry point and CLI commands
├── storage.py     # Data models (Todo, Timer) and JSON persistence
├── todo.py        # TodoManager for CRUD operations
├── timer.py       # Async TimerManager for parallel timers
├── ui.py          # Rich UI components
├── data/
│   └── todos.json # Persisted todo data
├── pyproject.toml # Project configuration
└── README.md
```

## Installation

```bash
# Clone the repository
git clone https://github.com/Cluelessthx/cli-pomodoro.git
cd cli-pomodoro

# Install dependencies
pip install rich typer plyer
```

## Usage

### Interactive Mode (Recommended)

Start the interactive mode for full functionality with multiple timers:

```bash
python pomodoro.py
# or
python pomodoro.py run
```

#### Interactive Commands

| Command | Description |
|---------|-------------|
| `add <minutes> [title]` | Add and start a new timer |
| `todo <title>` | Add a todo (prompts for timer association) |
| `list` | Show all todos |
| `done <id>` | Mark a todo as complete |
| `del <id>` | Delete a todo or timer |
| `pause <id>` | Pause a running timer |
| `resume <id>` | Resume a paused timer |
| `clear` | Remove all completed todos |
| `help` | Show available commands |
| `quit` / `q` | Exit the application |

### Classic Single Timer Mode

```bash
# Start a 25-minute timer (default)
python pomodoro.py start

# Start a custom duration timer
python pomodoro.py start 30

# Start with a custom title
python pomodoro.py start 25 --title "Deep Work"
```

### Todo Commands

```bash
# Add a todo
python pomodoro.py todo add "Write documentation"

# Add a todo with an associated timer
python pomodoro.py todo add "Code review" --timer 25

# List pending todos
python pomodoro.py todo list

# List all todos (including completed)
python pomodoro.py todo list --all

# Mark a todo as complete
python pomodoro.py todo done <id>

# Delete a todo
python pomodoro.py todo delete <id>

# Clear all completed todos
python pomodoro.py todo clear
```

## Screenshots

### Timer Display
```
                               <*> Active Timers
┌──────────┬───────────────┬───────────────────────────┬──────────┬───────────┐
│ ID       │ Title         │         Progress          │     Time │  Status   │
├──────────┼───────────────┼───────────────────────────┼──────────┼───────────┤
│ abc123   │ Focus Session │   ========............    │    15:00 │  RUNNING  │
│ def456   │ Code Review   │   ===.................    │    22:30 │  RUNNING  │
└──────────┴───────────────┴───────────────────────────┴──────────┴───────────┘
```

### Todo List
```
                                 Pending Todos
┌──────────────┬──────────┬─────────────────────────────┬──────────────────────┐
│ ID           │  Status  │ Title                       │        Timer         │
├──────────────┼──────────┼─────────────────────────────┼──────────────────────┤
│ a1b2c3       │   [ ]    │ Write documentation         │         25m          │
│ d4e5f6       │   [v]    │ Review PR #123              │          -           │
└──────────────┴──────────┴─────────────────────────────┴──────────────────────┘
```

## Architecture

### Data Flow

```
User Input
    │
    ▼
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  pomodoro   │────▶│ TimerManager │────▶│     UI      │
│    .py      │     │  (async)     │     │   (Rich)    │
└─────────────┘     └──────────────┘     └─────────────┘
    │                                           │
    ▼                                           ▼
┌─────────────┐     ┌──────────────┐     Terminal Output
│ TodoManager │────▶│   Storage    │
└─────────────┘     │   (JSON)     │
                    └──────────────┘
```

### Key Design Decisions

- **Async Architecture**: Uses `asyncio` for non-blocking parallel timer execution
- **Modular Design**: Separated concerns into storage, timer, todo, and UI modules
- **Rich Integration**: Leverages Rich library for beautiful terminal output
- **JSON Persistence**: Simple file-based storage without external database dependencies

## Configuration

Default settings are defined in the code:

| Setting | Default | Description |
|---------|---------|-------------|
| Default timer duration | 25 minutes | Standard Pomodoro length |
| Data directory | `./data/` | Location for JSON storage |
| Notification timeout | 10 seconds | Desktop notification duration |

## Requirements

- Python 3.9+
- rich >= 13.0.0
- typer >= 0.9.0
- plyer >= 2.1.0

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
