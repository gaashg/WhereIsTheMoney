# WhereIsTheMoney — Copyright (C) 2026 GaashG
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version. See <https://www.gnu.org/licenses/>.
#
# Additional terms under Section 7(b): see the NOTICE file.

from pathlib import Path

SUPPORTED_FILE_EXTENSIONS = frozenset({".xlsx", ".xls", ".csv", ".xlsm", ".xlsb", ".ods"})


def validate_file_path(file_path_str: str | None):
    if file_path_str is None or file_path_str == "":
        raise ValueError("No file path was supplied. Please supply a full path")

    file_path = Path(file_path_str)
    if not file_path.exists() or not file_path.is_file():
        raise FileNotFoundError(f"File not found in the supplied path: {file_path_str}")

    if file_path.suffix not in SUPPORTED_FILE_EXTENSIONS:
        raise ValueError("Supplied file type is not supported")


def validate_dates_range(dates_range_str: str | None):
    if not dates_range_str:
        raise ValueError("No dates range was supplied. Enter a valid dates range")
