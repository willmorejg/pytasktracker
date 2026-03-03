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
"""Service layer for the application."""

from datetime import datetime

from datetime_utilities import end_of_day, get_current_time, start_of_day
from logging_config import configure_logging
from models import Activity, Task, TaskGroup
from persistence import Persistence

logger = configure_logging()


class Services:
    """Service layer for the application. This is where business logic will go."""

    def __init__(self, database_url: str | None = None, recreate: bool = False) -> None:
        """Initialize the services with a persistence layer."""
        self.persistence = Persistence(database_url, recreate)

    ## TaskGroup methods
    def create_task_group(self, name: str, description: str | None = None) -> TaskGroup:
        """Create a new task group.

        Args:
            name (str): The name of the task group.
            description (str | None): An optional description of the task group.

        Returns:
            TaskGroup: The created TaskGroup object.
        """
        task_group = TaskGroup(name=name, description=description)
        return self.persistence.save(task_group)

    def modify_task_group(self, task_group: TaskGroup) -> TaskGroup:
        """Create or modify a task group.

        Args:
            task_group (TaskGroup): The TaskGroup object to create or modify.

        Returns:
            TaskGroup: The created or modified TaskGroup object.
        """
        return self.persistence.save(task_group)

    def get_all_task_groups(self, show: bool = True) -> list[TaskGroup]:
        """Get all task groups.

        Args:
            show (bool): Whether to fetch only task groups with show is True.

        Returns:
            list[TaskGroup]: A list of all TaskGroup objects.
        """
        if show:
            return self.persistence.fetch_all_shown_task_groups()
        return self.persistence.fetch_all(TaskGroup)

    def get_task_group_by_id(self, task_group_id: str) -> TaskGroup | None:
        """Get a task group by its ID.

        Args:
            task_group_id (str): The ID of the task group to fetch.

        Returns:
            TaskGroup | None: The TaskGroup object with the specified ID, or None if not found.
        """
        return self.persistence.fetch(TaskGroup, task_group_id)

    def soft_delete_task_group(self, task_group: TaskGroup) -> None:
        """Soft delete a task group.

        Args:
            task_group (TaskGroup): The TaskGroup object to delete.
        """
        task_group.show = False
        self.persistence.save(task_group)

    def soft_delete_task_group_by_id(self, task_group_id: str) -> None:
        """Soft delete a task group by its ID.

        Args:
            task_group_id (str): The ID of the TaskGroup object to delete.
        """
        task_group = self.get_task_group_by_id(task_group_id)
        if task_group:
            self.soft_delete_task_group(task_group)

    def undelete_task_group(self, task_group: TaskGroup) -> None:
        """Undelete a task group.

        Args:
            task_group (TaskGroup): The TaskGroup object to undelete.
        """
        task_group.show = True
        self.persistence.save(task_group)

    def undelete_task_group_by_id(self, task_group_id: str) -> None:
        """Undelete a task group by its ID.

        Args:
            task_group_id (str): The ID of the TaskGroup object to undelete.
        """
        task_group = self.get_task_group_by_id(task_group_id)
        if task_group:
            self.undelete_task_group(task_group)

    ## Task methods
    def create_task(
        self, task_group: TaskGroup, name: str, description: str | None = None
    ) -> Task:
        """Create a new task.

        Args:
            task_group (TaskGroup): The TaskGroup to associate with the task.
            name (str): The name of the task.
            description (str | None): An optional description of the task.

        Returns:
            Task: The created Task object.
        """
        task = Task(name=name, description=description, group_id=task_group.id)
        return self.persistence.save(task)

    def modify_task(self, task: Task) -> Task:
        """Create or modify a task.

        Args:
            task (Task): The Task object to create or modify.

        Returns:
            Task: The created or modified Task object.
        """
        return self.persistence.save(task)

    def get_all_tasks(self, show: bool = True) -> list[tuple[Task, TaskGroup]]:
        """Get all tasks.

        Args:
            show (bool): Whether to fetch only tasks with show is True.

        Returns:
            list[tuple[Task, TaskGroup]]: A list of all Task objects with their associated TaskGroup.
        """
        if show:
            return self.persistence.fetch_all_shown_tasks()
        return self.persistence.fetch_all_tasks()

    def get_task_by_id(self, task_id: str) -> tuple[Task, TaskGroup] | None:
        """Get a task by its ID.

        Args:
            task_id (str): The ID of the task to fetch.

        Returns:
            tuple[Task, TaskGroup] | None: The Task object with its associated TaskGroup, or None if not found.
        """
        return self.persistence.fetch_task(task_id)

    def soft_delete_task(self, task: Task) -> None:
        """Soft delete a task.

        Args:
            task (Task): The Task object to delete.
        """
        task.show = False
        self.persistence.save(task)

    def soft_delete_task_by_id(self, task_id: str) -> None:
        """Soft delete a task by its ID.

        Args:
            task_id (str): The ID of the Task object to delete.
        """
        task = self.get_task_by_id(task_id)
        if task:
            self.soft_delete_task(task[0])

    def undelete_task(self, task: Task) -> None:
        """Undelete a task.

        Args:
            task (Task): The Task object to undelete.
        """
        task.show = True
        self.persistence.save(task)

    def undelete_task_by_id(self, task_id: str) -> None:
        """Undelete a task by its ID.

        Args:
            task_id (str): The ID of the Task object to undelete.
        """
        task = self.get_task_by_id(task_id)
        if task:
            self.undelete_task(task[0])

    ## Activity methods
    def create_activity(self, task: Task, description: str | None = None) -> Activity:
        """Create a new activity.

        Args:
            task (Task): The Task to associate with the activity.
            description (str | None): An optional description of the activity.

        Returns:
            Activity: The created Activity object.
        """
        activity = Activity(
            description=description,
            task_id=task.id,
            group_id=task.group_id,
            started=get_current_time(),
        )
        return self.persistence.save(activity)

    def modify_activity(self, activity: Activity) -> Activity:
        """Create or modify an activity.

        Args:
            activity (Activity): The Activity object to create or modify.

        Returns:
            Activity: The created or modified Activity object.
        """
        return self.persistence.save(activity)

    def end_activity_by_id(self, activity_id: str) -> Activity | None:
        """End an activity by its ID.

        Args:
            activity_id (str): The ID of the activity to end.

        Returns:
            Activity | None: The modified Activity object with the 'ended' attribute set, or None if not found.
        """
        activity = self.get_activity_by_id(activity_id)
        if activity:
            return self.end_activity(activity[0])
        return None

    def end_activity(self, activity: Activity) -> Activity:
        """End an activity by setting its 'ended' attribute to the current time.

        Args:
            activity (Activity): The Activity object to end.

        Returns:
            Activity: The modified Activity object with the 'ended' attribute set.
        """
        activity.ended = get_current_time()
        return self.persistence.save(activity)

    def get_all_activities(self) -> list[tuple[Activity, Task, TaskGroup]]:
        """Get all activities.

        Returns:
            list[tuple[Activity, Task, TaskGroup]]: A list of all Activity objects with their associated Task and TaskGroup.
        """
        return self.persistence.fetch_all_activities()

    def get_filtered_activities(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        exact_start: bool = False,
        exact_end: bool = False,
    ) -> list[tuple[Activity, Task, TaskGroup]]:
        """Get activities filtered by start and end date. Will default for start of current day and end with end of current day.

        Args:
            start_date (datetime | None): The start date to filter activities (inclusive).
            end_date (datetime | None): The end date to filter activities (inclusive).
            exact_start (bool): If True, filter activities that started exactly on the start date.
            exact_end (bool): If True, filter activities that ended exactly on the end date.

        Returns:
            list[tuple[Activity, Task, TaskGroup]]: A list of Activity objects with their associated Task and TaskGroup that match the filter criteria.
        """
        # make sure dates are not None and adjust to start or end of day if not exact
        if start_date is None:
            filtered_start_date = get_current_time()
        else:
            filtered_start_date = start_date

        if end_date is None:
            filtered_end_date = get_current_time()
        else:
            filtered_end_date = end_date

        filtered_start_date = self._determine_filter_date(
            filtered_start_date, exact_start, start_of_day_flag=True
        )
        filtered_end_date = self._determine_filter_date(
            filtered_end_date, exact_end, start_of_day_flag=False
        )

        return self.persistence.fetch_filtered_activities(
            filtered_start_date, filtered_end_date
        )

    def _determine_filter_date(
        self, value: datetime, exact: bool, start_of_day_flag: bool
    ) -> datetime:
        """Determine the filter date based on the input value and whether it should be exact.

        Args:
            value (datetime): The input datetime value to determine the filter date from.
            exact (bool): Whether to use the exact datetime or adjust it to the start or end of the day.
            start_of_day_flag (bool): Whether to adjust to the start of the day (True) or end of the day (False) if not exact.

        Returns:
            datetime: The determined filter datetime.
        """
        if exact:
            return value
        return start_of_day(value) if start_of_day_flag else end_of_day(value)

    def get_activity_by_id(
        self, activity_id: str
    ) -> tuple[Activity, Task, TaskGroup] | None:
        """Get an activity by its ID.

        Args:
            activity_id (str): The ID of the activity to fetch.

        Returns:
            tuple[Activity, Task, TaskGroup] | None: The Activity object with its associated Task and TaskGroup, or None if not found.
        """
        return self.persistence.fetch_activity(activity_id)
