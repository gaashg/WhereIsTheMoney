# WhereIsTheMoney — Copyright (C) 2026 GaashG
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version. See <https://www.gnu.org/licenses/>.
#
# Additional terms under Section 7(b): see the NOTICE file.

"""Tests for parsers.parser.

parse_file() only reads the first bytes so far, so these tests cover what it
already does: opening the file, and the signature table it will match against.
"""

import pytest

from parsers import parser


# --- positive cases ---------------------------------------------------------


def test_an_existing_file_can_be_opened(tmp_path):
    file_path = tmp_path / "report.xlsx"
    file_path.write_bytes(b"PK\x03\x04rest of the file")
    parser.parse_file(str(file_path))


def test_a_file_shorter_than_the_header_is_read_without_failing(tmp_path):
    """read(8) returns what there is, so a tiny file must not blow up."""
    file_path = tmp_path / "tiny.xlsx"
    file_path.write_bytes(b"PK")
    parser.parse_file(str(file_path))


def test_the_zip_signature_maps_to_the_zip_based_formats():
    assert parser.FILE_TYPES[b"PK\x03\x04"] == [".xlsx", ".xlsm", ".ods"]


def test_parse_file_is_exported_by_the_package():
    from parsers import parse_file

    assert parse_file is parser.parse_file


# --- negative cases ---------------------------------------------------------


def test_missing_file_raises_file_not_found(tmp_path):
    with pytest.raises(FileNotFoundError):
        parser.parse_file(str(tmp_path / "absent.xlsx"))


def test_a_directory_cannot_be_parsed(tmp_path):
    with pytest.raises((IsADirectoryError, PermissionError, OSError)):
        parser.parse_file(str(tmp_path))
