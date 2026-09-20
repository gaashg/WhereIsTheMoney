# WhereIsTheMoney — Copyright (C) 2026 GaashG
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version. See <https://www.gnu.org/licenses/>.
#
# Additional terms under Section 7(b): see the NOTICE file.

"""Tests for utils.config.

Each test writes its own config.toml into a temporary folder and points the
WITM_CONFIG_PATH variable at it, so the real config.toml is never touched.
"""

import tomllib

import pytest

from utils import config

SAMPLE = """
log_level = "INFO"
retries = 0
verbose = false
empty_note = ""

[console_input]
max_attempts = 3
prompts = ["first", "second"]

[empty_section]
"""


@pytest.fixture
def write_config(tmp_path, monkeypatch):
    """Return a function that writes a config file and makes the module use it."""

    def write(text: str = SAMPLE) -> None:
        config_file = tmp_path / "config.toml"
        config_file.write_text(text, encoding="utf-8")
        monkeypatch.setenv(config.CONFIG_PATH_ENV_VAR, str(config_file))
        # The loader caches its result, so drop what an earlier test cached.
        config._load_toml.cache_clear()

    yield write
    config._load_toml.cache_clear()


# --- positive cases ---------------------------------------------------------


def test_returns_value_from_section(write_config):
    write_config()
    assert config.get_value("max_attempts", "console_input") == 3


def test_returns_top_level_value_without_section(write_config):
    write_config()
    assert config.get_value("log_level") == "INFO"


def test_returns_list_value(write_config):
    write_config()
    assert config.get_value("prompts", "console_input") == ["first", "second"]


@pytest.mark.parametrize(
    ("key", "expected"),
    [("retries", 0), ("verbose", False), ("empty_note", "")],
)
def test_returns_falsy_values(write_config, key, expected):
    """A value of 0, false or "" is present and must not count as missing."""
    write_config()
    assert config.get_value(key) == expected


def test_empty_section_is_read_as_a_section(write_config):
    write_config()
    with pytest.raises(config.ConfigError):
        config.get_value("anything", "empty_section")


def test_file_is_read_only_once(write_config):
    write_config()
    config.get_value("log_level")
    config.get_value("max_attempts", "console_input")
    assert config._load_toml.cache_info().misses == 1


def test_env_variable_overrides_the_default_path(write_config, monkeypatch):
    write_config('log_level = "DEBUG"')
    assert config.get_value("log_level") == "DEBUG"

    monkeypatch.delenv(config.CONFIG_PATH_ENV_VAR)
    assert config._config_path() == config.DEFAULT_CONFIG_PATH


def test_default_is_returned_when_the_key_is_missing(write_config):
    write_config()
    assert config.get_value("no_such_key", "console_input", default=7) == 7


def test_default_of_none_is_honoured(write_config):
    """None is a legal default, and must not be mistaken for "no default"."""
    write_config()
    assert config.get_value("no_such_key", default=None) is None


def test_default_is_ignored_when_the_key_exists(write_config):
    write_config()
    assert config.get_value("max_attempts", "console_input", default=7) == 3


# --- negative cases ---------------------------------------------------------


@pytest.mark.parametrize("key", ["", None])
def test_missing_key_argument_raises_value_error(write_config, key):
    write_config()
    with pytest.raises(ValueError):
        config.get_value(key)


def test_unknown_top_level_key_raises_config_error(write_config):
    write_config()
    with pytest.raises(config.ConfigError):
        config.get_value("no_such_key")


def test_unknown_key_in_section_raises_config_error(write_config):
    write_config()
    with pytest.raises(config.ConfigError):
        config.get_value("no_such_key", "console_input")


def test_unknown_section_raises_config_error(write_config):
    write_config()
    with pytest.raises(config.ConfigError):
        config.get_value("max_attempts", "no_such_section")


def test_section_key_lookup_does_not_fall_back_to_top_level(write_config):
    """log_level exists at the top level, but not inside console_input."""
    write_config()
    with pytest.raises(config.ConfigError):
        config.get_value("log_level", "console_input")


def test_error_message_names_the_missing_key(write_config):
    write_config()
    with pytest.raises(config.ConfigError, match="console_input.no_such_key"):
        config.get_value("no_such_key", "console_input")


def test_malformed_file_raises_decode_error(write_config):
    write_config("this is not = valid toml [[[")
    with pytest.raises(tomllib.TOMLDecodeError):
        config.get_value("log_level")


def test_missing_file_raises_file_not_found(tmp_path, monkeypatch):
    monkeypatch.setenv(config.CONFIG_PATH_ENV_VAR, str(tmp_path / "absent.toml"))
    config._load_toml.cache_clear()
    with pytest.raises(FileNotFoundError):
        config.get_value("log_level")
    config._load_toml.cache_clear()
