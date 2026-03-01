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


def build_datetime(
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
