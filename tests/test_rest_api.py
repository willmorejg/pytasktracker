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
"""REST API tests providing 100% endpoint coverage."""

from datetime import timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_group(name=None, description="test"):
    return rest_api.service.create_task_group(
        name=name or f"Group {uuid4()}", description=description
    )


def _make_task(group, name=None, description=None):
    return rest_api.service.create_task(
        task_group=group, name=name or f"Task {uuid4()}", description=description
    )


def _make_activity(task, description=None):
    return rest_api.service.create_activity(task=task, description=description)


# ---------------------------------------------------------------------------
# Chrome DevTools probe
# ---------------------------------------------------------------------------

def test_chrome_devtools_probe(client):
    response = client.get("/.well-known/appspecific/com.chrome.devtools.json")
    assert response.status_code == 200
    assert response.json() == {}


# ---------------------------------------------------------------------------
# Task Group endpoints
# ---------------------------------------------------------------------------

def test_get_task_groups_returns_only_visible(client):
    visible = _make_group()
    hidden = _make_group()
    rest_api.service.soft_delete_task_group(hidden)

    response = client.get("/task_groups")
    assert response.status_code == 200
    ids = {g["id"] for g in response.json()}
    assert visible.id in ids
    assert hidden.id not in ids


def test_get_task_groups_all_returns_every_group(client):
    visible = _make_group()
    hidden = _make_group()
    rest_api.service.soft_delete_task_group(hidden)

    response = client.get("/task_groups/all")
    assert response.status_code == 200
    ids = {g["id"] for g in response.json()}
    assert visible.id in ids
    assert hidden.id in ids


def test_create_task_group(client):
    name = f"New Group {uuid4()}"
    response = client.post("/task_groups", json={"name": name, "description": "desc"})
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == name
    assert data["show"] is True


def test_update_task_group(client):
    group = _make_group(description="original")
    group.description = "updated"
    response = client.put("/task_groups", json=group.model_dump(mode="json"))
    assert response.status_code == 200
    assert response.json()["description"] == "updated"


def test_soft_delete_task_group(client):
    group = _make_group()
    response = client.patch(f"/task_groups/{group.id}")
    assert response.status_code == 200
    assert response.json() is True
    assert rest_api.service.get_task_group_by_id(group.id).show is False


def test_enable_task_group(client):
    group = _make_group()
    rest_api.service.soft_delete_task_group(group)

    response = client.patch(f"/task_groups/{group.id}/enable")
    assert response.status_code == 200
    assert response.json() is True
    assert rest_api.service.get_task_group_by_id(group.id).show is True


def test_create_task_group_duplicate_name_returns_400(client):
    """IntegrityError handler: duplicate unique name yields 400."""
    name = f"Unique Group {uuid4()}"
    client.post("/task_groups", json={"name": name})
    response = client.post("/task_groups", json={"name": name})
    assert response.status_code == 400
    assert "error" in response.json()


# ---------------------------------------------------------------------------
# Task endpoints
# ---------------------------------------------------------------------------

def test_get_tasks_returns_only_visible(client):
    group = _make_group()
    visible = _make_task(group)
    hidden = _make_task(group)
    rest_api.service.soft_delete_task(hidden)

    response = client.get("/tasks")
    assert response.status_code == 200
    ids = {t["id"] for t in response.json()}
    assert visible.id in ids
    assert hidden.id not in ids


def test_get_tasks_all_returns_every_task(client):
    group = _make_group()
    visible = _make_task(group)
    hidden = _make_task(group)
    rest_api.service.soft_delete_task(hidden)

    response = client.get("/tasks/all")
    assert response.status_code == 200
    ids = {t["id"] for t in response.json()}
    assert visible.id in ids
    assert hidden.id in ids


def test_create_task(client):
    group = _make_group()
    task_name = f"New Task {uuid4()}"
    response = client.post(
        "/tasks",
        json={
            "task": {"name": task_name, "group_id": group.id},
            "task_group": group.model_dump(mode="json"),
        },
    )
    assert response.status_code == 200
    assert response.json()["name"] == task_name


def test_update_task(client):
    group = _make_group()
    task = _make_task(group, description=None)

    response = client.put(
        "/tasks",
        json={
            "id": task.id,
            "name": task.name,
            "description": "Updated description",
            "group_id": task.group_id,
            "show": task.show,
        },
    )
    assert response.status_code == 200

    result = rest_api.service.get_task_by_id(task.id)
    assert result is not None
    updated_task, _ = result
    assert updated_task.description == "Updated description"
    assert updated_task.name == task.name
    assert updated_task.created_at is not None


