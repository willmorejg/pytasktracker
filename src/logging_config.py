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
"""Logging configuration for the application."""

import logging
import sys

from loguru import logger


class InterceptHandler(logging.Handler):
    """Redirect stdlib logging records to loguru."""

    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log record."""
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = sys._getframe(6), 6
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def configure_logging():
    """Configure logging for the application."""
    logger.remove()  # Remove the default logger
    logger.add(
        "logs/pytasktracker.log",
        rotation="1 week",  # Rotate logs every week
        retention="4 weeks",  # Retain logs for 4 weeks
        compression="zip",  # Compress logs with zip
        level="DEBUG",  # Log all messages at DEBUG level and above
        format="{message}",  # Log format
        backtrace=True,  # Include backtrace in logs for better debugging
        diagnose=False,  # Include diagnostic information in logs
        serialize=True,  # Serialize logs in JSON format for better parsing and analysis
    )
    logger.add(
        sys.stdout,
        level="INFO",  # Log messages at INFO level and above to the console
        backtrace=True,  # Include backtrace in logs for better debugging
        diagnose=True,  # Include diagnostic information in logs
    )

    # Route stdlib logging (uvicorn, etc.) through loguru
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    for name in ("uvicorn", "uvicorn.access", "uvicorn.error"):
        logging.getLogger(name).handlers = [InterceptHandler()]
        logging.getLogger(name).propagate = False

    return logger
