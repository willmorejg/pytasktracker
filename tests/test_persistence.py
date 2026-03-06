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
from datetime import timedelta

import pytest

from logging_config import configure_logging
from models import Activity, Task, TaskGroup
from persistence import Persistence

logger = configure_logging()


@pytest.fixture(scope="class")
def persistence():
    """Fixture to provide a Persistence instance for testing. Uses an in-memory database for isolation."""
    return Persistence("duckdb:///:memory:", recreate=True)


class TestPersistence:
    """Tests for the Persistence class."""

    def test_initialization(self, persistence):
        """Test that the Persistence class initializes correctly."""
        assert persistence.engine is not None

    def test_task_group(self, persistence):
        """Test saving and fetching TaskGroups."""
        group = persistence.save(TaskGroup(name="Group 1", description="First group"))
        assert group.id is not None

        persistence.save(TaskGroup(name="Group 2", description="Second group"))

        groups = persistence.fetch_all(TaskGroup)
        assert len(groups) == 2
        assert any(g.name == "Group 1" for g in groups)

        group = groups[0]
        group.description = "Updated description"
        previous_modified = group.updated_at
        persistence.save(group)
        updated_group = persistence.fetch(TaskGroup, group.id)
        assert updated_group.description == "Updated description"
        assert updated_group.updated_at > previous_modified

    def test_task(self, persistence):
        """Test saving and fetching Tasks, using existing TaskGroups."""
        groups = persistence.fetch_all(TaskGroup)
        group = groups[0]

        task = persistence.save(
            Task(name="Task 1", description="First task", group_id=group.id)
        )
        assert task.id is not None

        persistence.save(
            Task(name="Task 2", description="Second task", group_id=group.id)
        )

        tasks = persistence.fetch_all(Task)
        assert len(tasks) == 2
        assert any(t.name == "Task 1" for t in tasks)

        tasks = persistence.fetch_all_tasks()
        assert len(tasks) == 2
        assert any(t[0].name == "Task 1" for t in tasks)

        tasks_by_group = persistence.fetch_tasks_by_task_group(group.id)
        assert len(tasks_by_group) == 2
        assert any(t[0].name == "Task 1" for t in tasks_by_group)

        task_1 = persistence.fetch(Task, task.id)
        assert task_1 is not None
        assert task_1.name == "Task 1"
        assert task_1.created_at is not None

        task_1.name = "Updated Task 1"
        previous_modified = task_1.updated_at
        persistence.save(task_1)
        updated_task_1 = persistence.fetch(Task, task.id)
        assert updated_task_1.name == "Updated Task 1"
        assert updated_task_1.updated_at > previous_modified

    def test_activity(self, persistence):
        """Test saving and fetching Activities, using existing TaskGroups and Tasks."""
        descriptions = ["First activity", "Second activity"]

        groups = persistence.fetch_all(TaskGroup)
        tasks = persistence.fetch_all(Task)
        group = groups[0]
        task = tasks[0]

        activity = persistence.save(
            Activity(group_id=group.id, task_id=task.id, description=descriptions[0])
        )
        assert activity.id is not None
        assert activity.started is not None
        assert activity.ended is None
        assert activity.elapsed is None
        assert activity.elapsed_hms is None

        activity.ended = activity.started + timedelta(seconds=120)
        activity = persistence.save(activity)
        assert activity.elapsed == 120
        assert activity.elapsed_hms == "00:02:00"

        activity.elapsed = 9999
        activity = persistence.save(activity)
        assert activity.elapsed == 120
        assert activity.elapsed_hms == "00:02:00"

        persistence.save(
            Activity(group_id=group.id, task_id=task.id, description=descriptions[1])
        )

        activities = persistence.fetch_all(Activity)
        assert len(activities) == 2
        assert any(a.description == descriptions[0] for a in activities)

        logger.info("Activity: " + str(activities[0]))

        first_activity = persistence.fetch(Activity, activity.id)
        assert first_activity is not None
        assert first_activity.description == descriptions[0]
        assert first_activity.started is not None
        assert first_activity.ended is not None
        assert first_activity.elapsed == 120

        first_activity_joined = persistence.fetch_activity(activity.id)
        assert first_activity_joined is not None
        assert first_activity_joined[0].description == descriptions[0]
        assert first_activity_joined[1].name == task.name
        assert first_activity_joined[2].name == group.name

        logger.info("Activity with joins: " + str(first_activity_joined))

    def test_delete(self, persistence):
        """Test soft deleting and fetching deleted records."""
        activities = persistence.fetch_all(Activity)
        activity = activities[0]

        persistence.delete(activity)

        deleted_activity = persistence.fetch(Activity, activity.id)
        assert deleted_activity is None

        all_activities = persistence.delete_many(activities)
        assert all_activities is None
