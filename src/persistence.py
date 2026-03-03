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
"""Persistence layer for the application."""

import os
from datetime import datetime
from typing import TypeVar

from sqlmodel import Session, SQLModel, col, create_engine, select

from logging_config import configure_logging
from models import Activity, Task, TaskGroup

logger = configure_logging()

T = TypeVar("T")


class Persistence:
    """Persistence layer for the application."""

    def __init__(self, database_url: str | None = None, recreate: bool = False) -> None:
        """Initialize the persistence layer."""
        database_url = database_url or os.getenv(
            "DATABASE_URL", "duckdb:///./pytasktracker.db"
        )
        logger.info(f"Initializing database with URL: {database_url}")
        self.engine = create_engine(database_url)
        # Drop all tables and recreate them if requested. This is useful for testing.
        if recreate or os.getenv("RECREATE_DB", "false").lower() == "true":
            SQLModel.metadata.drop_all(bind=self.engine)
        SQLModel.metadata.create_all(bind=self.engine)
        logger.info(
            "Database initialized",
            extra={"database_url": database_url, "recreate": recreate},
        )

    def get_session(self) -> Session:
        """Create and return a new database session.

        Returns:
            Session: A new database session.
        """
        return Session(bind=self.engine)

    def save(self, model: T) -> T:
        """Save an object to the database.

        Args:
            model (T): The object to save.
        """
        if isinstance(model, Activity):
            if model.started is not None:
                model.started = model.started.replace(microsecond=0)
            if model.ended is not None:
                model.ended = model.ended.replace(microsecond=0)
            model.elapsed = (
                int((model.ended - model.started).total_seconds())
                if model.started and model.ended
                else None
            )
        with self.get_session() as session:
            merged_model = session.merge(model, load=True)
            session.commit()
            session.refresh(merged_model)
            logger.info("Object persisted to database", extra={"object": merged_model})
            return merged_model

    def fetch(self, model_class: type[T], model_id: str) -> T | None:
        """Fetch an object from the database by its ID.

        Args:
            model_class (type[T]): The class of the object to fetch.
            model_id (str): The ID of the object to fetch.

        Returns:
            T | None: The fetched object or None if not found.
        """
        logger.info(
            "Fetching object from database",
            extra={"model_class": model_class.__name__, "model_id": model_id},
        )
        with self.get_session() as session:
            return session.get(model_class, model_id)

    def fetch_all(self, model_class: type[T]) -> list[T]:
        """Fetch all objects of a given class from the database.

        Args:
            model_class (type[T]): The class of the objects to fetch.

        Returns:
            list[T]: A list of all fetched objects.
        """
        logger.info(
            "Fetching all objects from database",
            extra={"model_class": model_class.__name__},
        )
        with self.get_session() as session:
            statement = select(model_class)
            return list(session.exec(statement).all())

    def delete(self, model: T) -> None:
        """Delete an object from the database.

        Args:
            model (T): The object to delete.
        """
        logger.info("Deleting object from database", extra={"object": model})
        with self.get_session() as session:
            session.delete(model)
            session.commit()
            logger.info("Object deleted from database", extra={"object": model})

    def delete_many(self, model: list[T]) -> None:
        """Delete multiple objects from the database.

        Args:
            model (list[T]): The objects to delete.
        """
        logger.info("Deleting multiple objects from database", extra={"objects": model})
        with self.get_session() as session:
            for obj in model:
                session.delete(obj)
            session.commit()
            logger.info("Objects deleted from database", extra={"objects": model})

    ##### Additional methods for specific queries can be added here as needed #####

    def fetch_all_shown_task_groups(self) -> list[TaskGroup]:
        """Fetch all TaskGroups that are marked as shown.

        Returns:
            list[TaskGroup]: The shown task groups.
        """
        logger.info("Fetching all shown task groups from database")
        with self.get_session() as session:
            statement = select(TaskGroup).where(TaskGroup.show)
            return session.exec(statement).all()  # type: ignore

    def fetch_all_shown_tasks(self) -> list[tuple[Task, TaskGroup]]:
        """Fetch all Tasks that are marked as shown, joined with their TaskGroup.

        Returns:
            list[tuple[Task, TaskGroup]]: The shown tasks with their task group.
        """
        logger.info("Fetching all shown tasks from database")
        with self.get_session() as session:
            statement = (
                select(Task, TaskGroup)
                .join(TaskGroup, col(Task.group_id) == col(TaskGroup.id))
                .where(Task.show)
            )
            return session.exec(statement).all()  # type: ignore

    def fetch_all_tasks(self) -> list[tuple[Task, TaskGroup]]:
        """Fetch all Tasks, joined with their TaskGroup.

        Returns:
            list[tuple[Task, TaskGroup]]: All tasks with their task group.
        """
        logger.info("Fetching all tasks from database")
        with self.get_session() as session:
            statement = select(Task, TaskGroup).join(
                TaskGroup, col(Task.group_id) == col(TaskGroup.id)
            )
            return session.exec(statement).all()  # type: ignore

    def fetch_task(self, task_id: str) -> tuple[Task, TaskGroup] | None:
        """Fetch a single Task by ID, joined with its TaskGroup.

        Args:
            task_id (str): The ID of the task to fetch.

        Returns:
            tuple[Task, TaskGroup] | None: The task with its task group, or None if not found.
        """
        logger.info("Fetching task from database", extra={"task_id": task_id})
        with self.get_session() as session:
            statement = (
                select(Task, TaskGroup)
                .join(TaskGroup, col(Task.group_id) == col(TaskGroup.id))
                .where(Task.id == task_id)
            )
            return session.exec(statement).first()

    def fetch_all_activities(self) -> list[tuple[Activity, Task, TaskGroup]]:
        """Fetch all Activities, joined with their Task and TaskGroup.

        Returns:
            list[tuple[Activity, Task, TaskGroup]]: The activities with their task and task group.
        """
        logger.info("Fetching all activities from database")
        with self.get_session() as session:
            statement = (
                select(Activity, Task, TaskGroup)
                .join(Task, col(Activity.task_id) == col(Task.id))
                .join(TaskGroup, col(Activity.group_id) == col(TaskGroup.id))
            )
            return session.exec(statement).all()  # type: ignore

    def fetch_filtered_activities(
        self,
        started_start_date: datetime,
        started_end_date: datetime,
    ) -> list[tuple[Activity, Task, TaskGroup]]:
        """Fetch all Activities within a date range, joined with their Task and TaskGroup.

        Args:
            started_start_date (datetime): The start date for filtering activities.
            started_end_date (datetime): The end date for filtering activities.

        Returns:
            list[tuple[Activity, Task, TaskGroup]]: The activities with their task and task group.
        """
        logger.info(
            "Fetching filtered activities from database",
            extra={"start_date": started_start_date, "end_date": started_end_date},
        )
        with self.get_session() as session:
            statement = (
                select(Activity, Task, TaskGroup)
                .join(Task, col(Activity.task_id) == col(Task.id))
                .join(TaskGroup, col(Activity.group_id) == col(TaskGroup.id))
                .where(
                    (col(Activity.started) >= started_start_date),
                    (col(Activity.started) <= started_end_date),
                )
            )
            return session.exec(statement).all()  # type: ignore

    def fetch_activity(
        self, activity_id: str
    ) -> tuple[Activity, Task, TaskGroup] | None:
        """Fetch a single Activity by ID, joined with its Task and TaskGroup.

        Args:
            activity_id (str): The ID of the activity to fetch.

        Returns:
            tuple[Activity, Task, TaskGroup] | None: The activity with its task and
            task group, or None if not found.
        """
        logger.info(
            "Fetching activity from database", extra={"activity_id": activity_id}
        )
        with self.get_session() as session:
            statement = (
                select(Activity, Task, TaskGroup)
                .join(Task, col(Activity.task_id) == col(Task.id))
                .join(TaskGroup, col(Activity.group_id) == col(TaskGroup.id))
                .where(Activity.id == activity_id)
            )
            return session.exec(statement).first()

    def fetch_tasks_by_task_group(
        self, task_group_id: str
    ) -> list[tuple[Task, TaskGroup]] | None:
        """Fetch all Tasks by TaskGroup ID, joined with their TaskGroup.

        Args:
            task_group_id (str): The ID of the task group to fetch tasks for.

        Returns:
            list[tuple[Task, TaskGroup]] | None: The tasks with their task group, or None if not found.
        """
        logger.info(
            "Fetching tasks by task group from database",
            extra={"task_group_id": task_group_id},
        )
        with self.get_session() as session:
            statement = (
                select(Task, TaskGroup)
                .join(TaskGroup, col(Task.group_id) == col(TaskGroup.id))
                .where(Task.group_id == task_group_id)
            )
            return session.exec(statement).all()  # type: ignore
