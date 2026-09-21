# WhereIsTheMoney — Copyright (C) 2026 GaashG
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version. See <https://www.gnu.org/licenses/>.
#
# Additional terms under Section 7(b): see the NOTICE file.

"""Tests for utils.categories_file_writer.

Each test points the config at a temporary folder, so the real categories file
is never written.
"""

import json
import logging
import os

import pytest

from exceptions import ConfigError
from file_readers import categories_file_reader
from utils import categories_file_writer, config

FILE_NAME = "existingCategories.json"
CATEGORIES = {"NETFLIX": ["תקשורת", "טלוויזיה"], "SUPER": ["מזון", "category conflict"]}


def configure(tmp_path, monkeypatch, folder: str):
    config_file = tmp_path / "config.toml"
    config_file.write_text(
        "[categories]\n"
        f"existing_categories_folder = '{folder}'\n"
        f"existing_categories_file_name = '{FILE_NAME}'\n",
        encoding="utf-8")
    monkeypatch.setenv(config.CONFIG_PATH_ENV_VAR, str(config_file))
    config._load_toml.cache_clear()


@pytest.fixture
def categories_file(tmp_path, monkeypatch):
    """Configure tmp_path as the categories folder and return the file's path."""
    configure(tmp_path, monkeypatch, f"{tmp_path}{os.sep}")
    yield tmp_path / FILE_NAME
    config._load_toml.cache_clear()


def written(categories_file):
    return json.loads(categories_file.read_text(encoding="utf-8"))


# --- positive cases ---------------------------------------------------------


def test_writes_the_categories_as_json(categories_file):
    categories_file_writer.write_categories_file(CATEGORIES)

    assert written(categories_file) == CATEGORIES


def test_an_empty_dictionary_is_written_as_an_empty_object(categories_file):
    categories_file_writer.write_categories_file({})

    assert written(categories_file) == {}


def test_an_existing_file_is_replaced(categories_file):
    categories_file.write_text('{"OLD": ["ישן"]}', encoding="utf-8")

    categories_file_writer.write_categories_file({"NEW": ["חדש"]})

    assert written(categories_file) == {"NEW": ["חדש"]}


def test_what_is_written_is_what_the_reader_reads(categories_file):
    categories_file_writer.write_categories_file(CATEGORIES)

    assert categories_file_reader.read_categories_file() == CATEGORIES


def test_the_file_is_created_when_missing(categories_file):
    assert not categories_file.exists()

    categories_file_writer.write_categories_file(CATEGORIES)

    assert categories_file.is_file()


def test_the_path_is_logged(categories_file, caplog):
    with caplog.at_level(logging.INFO):
        categories_file_writer.write_categories_file(CATEGORIES)

    assert f"Writing merged categories into file {categories_file}" in caplog.text


# --- negative cases ---------------------------------------------------------


def test_a_missing_folder_raises(tmp_path, monkeypatch):
    configure(tmp_path, monkeypatch, f"{tmp_path / 'no' / 'such' / 'folder'}{os.sep}")

    try:
        with pytest.raises(FileNotFoundError):
            categories_file_writer.write_categories_file(CATEGORIES)
    finally:
        config._load_toml.cache_clear()


def test_a_config_without_the_categories_section_raises(tmp_path, monkeypatch):
    config_file = tmp_path / "config.toml"
    config_file.write_text("[console_input]\nmax_attempts = 3\n", encoding="utf-8")
    monkeypatch.setenv(config.CONFIG_PATH_ENV_VAR, str(config_file))
    config._load_toml.cache_clear()

    try:
        with pytest.raises(ConfigError):
            categories_file_writer.write_categories_file(CATEGORIES)
    finally:
        config._load_toml.cache_clear()


def test_categories_that_are_not_json_raise(categories_file):
    with pytest.raises(TypeError):
        categories_file_writer.write_categories_file({"SUPER": {"מזון"}})  # a set
