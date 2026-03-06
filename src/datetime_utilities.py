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
"""Utility functions for datetime handling."""

from datetime import datetime

import arrow


def get_current_time() -> datetime:
    """Get the current local time as a naive datetime object."""
    return arrow.utcnow().to("local").naive


def start_of_day(value: datetime) -> datetime:
    """Get the start of the day for a given datetime."""
    return value.replace(hour=0, minute=0, second=0, microsecond=0)


def end_of_day(value: datetime) -> datetime:
    """Get the end of the day for a given datetime."""
    return value.replace(hour=23, minute=59, second=59, microsecond=999999)
