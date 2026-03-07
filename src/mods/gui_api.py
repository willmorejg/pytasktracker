# Copyright 2026 James G Willmore
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""GUI API module for handling GUI-related requests and responses."""

from datetime import datetime

from fastapi.responses import JSONResponse
from nicegui import app, ui

from logging_config import configure_logging
from mods import rest_api

logger = configure_logging()

_PAGE_COLUMN_CLASSES = "items-center w-full"
_PAGE_HEADING_CLASSES = "text-2xl font-bold mb-4"


def _build_datetime(
    date_input,
    time_input,
    result_label,
) -> datetime | None:
    """Combine date and time inputs into a single datetime object."""
    try:
        combined_datetime_str = f"{date_input.value} {time_input.value}"
        combined_datetime_obj = datetime.strptime(
            combined_datetime_str, "%Y-%m-%d %H:%M"
        )
        result_label.set_text(
            f"Selected Datetime: {combined_datetime_obj.isoformat(sep=' ')}"
        )
        return combined_datetime_obj
    except ValueError:
        result_label.set_text("Invalid date/time combination")
        return None


@app.get("/.well-known/appspecific/com.chrome.devtools.json", include_in_schema=False)
async def chrome_devtools_json() -> JSONResponse:
    """Satisfy Chrome's DevTools discovery probe so it never reaches the 404 handler."""
    return JSONResponse({})


async def datetime_component():
    """Show a datetime picker dialog and return the selected datetime."""
    return await pick_datetime_dialog(title="Select Date and Time")


async def pick_datetime_dialog(
    title: str,
    initial_value: datetime | None = None,
) -> datetime | None:
    """Show a date+time picker and return a datetime when submitted."""
    initial = initial_value or datetime.now()
    initial_date = initial.strftime("%Y-%m-%d")
    initial_time = initial.strftime("%H:%M")

    with ui.dialog() as dialog, ui.card():
        ui.label(title).classes("text-lg")
        date_input = ui.date_input("Date", value=initial_date)
        time_input = ui.time_input("Time", value=initial_time)
        result_label = ui.label()

        def submit_datetime():
            selected_datetime = _build_datetime(date_input, time_input, result_label)
            if selected_datetime is None:
                return
            dialog.submit(selected_datetime)

        date_input.on(
            "change", lambda _e: _build_datetime(date_input, time_input, result_label)
        )
        time_input.on(
            "change", lambda _e: _build_datetime(date_input, time_input, result_label)
        )
        _build_datetime(date_input, time_input, result_label)

        with ui.row().classes("justify-end w-full"):
            ui.button("Cancel", color="red", on_click=lambda: dialog.submit(None))
            ui.button("Submit", color="green", on_click=submit_datetime)

    dialog.open()
    result = await dialog
    return result if isinstance(result, datetime) else None


async def confirm_action_dialog(
    title: str,
    message: str,
    confirm_text: str = "Confirm",
    cancel_text: str = "Cancel",
) -> bool:
    """Show a reusable confirmation dialog and return True when confirmed."""
    with ui.dialog() as dialog, ui.card():
        ui.label(title).classes("text-lg")
        ui.label(message)
        with ui.row().classes("justify-end w-full"):
            ui.button(cancel_text, color="red", on_click=lambda: dialog.submit(False))
            ui.button(confirm_text, color="green", on_click=lambda: dialog.submit(True))

    dialog.open()
    return bool(await dialog)


def get_activity_id_from_event(e) -> str | None:
    """Extract an activity id from an event argument payload."""
    activity_id = e.args if isinstance(e.args, str) else None
    if activity_id is None:
        ui.notify("Unable to determine selected activity", type="negative")
    return activity_id


def get_activity_with_refs_or_notify(activity_id: str):
    """Get activity tuple (activity, task, group) or show a notification."""
    activity_with_refs = rest_api.service.get_activity_by_id(activity_id)
    if activity_with_refs is None:
        ui.notify("Activity not found", type="negative")
    return activity_with_refs


