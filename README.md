<!--
 Copyright 2026 James G Willmore

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

     https://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
-->

# PyTaskTracker

A task and activity tracking application with three operation modes: a web-based GUI, a REST API, and a CLI. Built on DuckDB, SQLModel, FastAPI, and NiceGUI.

## Documentation

Full API documentation is available at **<a href="[https://example.com](https://willmorejg.github.io/pytasktracker/)" target="_blank" rel="noopener noreferrer">willmorejg.github.io/pytasktracker</a>**.


## Features

- Organize work into **Task Groups** and **Tasks**
- Track **Activities** (work sessions) against tasks with automatic elapsed-time calculation displayed as `HH:MM:SS`
- Edit activity start and end times via an in-GUI date/time picker
- Soft-delete and restore task groups and tasks
- Three runtime modes: GUI, REST API, CLI
- Embedded DuckDB database — no separate database server required
- All dates and times stored and displayed in local time

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

## Installation

```bash
git clone https://github.com/willmorejg/pytasktracker.git
cd pytasktracker
uv sync
```

## Running

```bash
# Web GUI (default, port 8088)
python main.py

# REST API
python main.py --mode rest --port 8089

# CLI
python main.py --mode cli
```

### Options

| Option | Default | Description |
| --- | --- | --- |
| `--mode` | `gui` | Runtime mode: `gui`, `rest`, or `cli` |
| `--port` | `8088` | Port to bind to |
| `--database-url` | `duckdb:///:memory:` | SQLAlchemy database URL |
| `--recreate-db` | `False` | Drop and recreate tables on startup |

To use a persistent database file:

```bash
python main.py --database-url "duckdb:///./pytasktracker.db"
```

## REST API

When running in `rest` mode, the API is available at `http://localhost:<port>/api/`.

### Task Groups

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/api/task_groups` | List visible task groups |
| `GET` | `/api/task_groups/all` | List all task groups |
| `POST` | `/api/task_groups` | Create a task group |
| `PUT` | `/api/task_groups` | Update a task group |
| `PATCH` | `/api/task_groups/{id}` | Soft-delete a task group |
| `PATCH` | `/api/task_groups/{id}/enable` | Restore a task group |

### Tasks

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/api/tasks` | List visible tasks |
| `GET` | `/api/tasks/all` | List all tasks |
| `POST` | `/api/tasks` | Create a task |
| `PUT` | `/api/tasks` | Update a task |
| `PATCH` | `/api/tasks/{id}` | Soft-delete a task |
| `PATCH` | `/api/tasks/{id}/enable` | Restore a task |

### Activities

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/api/activities` | List all activities (includes `elapsed_hms`) |
| `POST` | `/api/activities` | Start a new activity |
| `PUT` | `/api/activities` | Update an activity |
| `PATCH` | `/api/activities/{id}/end` | End an activity (calculates elapsed time) |

API response schema (`GET /api/activities`):

```json
[
    {
        "id": "string",
        "group": "string",
        "task": "string",
        "started": "string | null", 
        "ended": "string | null",
        "elapsed_hms": "string | null",
        "description": "string | null"
    }
]
```

Example `GET /api/activities` response item:

```json
[
    {
        "id": "2f153858-fb39-4ac8-95a2-f5ee8217f7f3",
        "group": "Development",
        "task": "Implement API",
        "started": "2026-03-01T10:00:00",
        "ended": "2026-03-01T10:25:30",
        "elapsed_hms": "00:25:30",
        "description": "Initial implementation"
    }
]
```

Interactive API docs are available at `http://localhost:<port>/docs`.

## Project Structure

```text
pytasktracker/
├── main.py                 # Entry point and CLI options
├── src/
│   ├── models.py           # SQLModel ORM models (TaskGroup, Task, Activity)
│   ├── services.py         # Business logic layer
│   ├── persistence.py      # Database access layer
│   ├── datetime_utilities.py  # get_current_time(), build_datetime()
│   ├── logging_config.py
│   └── mods/
│       ├── rest_api.py     # FastAPI routes
│       └── gui_api.py      # NiceGUI web interface
├── tests/
│   ├── test_persistence.py
│   ├── test_services.py
│   └── test_rest_api.py
├── docs/                   # Sphinx documentation source
├── logs/                   # Rotating JSON log files
└── rest.http               # Example HTTP requests
```

## Data Model

```text
TaskGroup
└── Task (many per group)
    └── Activity (many per task)
        ├── started    (datetime, set on creation)
        ├── ended      (datetime, set on end)
        ├── elapsed    (int seconds, persisted, calculated on save)
        └── elapsed_hms (string HH:MM:SS, computed, not persisted)
```

All entities carry `created_at` / `updated_at` timestamps. TaskGroups and Tasks support soft-delete via a `show` boolean flag.

## Testing

```bash
# Run all tests
pytest tests/

# With coverage
pytest tests/ --cov=src
```

## Type Checking

The project uses [ty](https://docs.astral.sh/ty/) for static type checking (configured in `pyproject.toml` under `[tool.ty]`).

```bash
uv run ty check
```

## Logging

Logs are written to `logs/pytasktracker.log` in JSON format with weekly rotation (4-week retention, ZIP compressed). INFO-level logs are also printed to stdout.

## License

Apache License 2.0 — see [LICENSE](https://www.apache.org/licenses/LICENSE-2.0) for details.
