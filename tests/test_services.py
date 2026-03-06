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
"""Tests for the service layer of the application."""

from dataclasses import dataclass
from uuid import uuid4

import pytest

from logging_config import configure_logging
from models import Task, TaskGroup
from services import Services

logger = configure_logging()


@dataclass
class ModelValues:
    """A simple dataclass to hold model objects created during tests. This allows us to share state between test methods in a class."""

    task_group: TaskGroup
    task: Task
    activities: list


@pytest.fixture(scope="class")
def services():
    """Fixture to provide a Services instance for testing. Uses an in-memory database for isolation."""
    return Services("duckdb:///:memory:", recreate=True)


@pytest.fixture(scope="class")
def model_values():
    """Fixture to provide a ModelValues instance for testing. This will hold objects created during tests."""
    return ModelValues(
        task_group=TaskGroup(
            name="Original task group", description="Original task group"
        ),
        task=Task(
            group_id="", name="Original Task", description="Original task description"
        ),
        activities=[],
    )


class TestServices:
    """Tests for the Services class."""

    @pytest.mark.order(1)
    def test_modify_task_group(self, services, model_values):
        """Test creating or modifying a task group."""
        name = "Test Group"
        description = "A test task group"
        model_values.task_group = services.create_task_group(
            name=name, description=description
        )
        assert model_values.task_group.id is not None
        assert model_values.task_group.name == name
        assert model_values.task_group.description == description

        name = "Updated Test Group"
        model_values.task_group.name = name
        updated_task_group = services.modify_task_group(
            task_group=model_values.task_group
        )
        assert updated_task_group.id == model_values.task_group.id
        assert updated_task_group.name == name
        assert updated_task_group.description == description

        services.soft_delete_task_group(task_group=updated_task_group)

        task_groups = services.get_all_task_groups()
        assert len(task_groups) == 0

        services.undelete_task_group(task_group=updated_task_group)

        task_group = services.get_task_group_by_id(task_group_id=updated_task_group.id)
        assert task_group is not None
        assert task_group.id == updated_task_group.id
        assert task_group.name == name
        assert task_group.description == description
        assert task_group.show is True
        model_values.task_group = updated_task_group

    @pytest.mark.order(2)
    def test_modify_tasks(self, services, model_values):
        """Test creating or modifying tasks."""
        logger.info("Testing task modification.")
        task_group = model_values.task_group
        assert task_group.id is not None
        name = "Test Task"
        description = "A test task"
        task = services.create_task(
            task_group=task_group, name=name, description=description
        )
        assert task.id is not None
        assert task.name == name
        assert task.description == description
        assert task.group_id == task_group.id

        services.soft_delete_task(task=task)

        tasks = services.get_all_tasks()
        assert len(tasks) == 0

        services.undelete_task(task=task)

        services.soft_delete_task_by_id(task_id=task.id)

        ref_task = services.get_task_by_id(task_id=task.id)
        assert ref_task is not None

        services.undelete_task_by_id(task_id=task.id)

        tasks = services.get_all_tasks()
        assert len(tasks) == 1

        services.undelete_task(task=task)

        name = "Updated Test Task"
        task.name = name
        updated_task = services.modify_task(task=task)
        assert updated_task.id == task.id
        assert updated_task.name == name
        assert updated_task.description == description

        model_values.task = updated_task

        tasks = services.get_all_tasks(show=False)
        assert len(tasks) == 1
        print(f"Retrieved tasks: {tasks}")
        first_task = tasks[0][0]
        assert first_task.id == model_values.task.id
        assert first_task.name == model_values.task.name
        assert first_task.description == model_values.task.description
        assert first_task.group_id == model_values.task.group_id

        model_values.task = first_task

    @pytest.mark.order(3)
    def test_modify_activities(self, services, model_values):
        """Test creating or modifying activities. This is a placeholder for future tests once the Activity model and related service methods are implemented."""
        task_group = model_values.task_group
        task = model_values.task
        assert task_group.id is not None
        assert task.id is not None

        description = "Test Activity"
        activity = services.create_activity(task=task, description=description)
        assert activity.id is not None
        assert activity.task_id == task.id
        assert activity.group_id == task_group.id
        assert activity.description == description

        model_values.activities.append(activity)

        activities = services.get_filtered_activities()
        assert len(activities) == 1
        assert activities[0][0].id == activity.id
        assert activities[0][1].id == task.id
        assert activities[0][2].id == task_group.id

        activity = services.end_activity_by_id(activity_id=activity.id)

        activities = services.get_filtered_activities(
            start_date=activity.started,
            exact_start=True,
            end_date=activity.ended,
            exact_end=True,
        )
        assert len(activities) == 1
        assert activities[0][0].id == activity.id
        assert activities[0][1].id == task.id
        assert activities[0][2].id == task_group.id

        activity = services.end_activity_by_id(activity_id=uuid4())
        assert activity is None
