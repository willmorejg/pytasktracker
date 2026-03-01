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
"""Models for the application."""

from datetime import datetime
from uuid import uuid4

from sqlmodel import Field, SQLModel, text

from datetime_utilities import get_current_time


class TimestampMixin(SQLModel):
    """A mixin to add created_at and updated_at timestamp fields to a model."""

    created_at: datetime | None = Field(
        sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP")},
        nullable=False,
        index=True,
    )
    updated_at: datetime | None = Field(
        default_factory=get_current_time,
        sa_column_kwargs={"onupdate": get_current_time, "nullable": True},
        index=True,
    )


class SoftDeleteMixin(SQLModel):
    """A mixin to add soft delete functionality to a model."""

    show: bool = Field(default=True, index=True)


class ElapsedTimeMixin(SQLModel):
    """A mixin to add elapsed time tracking to a model."""

    started: datetime | None = Field(
        sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP")},
        nullable=False,
        index=True,
    )
    ended: datetime | None = Field(
        default=None,
        sa_column_kwargs={"onupdate": get_current_time, "nullable": True},
        index=True,
    )
    elapsed: int | None = Field(
        default=None,
        sa_column_kwargs={"nullable": True},
        index=True,
    )


class TaskGroup(TimestampMixin, SoftDeleteMixin, SQLModel, table=True):
    """A group of tasks."""

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    name: str = Field(index=True, unique=True)
    description: str | None = None


class Task(TimestampMixin, SoftDeleteMixin, SQLModel, table=True):
    """A task."""

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    name: str = Field(index=True, unique=True)
    description: str | None = None
    group_id: str = Field(foreign_key="taskgroup.id", index=True)


class Activity(ElapsedTimeMixin, SQLModel, table=True):
    """An activity."""

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    group_id: str = Field(foreign_key="taskgroup.id", index=True)
    task_id: str = Field(foreign_key="task.id", index=True)
    description: str | None = None
