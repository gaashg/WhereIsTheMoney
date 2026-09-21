# WhereIsTheMoney — Copyright (C) 2026 GaashG
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version. See <https://www.gnu.org/licenses/>.
#
# Additional terms under Section 7(b): see the NOTICE file.

"""Tests for file_readers.categories_file_reader.

Each test points the config at a temporary folder, so the real categories file
is never read.
"""

import json
import os

import pytest

from exceptions import ConfigError
from file_readers import categories_file_reader
from utils import config

FILE_NAME = "existingCategories.json"


@pytest.fixture
def categories_file(tmp_path, monkeypatch):
    """Configure tmp_path as the categories folder and return the file's path.

    The folder ends with a separator, as in config.toml, because the reader
    joins the folder and the file name as plain strings.
    """
    config_file = tmp_path / "config.toml"
    config_file.write_text(
        "[categories]\n"
        f"existing_categories_folder = '{tmp_path}{os.sep}'\n"
        f"existing_categories_file_name = '{FILE_NAME}'\n",
        encoding="utf-8")
    monkeypatch.setenv(config.CONFIG_PATH_ENV_VAR, str(config_file))
    config._load_toml.cache_clear()
    yield tmp_path / FILE_NAME
    config._load_toml.cache_clear()


# --- positive cases ---------------------------------------------------------


def test_reads_the_categories_from_the_file(categories_file):
    categories = {"NETFLIX": ["תקשורת", "טלוויזיה"], "SUPER": ["מזון"]}
    categories_file.write_text(json.dumps(categories), encoding="utf-8")

    assert categories_file_reader.read_categories_file() == categories


def test_hebrew_written_as_is_is_read_back(categories_file):
    """The file is read as UTF-8, not in Windows' default encoding."""
    categories_file.write_text('{"שופרסל": ["מזון", "סופר"]}', encoding="utf-8")

    assert categories_file_reader.read_categories_file() == {"שופרסל": ["מזון", "סופר"]}


def test_hebrew_written_as_escapes_is_read_back(categories_file):
    """json.dumps writes \\uXXXX escapes by default; they read back the same."""
    categories_file.write_text(json.dumps({"שופרסל": ["מזון"]}), encoding="utf-8")

    assert categories_file_reader.read_categories_file() == {"שופרסל": ["מזון"]}


def test_a_shop_with_no_categories_is_kept(categories_file):
    categories_file.write_text('{"CASH": []}', encoding="utf-8")

    assert categories_file_reader.read_categories_file() == {"CASH": []}


def test_an_empty_json_object_gives_an_empty_dictionary(categories_file):
    categories_file.write_text("{}", encoding="utf-8")

    assert categories_file_reader.read_categories_file() == {}


def test_a_missing_file_gives_an_empty_dictionary(categories_file):
    assert not categories_file.exists()

    assert categories_file_reader.read_categories_file() == {}


def test_an_empty_file_gives_an_empty_dictionary(categories_file):
    categories_file.write_bytes(b"")

    assert categories_file_reader.read_categories_file() == {}


def test_the_file_is_left_untouched(categories_file):
    content = '{"SUPER": ["מזון"]}'
    categories_file.write_text(content, encoding="utf-8")

    categories_file_reader.read_categories_file()

    assert categories_file.read_text(encoding="utf-8") == content


# --- negative cases ---------------------------------------------------------


@pytest.mark.parametrize(
    "content",
    ["not json", '{"SUPER": ["מזון"]', "{'SUPER': ['מזון']}", "   ", "\n"],
    ids=["plain text", "cut short", "single quotes", "spaces only", "newline only"],
)
def test_a_file_that_is_not_json_raises(categories_file, content):
    """Only a file of zero bytes counts as empty; whitespace is invalid JSON."""
    categories_file.write_text(content, encoding="utf-8")

    with pytest.raises(json.JSONDecodeError):
        categories_file_reader.read_categories_file()


def test_the_decode_error_is_a_value_error(categories_file):
    """categories_learner.learn() catches ValueError, which covers this error."""
    categories_file.write_text("not json", encoding="utf-8")

    with pytest.raises(ValueError):
        categories_file_reader.read_categories_file()


def test_a_config_without_the_categories_section_raises(tmp_path, monkeypatch):
    config_file = tmp_path / "config.toml"
    config_file.write_text("[console_input]\nmax_attempts = 3\n", encoding="utf-8")
    monkeypatch.setenv(config.CONFIG_PATH_ENV_VAR, str(config_file))
    config._load_toml.cache_clear()

    try:
        with pytest.raises(ConfigError, match="categories.existing_categories_folder"):
            categories_file_reader.read_categories_file()
    finally:
        config._load_toml.cache_clear()
