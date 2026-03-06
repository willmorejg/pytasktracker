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
import re
from playwright.sync_api import Playwright, sync_playwright, expect


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("http://127.0.0.1:8099/")
    page.get_by_role("button").click()
    page.get_by_text("Manage Task Groups").click()
    page.get_by_role("button", name="Create New Task Group").click()
    page.get_by_role("textbox", name="Name").click()
    page.get_by_role("textbox", name="Name").fill("Playwright")
    page.get_by_role("button", name="Submit").click()
    page.get_by_role("button").filter(has_text="menu").click()
    page.get_by_role("listitem").filter(has_text="Manage Tasks").click()
    page.get_by_role("button", name="Create New Task").click()
    page.get_by_text("arrow_drop_down").click()
    page.get_by_text("Playwright").click()
    page.get_by_role("textbox", name="Name").click()
    page.get_by_role("textbox", name="Name").fill("Playwright task")
    page.get_by_role("button", name="Submit").click()
    page.get_by_role("button").filter(has_text="menu").click()
    page.get_by_text("Manage Activities").click()
    page.get_by_role("button", name="Create New Activity").click()
    page.locator("div").filter(has_text=re.compile(r"^arrow_drop_down$")).click()
    page.get_by_text("Playwright - Playwright task").click()
    page.get_by_role("button", name="Submit").click()

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
