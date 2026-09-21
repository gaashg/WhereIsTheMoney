# WhereIsTheMoney — Copyright (C) 2026 GaashG
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version. See <https://www.gnu.org/licenses/>.
#
# Additional terms under Section 7(b): see the NOTICE file.

"""Tests for utils.logging_config.

setup_logger() changes the root logger and writes a file, so each test points
the configured log folder at a temporary one and puts the root logger back the
way it was.
"""

import logging
import logging.handlers

import pytest

from exceptions import ConfigError
from utils import config, logging_config


def use_log_folder(tmp_path, monkeypatch, folder):
    """Make the config name folder as the log folder."""
    config_file = tmp_path / "config.toml"
    config_file.write_text(f"[logging]\nfolder = '{folder}'\n", encoding="utf-8")
    monkeypatch.setenv(config.CONFIG_PATH_ENV_VAR, str(config_file))
    config._load_toml.cache_clear()


@pytest.fixture
def setup_logger():
    """Return a function calling setup_logger(), and restore the root logger afterwards.

    basicConfig() does nothing when the root logger already has handlers, and
    pytest installs its own once the test starts, so they are cleared just
    before the call.
    """
    root = logging.getLogger()
    saved_handlers, saved_level = root.handlers[:], root.level

    def setup() -> logging.Logger:
        root.handlers = []
        logging_config.setup_logger()
        return root

    yield setup
    for handler in root.handlers:
        handler.close()
    root.handlers, root.level = saved_handlers, saved_level
    config._load_toml.cache_clear()


@pytest.fixture
def setup_in_tmp_path(tmp_path, monkeypatch, setup_logger):
    """Call setup_logger() with tmp_path as the configured log folder."""
    use_log_folder(tmp_path, monkeypatch, tmp_path)
    return setup_logger


# --- positive cases ---------------------------------------------------------


def test_installs_a_rotating_file_handler(setup_in_tmp_path):
    root = setup_in_tmp_path()
    handler = root.handlers[0]
    assert isinstance(handler, logging.handlers.RotatingFileHandler)


def test_rotation_limits(setup_in_tmp_path):
    root = setup_in_tmp_path()
    handler = root.handlers[0]
    assert handler.maxBytes == 5_000_000
    assert handler.backupCount == 3


def test_level_is_info(setup_in_tmp_path):
    assert setup_in_tmp_path().level == logging.INFO


def test_writes_to_the_log_file(setup_in_tmp_path, tmp_path):
    setup_in_tmp_path()
    logging.getLogger("some.module").info("hello")
    logging.getLogger().handlers[0].flush()

    written = (tmp_path / "reports_parser.log").read_text(encoding="utf-8")
    assert "hello" in written
    assert "INFO" in written
    assert "some.module" in written


def test_the_format_carries_the_line_number(setup_in_tmp_path, tmp_path):
    """%(lineno)d must render a number, not the literal text."""
    setup_in_tmp_path()
    logging.getLogger("some.module").info("hello")
    logging.getLogger().handlers[0].flush()

    written = (tmp_path / "reports_parser.log").read_text(encoding="utf-8")
    line_number = written.split("some.module:")[1].split(":")[0]
    assert line_number.isdigit()


def test_the_file_is_in_the_configured_folder(setup_in_tmp_path, tmp_path):
    root = setup_in_tmp_path()

    assert root.handlers[0].baseFilename == str(tmp_path / "reports_parser.log")


def test_a_missing_log_folder_is_created(tmp_path, monkeypatch, setup_logger):
    folder = tmp_path / "not" / "there" / "yet"
    use_log_folder(tmp_path, monkeypatch, folder)

    root = setup_logger()
    logging.getLogger("some.module").info("hello")
    root.handlers[0].flush()

    assert "hello" in (folder / "reports_parser.log").read_text(encoding="utf-8")


def test_an_existing_log_folder_is_reused(tmp_path, monkeypatch, setup_logger):
    folder = tmp_path / "logs"
    folder.mkdir()
    (folder / "other.txt").write_text("keep me", encoding="utf-8")
    use_log_folder(tmp_path, monkeypatch, folder)

    setup_logger()

    assert (folder / "other.txt").read_text(encoding="utf-8") == "keep me"


# --- negative cases ---------------------------------------------------------


def test_debug_messages_are_dropped(setup_in_tmp_path, tmp_path):
    setup_in_tmp_path()
    logging.getLogger("some.module").debug("invisible")
    logging.getLogger().handlers[0].flush()

    written = (tmp_path / "reports_parser.log").read_text(encoding="utf-8")
    assert "invisible" not in written


def test_a_config_without_a_log_folder_raises(tmp_path, monkeypatch, setup_logger):
    config_file = tmp_path / "config.toml"
    config_file.write_text("[console_input]\nmax_attempts = 3\n", encoding="utf-8")
    monkeypatch.setenv(config.CONFIG_PATH_ENV_VAR, str(config_file))
    config._load_toml.cache_clear()

    with pytest.raises(ConfigError, match="logging.folder"):
        setup_logger()


def test_a_log_folder_that_is_a_file_raises(tmp_path, monkeypatch, setup_logger):
    occupied = tmp_path / "logs"
    occupied.write_text("I am a file", encoding="utf-8")
    use_log_folder(tmp_path, monkeypatch, occupied)

    with pytest.raises(OSError):
        setup_logger()
