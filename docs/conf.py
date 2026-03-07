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
"""Sphinx configuration for PyTaskTracker documentation."""

import os
import sys

# Make the src/ package importable without installation.
sys.path.insert(0, os.path.abspath("../src"))

# Pre-import FastAPI so it lands in sys.modules before autodoc's dynamic
# importer runs.  Sphinx 9's importer can trigger Pydantic forward-reference
# evaluation in an environment where typing.Dict isn't in scope; using the
# already-cached module avoids that re-execution entirely.
import fastapi  # noqa: F401

# ---------------------------------------------------------------------------
# Project metadata
# ---------------------------------------------------------------------------
project = "PyTaskTracker"
copyright = "2026, James G Willmore"
author = "James G Willmore"
release = "0.1.0"

# ---------------------------------------------------------------------------
# Extensions
# ---------------------------------------------------------------------------
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
]

# ---------------------------------------------------------------------------
# Napoleon (Google-style docstrings)
# ---------------------------------------------------------------------------
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_use_admonition_for_notes = True

# ---------------------------------------------------------------------------
# Autodoc
# ---------------------------------------------------------------------------
autodoc_member_order = "bysource"
autodoc_typehints = "description"
autodoc_typehints_format = "short"

# nicegui starts up its event loop on import; mock it so autodoc can import
# gui_api without a running server.
autodoc_mock_imports = ["nicegui"]

# ---------------------------------------------------------------------------
# Intersphinx — link to Python standard library docs
# ---------------------------------------------------------------------------
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

# ---------------------------------------------------------------------------
# HTML output
# ---------------------------------------------------------------------------
html_theme = "furo"
html_title = "PyTaskTracker"
templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
