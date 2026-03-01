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
"""REST API module for handling RESTful requests and responses."""

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from sqlmodel import SQLModel

from logging_config import configure_logging
from models import Activity, Task, TaskGroup
from services import Services

logger = configure_logging()

app = FastAPI()

service = Services()


class ActivityDisplay(SQLModel):
    """Display model for activity responses."""

    id: str
    group: str
    task: str
    started: str | None
    ended: str | None
    elapsed_hms: str | None
    description: str | None


def get_app() -> FastAPI:
    """Get the FastAPI application instance.

    Returns:
        FastAPI: The FastAPI application instance.
    """
    return app


class BaseAppException(Exception):
    """Base exception for our application."""

    def __init__(self, message: str, status_code: int = 400):
        """Initialize the BaseAppException."""
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


# Global exception handler
@app.exception_handler(BaseAppException)
async def app_exception_handler(_request, exc):
    """Global exception handler for BaseAppException."""
    logger.error(f"Application error: {exc.message}")
    return JSONResponse(status_code=exc.status_code, content={"error": exc.message})


@app.exception_handler(IntegrityError)
async def integrity_error_handler(_request, exc):
    """Global exception handler for IntegrityError."""
    logger.error(f"Application error: {exc.args}")
    return JSONResponse(
        status_code=400,
        content={
            "error": "Request will result in a duplicate entry or violates a database constraint."
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(_request, exc):
    """Global exception handler for all other exceptions."""
    logger.error(f"Application error: {exc}")
    return JSONResponse(
        status_code=400, content={"error": "An unexpected error occurred."}
    )


@app.get("/.well-known/appspecific/com.chrome.devtools.json", include_in_schema=False)
async def chrome_devtools_json() -> JSONResponse:
    """Satisfy Chrome's DevTools discovery probe so it never reaches the 404 handler."""
    return JSONResponse({})


## Task Group Endpoints
@app.get(
    "/task_groups",
    response_model=list[TaskGroup],
    summary="Get all task groups with show is True",
    description="Retrieve a list of all task groups with show is True.",
)
async def get_task_groups_visible() -> list[TaskGroup]:
    """Endpoint to retrieve all task groups with show is True.

    Returns:
        list[TaskGroup]: A list of all task groups with show is True.
    """
    task_groups = service.get_all_task_groups(show=True)
    return task_groups


@app.get(
    "/task_groups/all",
    response_model=list[TaskGroup],
    summary="Get all task groups",
    description="Retrieve a list of all task groups.",
)
async def get_task_groups() -> list[TaskGroup]:
    """Endpoint to retrieve all task groups.

    Returns:
        list[TaskGroup]: A list of all task groups.
    """
    task_groups = service.get_all_task_groups(show=False)
    return task_groups


@app.post(
    "/task_groups",
    response_model=TaskGroup,
    summary="Create a new task group",
    description="Create a new task group with the provided name and description.",
)
async def create_task_group(task_group: TaskGroup) -> TaskGroup:
    """Endpoint to create a new task group.

    Args:
        task_group (TaskGroup): The task group to create.

    Returns:
        TaskGroup: The created task group.
    """
    return service.create_task_group(
        name=task_group.name, description=task_group.description
    )


@app.put(
    "/task_groups",
    response_model=TaskGroup,
    summary="Update an existing task group",
    description="Update an existing task group with the provided name and description.",
)
async def update_task_group(task_group: TaskGroup) -> TaskGroup:
    """Endpoint to update an existing task group.

    Args:
        task_group (TaskGroup): The task group to update.

    Returns:
        TaskGroup: The updated task group.
    """
    return service.modify_task_group(task_group=task_group)


@app.patch(
    "/task_groups/{task_group_id}",
    response_model=bool,
    summary="Soft delete a task group",
    description="Soft delete an existing task group by setting its 'show' attribute to False.",
)
async def soft_delete_task_group(task_group_id: str) -> bool:
    """Endpoint to soft delete an existing task group.

    Args:
        task_group_id (str): The ID of the task group to soft delete.

    Returns:
        bool: True if the task group was successfully soft deleted, False otherwise.
    """
    service.soft_delete_task_group_by_id(task_group_id=task_group_id)
    return True


@app.patch(
    "/task_groups/{task_group_id}/enable",
    response_model=bool,
    summary="Enable a task group",
    description="Enable an existing task group by setting its 'show' attribute to True.",
)
async def enable_task_group(task_group_id: str) -> bool:
    """Endpoint to enable an existing task group.

    Args:
        task_group_id (str): The ID of the task group to enable.

    Returns:
        bool: True if the task group was successfully enabled, False otherwise.
    """
    service.undelete_task_group_by_id(task_group_id=task_group_id)
    return True


## Task Endpoints
@app.get(
    "/tasks",
    response_model=list[Task],
    summary="Get all tasks with show is True",
    description="Retrieve a list of all tasks with show is True.",
)
async def get_tasks_visible() -> list[tuple[Task, TaskGroup]]:
    """Endpoint to retrieve all tasks with show is True.

    Returns:
        list[tuple[Task, TaskGroup]]: A list of all tasks with show is True.
    """
    tasks = service.get_all_tasks(show=True)
    return tasks


@app.get(
    "/tasks/all",
    response_model=list[tuple[Task, TaskGroup]],
    summary="Get all tasks",
    description="Retrieve a list of all tasks.",
)
async def get_all_tasks() -> list[tuple[Task, TaskGroup]]:
    """Endpoint to retrieve all tasks.

    Returns:
        list[tuple[Task, TaskGroup]]: A list of all tasks.
    """
    tasks = service.get_all_tasks(show=False)
    return tasks


@app.post(
    "/tasks",
    response_model=Task,
    summary="Create a new task",
    description="Create a new task with the provided name and description.",
)
async def create_task(task: Task, task_group: TaskGroup) -> Task:
    """Endpoint to create a new task.

    Args:
        task (Task): The task to create.
        task_group (TaskGroup): The task group to associate with the task.

    Returns:
        Task: The created task.
    """
    return service.create_task(
        name=task.name, description=task.description, task_group=task_group
    )


@app.put(
    "/tasks",
    response_model=Task,
    summary="Update an existing task",
    description="Update an existing task with the provided name and description.",
)
async def update_task(task: Task) -> Task:
    """Endpoint to update an existing task.

    Args:
        task (Task): The task to update.

    Returns:
        Task: The updated task.
    """
    return service.modify_task(task=task)


@app.patch(
    "/tasks/{task_id}",
    response_model=bool,
    summary="Soft delete a task",
    description="Soft delete an existing task by setting its 'show' attribute to False.",
)
async def soft_delete_task(task_id: str) -> bool:
    """Endpoint to soft delete an existing task.

    Args:
        task_id (str): The ID of the task to soft delete.

    Returns:
        bool: True if the task was successfully soft deleted, False otherwise.
    """
    service.soft_delete_task_by_id(task_id=task_id)
    return True


@app.patch(
    "/tasks/{task_id}/enable",
    response_model=bool,
    summary="Enable a task",
    description="Enable an existing task by setting its 'show' attribute to True.",
)
async def enable_task(task_id: str) -> bool:
    """Endpoint to enable an existing task.

    Args:
        task_id (str): The ID of the task to enable.

    Returns:
        bool: True if the task was successfully enabled, False otherwise.
    """
    service.undelete_task_by_id(task_id=task_id)
    return True


## Activity Endpoints
@app.get(
    "/activities",
    response_model=list[ActivityDisplay],
    summary="Get all activities",
    description="Retrieve a list of all activities.",
)
async def get_activities() -> list[ActivityDisplay]:
    """Endpoint to retrieve all activities.

    Returns:
        list[ActivityDisplay]: A list of all activities for display.
    """
    activities = service.get_all_activities()
    return [
        ActivityDisplay(
            id=activity.id,
            group=task_group.name,
            task=task.name,
            started=activity.started.isoformat() if activity.started else None,
            ended=activity.ended.isoformat() if activity.ended else None,
            elapsed_hms=activity.elapsed_hms,
            description=activity.description,
        )
        for activity, task, task_group in activities
    ]


@app.post(
    "/activities",
    response_model=Activity,
    summary="Create a new activity",
    description="Create a new activity with the provided task and description.",
)
async def create_activity(task: Task, description: str | None = None) -> Activity:
    """Endpoint to create a new activity.

    Args:
        task (Task): The task to associate with the activity.
        description (str | None): An optional description for the activity.

    Returns:
        Activity: The created activity.
    """
    return service.create_activity(task=task, description=description)


@app.put(
    "/activities",
    response_model=Activity,
    summary="Update an existing activity",
    description="Update an existing activity with the provided task and description.",
)
async def update_activity(activity: Activity) -> Activity:
    """Endpoint to update an existing activity.

    Args:
        activity (Activity): The activity to update.

    Returns:
        Activity: The updated activity.
    """
    return service.modify_activity(activity=activity)


@app.patch(
    "/activities/{activity_id}/end",
    response_model=Activity,
    summary="End an activity",
    description="End an existing activity by setting its 'ended' attribute to the current time.",
)
async def end_activity(activity_id: str) -> bool:
    """Endpoint to end an existing activity.

    Args:
        activity_id (str): The ID of the activity to end.

    Returns:
        bool: True if the activity was successfully ended, False otherwise.
    """
    service.end_activity_by_id(activity_id=activity_id)
    return True
