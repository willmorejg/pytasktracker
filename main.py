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
"""The main module of the pytasktracker package."""

import os
from dataclasses import dataclass
from enum import Enum
from typing import Annotated

import click
from dataclass_click import dataclass_click, option

from logging_config import configure_logging

logger = configure_logging()

CONTEXT_SETTINGS = {"max_content_width": 120, "show_default": True}


class ApplicationMode(Enum):
    """Application modes."""

    CLI = "cli"
    REST = "rest"
    GUI = "gui"


@dataclass
class CLIOptions:
    """Options for the CLI."""

    port: Annotated[
        int,
        option(
            "--port",
            type=int,
            help="Port to run the application on",
            required=False,
            default=8088,
        ),
    ] = 0

    database_url: Annotated[
        str,
        option(
            "--database-url",
            type=str,
            help="Database URL to connect to",
            required=False,
            default="duckdb:///:memory:",
        ),
    ] = "duckdb:///:memory:"

    recreate_db: Annotated[
        bool,
        option(
            "--recreate-db",
            is_flag=True,
            help="(Re)create the database on startup",
            required=False,
            default=False,
        ),
    ] = False

    mode: Annotated[
        ApplicationMode,
        option(
            "--mode",
            type=click.Choice([e.value for e in ApplicationMode]),
            help="Application mode to run",
            required=False,
            default=ApplicationMode.GUI.value,
        ),
    ] = ApplicationMode.GUI


class CLI:
    """Command line interface for the application."""

    def __init__(self, options: CLIOptions):
        """Initialize the CLI."""
        self.options = options

    def run(self):
        """Run the CLI."""
        logger.info("Running the CLI...")
        self.validate_options()

    def validate_options(self):
        """Validate the CLI options."""
        logger.info("Validating CLI options...")

        mode_selected = self.options.mode
        logger.info(f"Selected application mode: {mode_selected}")
        port_selected = self.options.port
        logger.info(f"Selected port: {port_selected}")
        database_url_selected = self.options.database_url
        if database_url_selected is not None:
            os.environ["DATABASE_URL"] = database_url_selected
        if self.options.recreate_db:
            os.environ["RECREATE_DB"] = "true"
        logger.info(f"Selected database URL: {database_url_selected}")
        logger.info(f"Recreate database on startup: {self.options.recreate_db}")

        match mode_selected:
            case ApplicationMode.CLI.value:
                logger.info("Running in CLI mode.")
            case ApplicationMode.REST.value:
                import uvicorn

                from mods.rest_api import app

                uvicorn.run(app, host="127.0.0.1", port=port_selected, reload=True)
                logger.info("Running in REST mode.")
            case ApplicationMode.GUI.value:
                from mods.gui_api import GuiApp

                gui_api = GuiApp()
                gui_api.start_gui(port=port_selected)
                logger.info("Running in GUI mode.")
            case _:
                logger.error(f"Invalid application mode: {mode_selected}")


@logger.catch
@click.command(context_settings=CONTEXT_SETTINGS)
@dataclass_click(CLIOptions)
def main(options: CLIOptions = CLIOptions()):
    """Pytasktracker - A task tracking application."""
    cli = CLI(options)
    cli.run()
    logger.info("Hello from pytasktracker!", {"foo": "bar"})


if __name__ == "__main__":
    main()
