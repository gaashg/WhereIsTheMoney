# WhereIsTheMoney — Copyright (C) 2026 GaashG
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version. See <https://www.gnu.org/licenses/>.
#
# Additional terms under Section 7(b): see the NOTICE file.

"""Tests for utils.logging_config.

setup_logger() changes the root logger and writes a file, so each test runs in
a temporary folder and puts the root logger back the way it was.
"""

import logging
import logging.handlers

import pytest

from utils import logging_config


@pytest.fixture
def setup_in_tmp_path(tmp_path, monkeypatch):
    """Call setup_logger() in a temporary folder, then restore the root logger.

    basicConfig() does nothing when the root logger already has handlers, and
    pytest installs its own, so they are cleared just before the call.
    """
    root = logging.getLogger()
    saved_handlers, saved_level = root.handlers[:], root.level
    monkeypatch.chdir(tmp_path)

    def setup() -> logging.Logger:
        root.handlers = []
        logging_config.setup_logger()
        return root

    yield setup
    for handler in root.handlers:
        handler.close()
    root.handlers, root.level = saved_handlers, saved_level


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


# --- negative cases ---------------------------------------------------------


def test_debug_messages_are_dropped(setup_in_tmp_path, tmp_path):
    setup_in_tmp_path()
    logging.getLogger("some.module").debug("invisible")
    logging.getLogger().handlers[0].flush()

    written = (tmp_path / "reports_parser.log").read_text(encoding="utf-8")
    assert "invisible" not in written