async def end_activity_handler(e):
    """Handle ending an activity from the activities table."""
    activity_id = get_activity_id_from_event(e)
    if activity_id is None:
        return

    activity_with_refs = get_activity_with_refs_or_notify(activity_id)
    if activity_with_refs is None:
        return

    activity = activity_with_refs[0]
    task = activity_with_refs[1]
    confirmed = await confirm_action_dialog(
        title="Confirm End Activity",
        message=f"Are you sure you want to end activity '{task.name}'?",
        confirm_text="Yes",
        cancel_text="No",
    )
    if not confirmed:
        return

    rest_api.service.end_activity_by_id(activity_id=activity.id)
    ui.notify("Activity ended")
    ui.navigate.reload()


async def edit_activity_datetime_handler(e, field_name: str):
    """Handle editing started/ended datetime for an activity row."""
    activity_id = get_activity_id_from_event(e)
    if activity_id is None:
        return

    activity_with_refs = get_activity_with_refs_or_notify(activity_id)
    if activity_with_refs is None:
        return

    activity = activity_with_refs[0]
    task = activity_with_refs[1]
    current_value = getattr(activity, field_name)
    selected_datetime = await pick_datetime_dialog(
        title=f"Edit {field_name.capitalize()} for '{task.name}'",
        initial_value=current_value,
    )
    if selected_datetime is None:
        return

    confirmed = await confirm_action_dialog(
        title="Confirm Datetime Change",
        message=(
            f"Update {field_name} for activity '{task.name}' to "
            f"'{selected_datetime.isoformat(sep=' ')}'?"
        ),
        confirm_text="Yes",
        cancel_text="No",
    )
    if not confirmed:
        return

    setattr(activity, field_name, selected_datetime)
    rest_api.service.modify_activity(activity)
    ui.notify(f"Activity {field_name} updated")
    ui.navigate.reload()


async def edit_started_handler(e):
    """Handle editing activity started datetime."""
    await edit_activity_datetime_handler(e, "started")


async def edit_ended_handler(e):
    """Handle editing activity ended datetime."""
    await edit_activity_datetime_handler(e, "ended")


