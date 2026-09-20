# WhereIsTheMoney — Copyright (C) 2026 GaashG
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version. See <https://www.gnu.org/licenses/>.
#
# Additional terms under Section 7(b): see the NOTICE file.

"""Tests for validators.console_input_validator.

Files are created under pytest's tmp_path, so nothing real is touched.
"""

import pytest

from validators import console_input_validator as validator

SUPPORTED = sorted(validator.SUPPORTED_FILE_EXTENSIONS)


@pytest.fixture
def existing_file(tmp_path):
    """Return a function creating a file with the given name, and its path."""

    def create(name: str) -> str:
        file_path = tmp_path / name
        file_path.write_text("content", encoding="utf-8")
        return str(file_path)

    return create


# --- validate_file_path, positive cases -------------------------------------


@pytest.mark.parametrize("extension", SUPPORTED)
def test_every_supported_extension_is_accepted(existing_file, extension):
    validator.validate_file_path(existing_file(f"report{extension}"))


def test_a_name_with_several_dots_uses_the_last_one(existing_file):
    """report.2026.xlsx is an xlsx file: only the final suffix counts."""
    validator.validate_file_path(existing_file("report.2026.xlsx"))


def test_valid_file_returns_none(existing_file):
    """The validator reports by raising, so a good path returns nothing."""
    assert validator.validate_file_path(existing_file("report.csv")) is None


# --- validate_file_path, negative cases -------------------------------------


@pytest.mark.parametrize("file_path", [None, ""])
def test_missing_file_path_raises_value_error(file_path):
    with pytest.raises(ValueError, match="No file path was supplied"):
        validator.validate_file_path(file_path)


def test_unknown_path_raises_file_not_found(tmp_path):
    with pytest.raises(FileNotFoundError, match="File not found"):
        validator.validate_file_path(str(tmp_path / "absent.xlsx"))


def test_directory_is_not_a_file(tmp_path):
    """The path exists, but is a folder, so is_file() rejects it."""
    folder = tmp_path / "reports.xlsx"
    folder.mkdir()
    with pytest.raises(FileNotFoundError):
        validator.validate_file_path(str(folder))


@pytest.mark.parametrize("name", ["notes.txt", "report.pdf", "report", "report."])
def test_unsupported_extension_raises_value_error(existing_file, name):
    with pytest.raises(ValueError, match="not supported"):
        validator.validate_file_path(existing_file(name))


def test_extension_check_is_case_sensitive(existing_file):
    """.XLSX is not in the supported set, so it is rejected as things stand."""
    with pytest.raises(ValueError, match="not supported"):
        validator.validate_file_path(existing_file("REPORT.XLSX"))


def test_error_message_names_the_path(tmp_path):
    missing = str(tmp_path / "absent.xlsx")
    with pytest.raises(FileNotFoundError, match="absent.xlsx"):
        validator.validate_file_path(missing)


# --- validate_dates_range ---------------------------------------------------


@pytest.mark.parametrize("dates_range", ["all", "3", "5, 6", "4-6", "nonsense", " "])
def test_any_non_empty_dates_range_is_accepted(dates_range):
    """This validator only checks for emptiness; the format is checked later."""
    assert validator.validate_dates_range(dates_range) is None


@pytest.mark.parametrize("dates_range", [None, ""])
def test_empty_dates_range_raises_value_error(dates_range):
    with pytest.raises(ValueError, match="No dates range was supplied"):
        validator.validate_dates_range(dates_range)
