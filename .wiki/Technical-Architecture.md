# PyTaskTracker - Technical Architecture

## 🎯 Summary

PyTaskTracker is a layered Python application comprising an **Entry Point / CLI**, a **Service Layer**, a **Persistence Layer**, and two optional interface modules — a **REST API** (FastAPI) and a **GUI** (NiceGUI). All state is stored in an embedded DuckDB database accessed through SQLModel / SQLAlchemy.

---

## 🏗️ Component Diagram

```mermaid
graph TD
    subgraph Client["Client Layer"]
        Browser["Browser\n(NiceGUI)"]
        HTTPClient["HTTP Client\n(REST)"]
        Terminal["Terminal\n(CLI)"]
    end

    subgraph Entry["Entry Point"]
        MainPy["main.py\nCLI / Application Boot"]
    end

    subgraph Interfaces["Interface Modules (src/mods/)"]
        GuiAPI["gui_api.py\nNiceGUI Pages & Dialogs"]
        RestAPI["rest_api.py\nFastAPI Routes"]
    end

    subgraph Core["Core (src/)"]
        Services["services.py\nBusiness Logic"]
        Persistence["persistence.py\nDatabase Access Layer"]
        Models["models.py\nSQLModel ORM Models"]
        DtUtils["datetime_utilities.py\nDate/Time Helpers"]
        LogCfg["logging_config.py\nStructured JSON Logging"]
    end

    subgraph DB["Database"]
        DuckDB[("DuckDB\n(file or :memory:)")]
    end

    Browser --> GuiAPI
    HTTPClient --> RestAPI
    Terminal --> MainPy
    MainPy --> GuiAPI
    MainPy --> RestAPI
    GuiAPI --> Services
    RestAPI --> Services
    Services --> Persistence
    Services --> DtUtils
    Persistence --> Models
    Persistence --> DuckDB
    Models --> DtUtils
    GuiAPI --> LogCfg
    RestAPI --> LogCfg
    Services --> LogCfg
    Persistence --> LogCfg
```

---

## 🔌 REST API Endpoint Map

```mermaid
graph LR
    subgraph TaskGroups["/task_groups"]
        TG1["GET /task_groups\nVisible groups"]
        TG2["GET /task_groups/all\nAll groups"]
        TG3["POST /task_groups\nCreate"]
        TG4["PUT /task_groups\nUpdate"]
        TG5["PATCH /task_groups/{id}\nSoft-delete"]
        TG6["PATCH /task_groups/{id}/enable\nRestore"]
    end

    subgraph Tasks["/tasks"]
        T1["GET /tasks\nVisible tasks"]
        T2["GET /tasks/all\nAll tasks"]
        T3["POST /tasks\nCreate"]
        T4["PUT /tasks\nUpdate"]
        T5["PATCH /tasks/{id}\nSoft-delete"]
        T6["PATCH /tasks/{id}/enable\nRestore"]
    end

    subgraph Activities["/activities"]
        A1["GET /activities\nAll activities"]
        A2["GET /activities/filtered\nDate-range query"]
        A3["POST /activities\nStart activity"]
        A4["PUT /activities\nUpdate activity"]
        A5["PATCH /activities/{id}/end\nEnd activity"]
    end
```

---

## ⚙️ Application Startup Flow

```mermaid
sequenceDiagram
    participant User
    participant CLI as main.py (CLI)
    participant Env as Environment
    participant UVI as Uvicorn / NiceGUI
    participant SVC as Services
    participant DB as DuckDB

    User->>CLI: python main.py [options]
    CLI->>Env: Set DATABASE_URL, RECREATE_DB env vars
    CLI->>SVC: Instantiate Services(database_url, recreate)
    SVC->>DB: create_engine(database_url)
    alt recreate=True
        SVC->>DB: drop_all tables
    end
    SVC->>DB: create_all tables
    alt mode=rest
        CLI->>UVI: uvicorn.run(app, port)
    else mode=gui
        CLI->>UVI: GuiApp.start_gui(port)
    end
```

---

## 🔒 Error Handling Strategy

| Scenario | Handler | HTTP Status |
|---|---|---|
| Duplicate / constraint violation | `@app.exception_handler(IntegrityError)` | 400 |
| Application-level error | `@app.exception_handler(BaseAppException)` | Configurable (default 400) |
| Task not found on update | Inline raise `BaseAppException` | 404 |
| All other exceptions | `@app.exception_handler(Exception)` | 400 |

---

## 🛠️ Technology Stack

| Concern | Technology |
|---|---|
| Language | Python 3.12+ |
| ORM / Models | SQLModel + Pydantic v2 |
| Database | DuckDB (embedded) |
| REST Framework | FastAPI + Uvicorn |
| GUI Framework | NiceGUI |
| CLI Framework | Click + dataclass-click |
| Type Checking | ty (Astral) |
| Logging | Loguru (JSON, rotating) |
| Package Manager | uv |
| Testing | pytest |