def format_elapsed_hms(total_seconds: int) -> str:
    """Format elapsed seconds as HH:MM:SS."""
    sign = "-" if total_seconds < 0 else ""
    hours, remainder = divmod(abs(total_seconds), 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{sign}{hours:02d}:{minutes:02d}:{seconds:02d}"


def parse_filter_datetime(
    date_value: str | None,
    time_value: str | None,
    label: str,
) -> tuple[datetime | None, bool]:
    """Parse date/time filter input and return datetime with exactness flag."""
    if not date_value:
        ui.notify(f"{label} date is required", type="negative")
        return None, False

    clean_time = (time_value or "").strip()
    if clean_time:
        try:
            return (
                datetime.strptime(f"{date_value} {clean_time}", "%Y-%m-%d %H:%M"),
                True,
            )
        except ValueError:
            ui.notify(
                f"Invalid {label.lower()} time format. Use HH:MM.",
                type="negative",
            )
            return None, False

    return datetime.strptime(date_value, "%Y-%m-%d"), False


def build_activity_rows(
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    exact_start: bool = False,
    exact_end: bool = False,
) -> list[dict]:
    """Build activities rows and append an elapsed total summary row."""
    activity_rows: list[dict] = []
    total_elapsed_seconds = 0
    for activity, task, task_group in rest_api.service.get_filtered_activities(
        start_date=start_date,
        end_date=end_date,
        exact_start=exact_start,
        exact_end=exact_end,
    ):
        elapsed_seconds = activity.elapsed or 0
        total_elapsed_seconds += elapsed_seconds
        activity_rows.append(
            {
                "id": activity.id,
                "group": task_group.name,
                "task": task.name,
                "started": activity.started,
                "ended": activity.ended,
                "elapsed_hms": activity.elapsed_hms,
                "is_summary": False,
            }
        )

    activity_rows.append(
        {
            "id": "__summary__",
            "group": "",
            "task": "Total",
            "started": "",
            "ended": "",
            "elapsed_hms": format_elapsed_hms(total_elapsed_seconds),
            "is_summary": True,
        }
    )

    return activity_rows


def menu_navigate(path: str, drawer: ui.right_drawer):
    """Navigate to a different page in the GUI."""
    ui.navigate.to(path)
    if drawer:
        drawer.set_value(False)


def menu():
    """Menu for the GUI."""
    with (
        ui.right_drawer().classes("bg-blue-100").props("id=menu-drawer") as right_drawer
    ):
        ui.menu_item(
            "Manage Task Groups",
            on_click=lambda: menu_navigate("/task_groups", right_drawer),
        )
        ui.menu_item(
            "Manage Tasks",
            on_click=lambda: menu_navigate("/tasks", right_drawer),
        )
        ui.menu_item(
            "Manage Activities",
            on_click=lambda: menu_navigate("/activities", right_drawer),
        )

    right_drawer.set_value(False)

    with ui.header().classes("items-center"):
        ui.link("My Application", target="/").style(
            "font-size: 1.5em; font-weight: bold; color: black; text-decoration: none;"
        )
        # Add a spacer to push subsequent elements to the right
        ui.space()
        # The button to toggle the right drawer, with a menu icon
        ui.button(
            on_click=lambda: right_drawer.set_value(not right_drawer.value), icon="menu"
        ).props("flat color=black").classes("ml-2")


def task_group_dialog():
    """Dialog for creating a new task group."""
    with ui.dialog() as dialog, ui.card():
        ui.label("Create Task Group").classes("text-lg")

        name_input = ui.input("Name")
        description_input = ui.input("Description")

        def submit_task_group():
            if not name_input.value:
                ui.notify("Name is required", type="negative")
                return

            rest_api.service.create_task_group(
                name=name_input.value,
                description=description_input.value or None,
            )
            ui.notify("Task group created")
            dialog.close()
            ui.navigate.reload()

        with ui.row():
            ui.button("Submit", on_click=submit_task_group, color="green")
            ui.button("Cancel", on_click=dialog.close, color="red")

    return dialog


def task_dialog():
    """Dialog for creating a new task."""
    with ui.dialog() as dialog, ui.card():
        ui.label("Create Task").classes("text-lg")

        task_groups_options = rest_api.service.get_all_task_groups(show=True)
        task_groups_options_objects = {tg.id: tg.name for tg in task_groups_options}

        def task_group_change_handler(e):
            selected_id = e.value
            logger.info(f"Selected task group ID: {selected_id}")
            selected_name = task_groups_options_objects.get(selected_id, "Unknown")
            logger.info(f"Selected task group name: {selected_name}")
            selected = next(
                (tg for tg in task_groups_options if tg.id == selected_id), None
            )
            if selected:
                logger.info(f"Selected task group object: {selected}")
            else:
                logger.warning(f"No task group found for ID: {selected_id}")

        task_group_input = ui.select(
            task_groups_options_objects,
            label="Task Group",
            value=None,
            on_change=task_group_change_handler,
        )
        name_input = ui.input("Name")
        description_input = ui.input("Description")

        def submit_task():
            if not name_input.value:
                ui.notify("Name is required", type="negative")
                return

            selected_task_group = next(
                (tg for tg in task_groups_options if tg.id == task_group_input.value),
                None,
            )
            if selected_task_group is None:
                ui.notify("Invalid task group selected", type="negative")
                return

            rest_api.service.create_task(
                name=name_input.value,
                description=description_input.value or None,
                task_group=selected_task_group,
            )
            ui.notify("Task created")
            dialog.close()
            ui.navigate.reload()

        with ui.row():
            ui.button("Submit", on_click=submit_task, color="green")
            ui.button("Cancel", on_click=dialog.close, color="red")

    return dialog


def activities_dialog():
    """Dialog for creating a new activity."""
    with ui.dialog() as dialog, ui.card():
        ui.label("Create Activity").classes("text-lg")

        task_options = rest_api.service.get_all_tasks(show=True)
        task_options_objects = {
            task.id: f"{task_group.name} - {task.name}"
            for task, task_group in task_options
        }

        def task_change_handler(e):
            selected_id = e.value
            logger.info(f"Selected task ID: {selected_id}")
            selected_name = task_options_objects.get(selected_id, "Unknown")
            logger.info(f"Selected task name: {selected_name}")
            selected = next(
                (
                    (task, task_group)
                    for task, task_group in task_options
                    if task.id == selected_id
                ),
                None,
            )
            if selected:
                logger.info(f"Selected task object: {selected}")
            else:
                logger.warning(f"No task found for ID: {selected_id}")

        task_input = ui.select(
            task_options_objects,
            label="Task",
            value=None,
            on_change=task_change_handler,
        )

        description_input = ui.input("Description")

        def submit_activity():
            selected_task = next(
                (
                    (task, task_group)
                    for task, task_group in task_options
                    if task.id == task_input.value
                ),
                None,
            )
            if selected_task is None:
                ui.notify("Invalid task selected", type="negative")
                return

            rest_api.service.create_activity(
                task=selected_task[0],
                description=description_input.value or None,
            )
            ui.notify("Activity created")
            dialog.close()
            ui.navigate.reload()

        with ui.row():
            ui.button("Submit", on_click=submit_activity, color="green")
            ui.button("Cancel", on_click=dialog.close, color="red")

    return dialog


@ui.page("/")
def index():
    """Index page for the GUI."""
    ui.label("Welcome to PyTaskTracker!").classes("text-2xl font-bold")
    menu()


@ui.page("/task_groups")
def task_groups():
    """Task groups page for the GUI."""
    task_group_rows = [
        {
            "id": tg.id,
            "name": tg.name,
            "show": tg.show,
            "toggle": "Disable" if tg.show else "Enable",
        }
        for tg in rest_api.service.get_all_task_groups(show=False)
    ]

    async def toggle_task_group_show(e):
        task_group_id = e.args if isinstance(e.args, str) else None
        if task_group_id is None:
            ui.notify("Unable to determine selected task group", type="negative")
            return

        task_group = rest_api.service.get_task_group_by_id(task_group_id)
        if task_group is None:
            ui.notify("Task group not found", type="negative")
            return

        action = "disable" if task_group.show else "enable"
        confirmed = await confirm_action_dialog(
            title="Confirm Change",
            message=f"Are you sure you want to {action} task group '{task_group.name}'?",
            confirm_text="Yes",
            cancel_text="No",
        )
        if not confirmed:
            return

        if task_group.show:
            rest_api.service.soft_delete_task_group_by_id(task_group_id=task_group.id)
        else:
            rest_api.service.undelete_task_group_by_id(task_group_id=task_group.id)
        ui.notify("Task group updated")
        ui.navigate.reload()

    menu()
    with ui.column().classes(_PAGE_COLUMN_CLASSES):
        ui.label("Task Groups").classes(_PAGE_HEADING_CLASSES)

        dialog = task_group_dialog()
        ui.button("Create New Task Group", on_click=dialog.open).classes("mb-4")

        table = ui.table(
            title="Task Groups",
            columns=[
                {
                    "name": "name",
                    "label": "Name",
                    "field": "name",
                    "required": True,
                    "sortable": True,
                },
                {"name": "show", "label": "Show", "field": "show", "required": True},
                {
                    "name": "toggle",
                    "label": "Action",
                    "field": "toggle",
                    "required": True,
                },
            ],
            rows=task_group_rows,
            row_key="id",
        )

        table.add_slot(
            "body-cell-toggle",
            """
            <q-td :props="props">
                <a href="#" 
                    class="text-primary" 
                    @click.prevent="$parent.$emit('toggle_show', props.row.id)">
                    {{ props.value }}
                </a>
            </q-td>
            """,
        )
        table.on("toggle_show", toggle_task_group_show)


@ui.page("/tasks")
def tasks():
    """Tasks page for the GUI."""
    task_rows = [
        {
            "id": task.id,
            "group": task_group.name,
            "name": task.name,
            "show": task.show,
            "toggle": "Disable" if task.show else "Enable",
        }
        for task, task_group in rest_api.service.get_all_tasks(show=False)
    ]

    async def toggle_task_show(e):
        task_id = e.args if isinstance(e.args, str) else None
        if task_id is None:
            ui.notify("Unable to determine selected task", type="negative")
            return

        task = rest_api.service.get_task_by_id(task_id)
        if task is None:
            ui.notify("Task not found", type="negative")
            return

        action = "disable" if task[0].show else "enable"
        confirmed = await confirm_action_dialog(
            title="Confirm Change",
            message=f"Are you sure you want to {action} task '{task[0].name}'?",
            confirm_text="Yes",
            cancel_text="No",
        )
        if not confirmed:
            return

        if task[0].show:
            rest_api.service.soft_delete_task_by_id(task_id=task[0].id)
        else:
            rest_api.service.undelete_task_by_id(task_id=task[0].id)
        ui.notify("Task updated")
        ui.navigate.reload()

    menu()
    with ui.column().classes(_PAGE_COLUMN_CLASSES):
        ui.label("Tasks").classes(_PAGE_HEADING_CLASSES)

        dialog = task_dialog()
        ui.button("Create New Task", on_click=dialog.open).classes("mb-4")

        table = ui.table(
            title="Tasks",
            columns=[
                {
                    "name": "group",
                    "label": "Group",
                    "field": "group",
                    "required": True,
                    "sortable": True,
                },
                {
                    "name": "name",
                    "label": "Name",
                    "field": "name",
                    "required": True,
                    "sortable": True,
                },
                {"name": "show", "label": "Show", "field": "show", "required": True},
                {
                    "name": "toggle",
                    "label": "Action",
                    "field": "toggle",
                    "required": True,
                },
            ],
            rows=task_rows,
            row_key="id",
        )

        table.add_slot(
            "body-cell-toggle",
            """
            <q-td :props="props">
                <a href="#" class="text-primary" 
                    @click.prevent="$parent.$emit('toggle_show', props.row.id)">
                    {{ props.value }}
                </a>
            </q-td>
            """,
        )
        table.on("toggle_show", toggle_task_show)


@ui.page("/activities")
def activities():
    """Activities page for the GUI."""
    today = datetime.now().strftime("%Y-%m-%d")

    activities_rows = build_activity_rows(
        start_date=datetime.strptime(today, "%Y-%m-%d"),
        end_date=datetime.strptime(today, "%Y-%m-%d"),
    )

    menu()
    with ui.column().classes(_PAGE_COLUMN_CLASSES):
        ui.label("Activities").classes(_PAGE_HEADING_CLASSES)

        dialog = activities_dialog()

        with ui.row().classes("mb-2"):
            ui.button("Create New Activity", on_click=dialog.open)

        with ui.card().classes("w-full max-w-6xl p-4"):
            with ui.row().classes("items-end gap-2"):
                ui.label("Filter Activities")
                start_date_input = ui.date_input("Start Date", value=today)
                start_time_input = ui.input("Start Time (optional)").props(
                    "type=time clearable"
                )
                end_date_input = ui.date_input("End Date", value=today)
                end_time_input = ui.input("End Time (optional)").props(
                    "type=time clearable"
                )

            filter_actions_row = ui.row().classes("mb-2 mt-2 gap-2")

            table = ui.table(
                title="Activities",
                columns=[
                    {
                        "name": "group",
                        "label": "Group",
                        "field": "group",
                        "required": True,
                        "sortable": True,
                    },
                    {
                        "name": "task",
                        "label": "Task",
                        "field": "task",
                        "required": True,
                        "sortable": True,
                    },
                    {
                        "name": "started",
                        "label": "Started",
                        "field": "started",
                        "required": True,
                        "sortable": True,
                    },
                    {
                        "name": "ended",
                        "label": "Ended",
                        "field": "ended",
                        "required": True,
                        "sortable": True,
                    },
                    {
                        "name": "elapsed_hms",
                        "label": "Elapsed",
                        "field": "elapsed_hms",
                        "required": True,
                    },
                    {
                        "name": "end_activity",
                        "label": "Action",
                        "field": "end_activity",
                        "required": True,
                    },
                ],
                rows=activities_rows,
                row_key="id",
            ).classes("w-full")

        def apply_activities_filter() -> None:
            start_date, exact_start = parse_filter_datetime(
                start_date_input.value,
                start_time_input.value,
                "Start",
            )
            if start_date is None:
                return

            end_date, exact_end = parse_filter_datetime(
                end_date_input.value,
                end_time_input.value,
                "End",
            )
            if end_date is None:
                return

            table.rows = build_activity_rows(
                start_date=start_date,
                end_date=end_date,
                exact_start=exact_start,
                exact_end=exact_end,
            )
            table.update()

        def clear_activities_filter() -> None:
            start_date_input.value = today
            start_time_input.value = None
            end_date_input.value = today
            end_time_input.value = None
            apply_activities_filter()

        with filter_actions_row:
            ui.button("Apply Filter", on_click=apply_activities_filter).props(
                "dense"
            ).classes("text-xs px-2 py-1")
            ui.button("Clear Filter", on_click=clear_activities_filter).props(
                "dense"
            ).classes("text-xs px-2 py-1")

        table.add_slot(
            "body-cell-started",
            """
            <q-td :props="props">
                <a v-if="!props.row.is_summary" href="#" 
                    class="text-primary" 
                    @click.prevent="$parent.$emit('on-edit_started', props.row.id)">
                    {{ props.value ? props.value : 'Set Started' }}
                </a>
            </q-td>
            """,
        )
        table.on("on-edit_started", edit_started_handler)

        table.add_slot(
            "body-cell-ended",
            """
            <q-td :props="props">
                <a v-if="!props.row.is_summary" href="#" 
                    class="text-primary" 
                    @click.prevent="$parent.$emit('on-edit_ended', props.row.id)">
                    {{ props.value ? props.value : 'Set Ended' }}
                </a>
            </q-td>
            """,
        )
        table.on("on-edit_ended", edit_ended_handler)

        table.add_slot(
            "body-cell-end_activity",
            """
            <q-td :props="props">
                <a v-if="!props.row.is_summary" href="#" 
                    class="text-primary" 
                    @click.prevent="$parent.$emit('on-end_activity', props.row.id)">
                    End Activity
                </a>
            </q-td>
            """,
        )
        table.on("on-end_activity", end_activity_handler)


class GuiApp:
    """GUI API class for handling GUI-related requests and responses."""

    def __init__(self):
        """Initialize the GUI API."""
        self.rest_api_app = rest_api.get_app()
        self.app = app
        self.app.include_router(self.rest_api_app.router, prefix="/api")

    def start_gui(self, port: int = 8989, host: str = "127.0.0.1"):
        """Start the GUI.
        NOTE: there is an issue using 'reload=True' with the FastAPI router,
        so we set it to False for now.
        """
        ui.run(
            port=port,
            host=host,
            reload=False,
            storage_secret="pytasktracker_secret",
            fastapi_docs=True,
            reconnect_timeout=30.0,
        )