def test_update_task_not_found_returns_404(client):
    """BaseAppException handler: unknown task ID yields 404."""
    response = client.put(
        "/tasks",
        json={
            "id": str(uuid4()),
            "name": "Ghost Task",
            "description": None,
            "group_id": str(uuid4()),
            "show": True,
        },
    )
    assert response.status_code == 404
    assert "error" in response.json()


def test_soft_delete_task(client):
    group = _make_group()
    task = _make_task(group)

    response = client.patch(f"/tasks/{task.id}")
    assert response.status_code == 200
    assert response.json() is True

    result = rest_api.service.get_task_by_id(task.id)
    assert result is not None
    assert result[0].show is False


def test_enable_task(client):
    group = _make_group()
    task = _make_task(group)
    rest_api.service.soft_delete_task(task)

    response = client.patch(f"/tasks/{task.id}/enable")
    assert response.status_code == 200
    assert response.json() is True

    result = rest_api.service.get_task_by_id(task.id)
    assert result is not None
    assert result[0].show is True


# ---------------------------------------------------------------------------
# Activity endpoints
# ---------------------------------------------------------------------------

def test_get_activities_returns_elapsed_hms(client):
    """GET /activities exposes elapsed_hms and omits elapsed."""
    group = _make_group()
    task = _make_task(group)
    activity = _make_activity(task, description="API display test")
    activity.ended = activity.started + timedelta(seconds=125)
    rest_api.service.modify_activity(activity)

    response = client.get("/activities")
    assert response.status_code == 200
    matching = [item for item in response.json() if item["id"] == activity.id]
    assert matching
    item = matching[0]
    assert item["elapsed_hms"] == "00:02:05"
    assert "elapsed" not in item


def test_create_activity(client):
    group = _make_group()
    task = _make_task(group)

    response = client.post("/activities", json=task.model_dump(mode="json"))
    assert response.status_code == 200
    assert response.json()["task_id"] == task.id


def test_create_activity_with_description(client):
    group = _make_group()
    task = _make_task(group)

    response = client.post(
        "/activities?description=my+desc", json=task.model_dump(mode="json")
    )
    assert response.status_code == 200
    assert response.json()["description"] == "my desc"


def test_update_activity(client):
    group = _make_group()
    task = _make_task(group)
    activity = _make_activity(task)

    response = client.put(
        "/activities",
        json={
            "id": activity.id,
            "task_id": activity.task_id,
            "group_id": activity.group_id,
            "description": "updated desc",
            "started": activity.started.isoformat() if activity.started else None,
            "ended": None,
            "elapsed": None,
        },
    )
    assert response.status_code == 200
    assert response.json()["description"] == "updated desc"


def test_end_activity(client):
    group = _make_group()
    task = _make_task(group)
    activity = _make_activity(task)

    response = client.patch(f"/activities/{activity.id}/end")
    assert response.status_code == 200
    assert response.json() is True

    result = rest_api.service.get_activity_by_id(activity.id)
    assert result is not None
    assert result[0].ended is not None


def test_get_filtered_activities_no_params(client):
    response = client.get("/activities/filtered")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_filtered_activities_with_date_range(client):
    group = _make_group()
    task = _make_task(group)
    activity = _make_activity(task)
    activity.ended = activity.started + timedelta(hours=1)
    rest_api.service.modify_activity(activity)

    start = (activity.started - timedelta(days=1)).isoformat()
    end = (activity.ended + timedelta(days=1)).isoformat()
    response = client.get(f"/activities/filtered?start_date={start}&end_date={end}")
    assert response.status_code == 200
    ids = {a["id"] for a in response.json()}
    assert activity.id in ids


def test_get_filtered_activities_exact_flags(client):
    response = client.get("/activities/filtered?exact_start=true&exact_end=true")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


# ---------------------------------------------------------------------------
# General exception handler
# ---------------------------------------------------------------------------

def test_general_exception_handler():
    """Unhandled exceptions yield 400 with a generic error message."""
    with TemporaryDirectory() as tmp_dir:
        database_path = Path(tmp_dir) / "test_api.duckdb"
        rest_api.service = Services(f"duckdb:///{database_path}", recreate=True)
        with patch.object(
            rest_api.service, "get_all_task_groups", side_effect=RuntimeError("boom")
        ):
            no_raise_client = TestClient(rest_api.app, raise_server_exceptions=False)
            response = no_raise_client.get("/task_groups")
    assert response.status_code == 400
    assert response.json() == {"error": "An unexpected error occurred."}
