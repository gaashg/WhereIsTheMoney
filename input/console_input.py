# WhereIsTheMoney — Copyright (C) 2026 GaashG
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version. See <https://www.gnu.org/licenses/>.
#
# Additional terms under Section 7(b): see the NOTICE file.
import logging
import re

from exceptions import FatalError
from utils import config
from validators import console_input_validator

logger = logging.getLogger(__name__)

ALL_MONTHS = "all"
FIRST_MONTH = 1
LAST_MONTH = 12

# Accepted shapes: "3", "5, 6" (at least one comma) and "4-6".
_MONTH = r"\d{1,2}"
SINGLE_MONTH = re.compile(rf"\s*{_MONTH}\s*")
MONTHS_LIST = re.compile(rf"\s*{_MONTH}\s*(?:,\s*{_MONTH}\s*)+")
MONTHS_RANGE = re.compile(rf"\s*{_MONTH}\s*-\s*{_MONTH}\s*")


def supply_input() -> tuple:
    max_attempts = config.get_value("max_attempts", "console_input")
    file_path = get_file_path_input(max_attempts)
    months_range = get_months_range(max_attempts)

    return file_path, months_range


def get_file_path_input(max_attempts: int) -> str | None:
    if max_attempts < 1:
        raise ValueError(f"max_attempts must be at least 1, got {max_attempts}")

    for attempt in range(max_attempts):
        file_path = input("Hello, which file would you like me to learn today? Write a "
                          f"full path ({max_attempts - attempt} attempts are left")
        try:
            console_input_validator.validate_file_path(file_path)
            return file_path
        except (ValueError, FileNotFoundError) as ex:
            if attempt < max_attempts - 1:
                print("That didn't go very well... Enter a valid file path (failure"
                      f"reason: {ex}")
                logger.warning(
                    f"Failed to validate file: attempt={attempt}, reason={ex}")
            else:
                print("Maximum number of attempts reached. Exiting. Bye bye...")
                raise FatalError(f"Maximum number of attempts ({max_attempts}) has "
                                 f"reached. Exiting")
    return None


def format_months_range(months_range: str) -> list[int]:
    """Turn "all", "3", "5, 6" or "4-6" into the months they stand for."""
    months_range = months_range.strip()
    if months_range.lower() == ALL_MONTHS:
        return list(range(FIRST_MONTH, LAST_MONTH + 1))

    if SINGLE_MONTH.fullmatch(months_range):
        return _to_months(months_range)

    if MONTHS_LIST.fullmatch(months_range):
        return _to_months(*months_range.split(","))

    if MONTHS_RANGE.fullmatch(months_range):
        first, last = _to_months(*months_range.split("-"))
        if first > last:
            raise ValueError(f"Range starts after it ends: {months_range}")
        return list(range(first, last + 1))

    raise ValueError(f"Unsupported dates range: {months_range}. Supported formats "
                     f"are: all | 3 | 5, 6 | 4-6")


def _to_months(*months: str) -> list[int]:
    """Convert the matched parts to numbers, rejecting anything outside 1-12."""
    numbers = [int(month) for month in months]
    for number in numbers:
        if not FIRST_MONTH <= number <= LAST_MONTH:
            raise ValueError(f"Month out of range: {number}. Months are "
                             f"{FIRST_MONTH}-{LAST_MONTH}")

    return numbers


def get_months_range(max_attempts: int) -> list[int] | None:
    if max_attempts < 1:
        raise ValueError(f"max_attempts must be at least 1, got {max_attempts}")

    for attempt in range(max_attempts):
        months_range = input("Great!! Now, tell me which months to learn (format options"
                             ": [all | 3 | 5, 6 | 4-6]")
        try:
            console_input_validator.validate_dates_range(months_range)
            return format_months_range(months_range)
        except (ValueError, FileNotFoundError) as ex:
            if attempt < max_attempts - 1:
                print("That didn't go very well... Enter a valid dates range (failure"
                      f"reason: {ex}")
                logger.warning(
                    f"Failed to validate months range: attempt={attempt}, reason={ex}")
            else:
                print("Maximum number of attempts reached. Exiting. Bye bye...")
                raise FatalError(f"Maximum number of attempts ({max_attempts}) has "
                                 f"reached. Exiting")

    return None
