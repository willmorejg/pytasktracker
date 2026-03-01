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
"""REST API tests for task group state changes."""

from datetime import timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from mods import rest_api
from services import Services


@pytest.fixture
def client():
    """Provide an isolated REST client backed by an in-memory database."""
    with TemporaryDirectory() as tmp_dir:
        database_path = Path(tmp_dir) / "test_api.duckdb"
        rest_api.service = Services(f"duckdb:///{database_path}", recreate=True)
        yield TestClient(rest_api.app)


def test_task_group_enable_endpoint_sets_show_true(client):
    """Disable then enable a task group via REST endpoints."""
    task_group_name = f"Test Group {uuid4()}"

    create_response = client.post(
        "/task_groups",
        json={"name": task_group_name, "description": "API endpoint test"},
    )
    assert create_response.status_code == 200
    created_task_group = create_response.json()
    task_group_id = created_task_group["id"]

    disable_response = client.patch(f"/task_groups/{task_group_id}")
    assert disable_response.status_code == 200
    assert disable_response.json() is True

    all_groups_after_disable = client.get("/task_groups/all")
    assert all_groups_after_disable.status_code == 200
    disabled_group = next(
        (
            group
            for group in all_groups_after_disable.json()
            if group["id"] == task_group_id
        ),
        None,
    )
    assert disabled_group is not None
    assert disabled_group["show"] is False

    enable_response = client.patch(f"/task_groups/{task_group_id}/enable")
    assert enable_response.status_code == 200
    assert enable_response.json() is True

    all_groups_after_enable = client.get("/task_groups/all")
    assert all_groups_after_enable.status_code == 200
    enabled_group = next(
        (
            group
            for group in all_groups_after_enable.json()
            if group["id"] == task_group_id
        ),
        None,
    )
    assert enabled_group is not None
    assert enabled_group["show"] is True


def test_activities_endpoint_returns_elapsed_hms(client):
    """Verify the activities display payload exposes elapsed_hms instead of elapsed."""
    task_group = rest_api.service.create_task_group(
        name=f"Activities Group {uuid4()}", description="activities test"
    )
    task = rest_api.service.create_task(
        task_group=task_group,
        name=f"Activities Task {uuid4()}",
        description="activities test",
    )
    activity = rest_api.service.create_activity(
        task=task, description="API display test"
    )
    activity.ended = activity.started + timedelta(seconds=125)
    rest_api.service.modify_activity(activity)

    response = client.get("/activities")
    assert response.status_code == 200

    payload = response.json()
    matching = [item for item in payload if item["id"] == activity.id]
    assert matching

    item = matching[0]
    assert item["elapsed_hms"] == "00:02:05"
    assert "elapsed" not in item
