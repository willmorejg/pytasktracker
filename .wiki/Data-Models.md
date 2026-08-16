# PyTaskTracker - Data Models

## 🎯 Summary

PyTaskTracker uses three database entities — **TaskGroup**, **Task**, and **Activity** — together with three reusable mixins that add audit timestamps, soft-delete capability, and elapsed-time tracking.

---

## 🗂️ Entity Relationship Diagram

```mermaid
erDiagram
    TASKGROUP {
        string id PK "UUID v4"
        string name "unique, indexed"
        string description "nullable"
        datetime created_at "server default NOW"
        datetime updated_at "nullable, auto-updated"
        bool show "default true (soft-delete flag)"
    }

    TASK {
        string id PK "UUID v4"
        string name "unique, indexed"
        string description "nullable"
        string group_id FK "→ TASKGROUP.id"
        datetime created_at "server default NOW"
        datetime updated_at "nullable, auto-updated"
        bool show "default true (soft-delete flag)"
    }

    ACTIVITY {
        string id PK "UUID v4"
        string group_id FK "→ TASKGROUP.id"
        string task_id FK "→ TASK.id"
        string description "nullable"
        datetime started "server default NOW"
        datetime ended "nullable"
        int elapsed "seconds, computed on save, nullable"
    }

    TASKGROUP ||--o{ TASK : "has"
    TASK ||--o{ ACTIVITY : "has"
    TASKGROUP ||--o{ ACTIVITY : "references"
```

---

## 🏛️ Class Diagram

```mermaid
classDiagram
    class TimestampMixin {
        +datetime|None created_at
        +datetime|None updated_at
    }

    class SoftDeleteMixin {
        +bool show
    }

    class ElapsedTimeMixin {
        +datetime|None started
        +datetime|None ended
        +int|None elapsed
        +str|None elapsed_hms()
    }

    class TaskGroup {
        +str id
        +str name
        +str|None description
    }

    class Task {
        +str id
        +str name
        +str|None description
        +str group_id
    }

    class Activity {
        +str id
        +str group_id
        +str task_id
        +str|None description
    }

    class TaskDisplay {
        +str id
        +str name
        +str|None description
        +str group_id
        +str group
        +bool show
    }

    class ActivityDisplay {
        +str id
        +str group
        +str task
        +str|None started
        +str|None ended
        +str|None elapsed_hms
        +str|None description
    }

    TimestampMixin <|-- TaskGroup
    SoftDeleteMixin <|-- TaskGroup
    TimestampMixin <|-- Task
    SoftDeleteMixin <|-- Task
    ElapsedTimeMixin <|-- Activity
    TaskGroup "1" --> "0..*" Task : group_id
    Task "1" --> "0..*" Activity : task_id
    TaskGroup "1" --> "0..*" Activity : group_id
    Task ..> TaskDisplay : projected to
    Activity ..> ActivityDisplay : projected to
```

---

## 📐 Mixin Reference

| Mixin | Fields Added | Purpose |
|---|---|---|
| `TimestampMixin` | `created_at`, `updated_at` | Audit trail for all entities |
| `SoftDeleteMixin` | `show` (bool, default `True`) | Non-destructive hide/restore pattern |
| `ElapsedTimeMixin` | `started`, `ended`, `elapsed` (int seconds), `elapsed_hms` (computed `HH:MM:SS`) | Time-tracking lifecycle for Activities |

---

## 📦 Display / Projection Models

These are **read-only response shapes** used by the REST API — they are **not** persisted.

### `TaskDisplay`
Flattens `Task` + `TaskGroup` into a single response object, adding the `group` name as a string.

### `ActivityDisplay`
Flattens `Activity` + `Task` + `TaskGroup` into a single response object, serialising datetime fields as ISO-8601 strings and exposing `elapsed_hms`.

---

## 🔑 Key Design Decisions

| Decision | Rationale |
|---|---|
| UUID v4 primary keys | Avoids auto-increment conflicts; supports distributed or merged datasets |
| `show` soft-delete flag | Preserves historical integrity; deleted items can be restored without data loss |
| `elapsed` stored as integer seconds | Enables arithmetic queries (sum, average) directly in SQL without datetime subtraction |
| `elapsed_hms` as a computed Pydantic field | Human-readable format kept out of the DB to avoid staleness |
| `group_id` denormalised onto `Activity` | Allows single-join group-level activity queries without chaining through `Task` |
| DuckDB embedded database | Zero infrastructure dependency; file or in-memory modes support both production and testing |
