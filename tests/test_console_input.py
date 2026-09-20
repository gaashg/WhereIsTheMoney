# WhereIsTheMoney — Copyright (C) 2026 GaashG
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version. See <https://www.gnu.org/licenses/>.
#
# Additional terms under Section 7(b): see the NOTICE file.

"""Tests for input.console_input.

The console is never touched: builtins.input is replaced by a function that
hands out prepared answers, one per call.
"""

import pytest

from exceptions import FatalError
from input import console_input

ALL_TWELVE = list(range(1, 13))


@pytest.fixture
def answers(monkeypatch):
    """Return a function that feeds the given answers to input(), in order."""

    def feed(*prepared: str) -> list[str]:
        remaining = list(prepared)

        def fake_input(prompt: str = "") -> str:
            assert remaining, "input() was called more times than expected"
            return remaining.pop(0)

        monkeypatch.setattr("builtins.input", fake_input)
        return remaining

    return feed


@pytest.fixture
def excel_file(tmp_path):
    """A real file with a supported extension, so validation passes."""
    file_path = tmp_path / "report.xlsx"
    file_path.write_text("content", encoding="utf-8")
    return str(file_path)


# --- format_months_range, positive cases ------------------------------------


@pytest.mark.parametrize("months_range", ["all", "ALL", "All", "  all  "])
def test_all_returns_every_month(months_range):
    assert console_input.format_months_range(months_range) == ALL_TWELVE


@pytest.mark.parametrize(
    ("months_range", "expected"),
    [("3", [3]), ("12", [12]), ("1", [1]), ("  7 ", [7])],
)
def test_single_month(months_range, expected):
    assert console_input.format_months_range(months_range) == expected


@pytest.mark.parametrize(
    ("months_range", "expected"),
    [
        ("5, 6", [5, 6]),
        ("5,6", [5, 6]),
        ("1, 2, 3", [1, 2, 3]),
        (" 11 , 12 ", [11, 12]),
        ("6, 6", [6, 6]),
    ],
)
def test_months_list(months_range, expected):
    assert console_input.format_months_range(months_range) == expected


@pytest.mark.parametrize(
    ("months_range", "expected"),
    [
        ("4-6", [4, 5, 6]),
        ("4 - 6", [4, 5, 6]),
        ("1-12", ALL_TWELVE),
        ("6-6", [6]),
    ],
)
def test_months_range(months_range, expected):
    assert console_input.format_months_range(months_range) == expected


def test_every_result_is_a_list_of_ints():
    for months_range in ["all", "3", "5, 6", "4-6"]:
        result = console_input.format_months_range(months_range)
        assert all(isinstance(month, int) for month in result)


# --- format_months_range, negative cases ------------------------------------


@pytest.mark.parametrize("months_range", ["0", "13", "99", "0-3", "10-13"])
def test_month_out_of_range_is_rejected(months_range):
    with pytest.raises(ValueError, match="out of range"):
        console_input.format_months_range(months_range)


@pytest.mark.parametrize("months_range", ["6-4", "12-1"])
def test_backwards_range_is_rejected(months_range):
    with pytest.raises(ValueError, match="starts after it ends"):
        console_input.format_months_range(months_range)


@pytest.mark.parametrize(
    "months_range",
    ["", "   ", "everything", "2;3", "3-", "-3", "5,", ",5", "1.5", "3 4", "1-2-3"],
)
def test_unsupported_shapes_are_rejected(months_range):
    with pytest.raises(ValueError, match="Unsupported dates range"):
        console_input.format_months_range(months_range)


def test_error_message_lists_the_supported_formats():
    with pytest.raises(ValueError, match=r"all \| 3 \| 5, 6 \| 4-6"):
        console_input.format_months_range("nonsense")


# --- get_file_path_input ----------------------------------------------------


def test_file_path_accepted_on_the_first_attempt(answers, excel_file):
    answers(excel_file)
    assert console_input.get_file_path_input(3) == excel_file


def test_file_path_accepted_after_bad_attempts(answers, excel_file):
    remaining = answers("", "notes.txt", excel_file)
    assert console_input.get_file_path_input(3) == excel_file
    assert remaining == []


def test_file_path_attempts_run_out(answers):
    answers("bad", "worse", "worst")
    with pytest.raises(FatalError, match="Maximum number of attempts"):
        console_input.get_file_path_input(3)


def test_file_path_uses_no_more_attempts_than_allowed(answers, excel_file):
    """With one attempt left, a bad answer fails instead of asking again."""
    answers("bad")
    with pytest.raises(FatalError):
        console_input.get_file_path_input(1)


@pytest.mark.parametrize("max_attempts", [0, -1])
def test_file_path_rejects_a_non_positive_attempt_count(max_attempts):
    with pytest.raises(ValueError, match="at least 1"):
        console_input.get_file_path_input(max_attempts)


# --- get_months_range -------------------------------------------------------


def test_months_range_accepted_on_the_first_attempt(answers):
    answers("4-6")
    assert console_input.get_months_range(3) == [4, 5, 6]


def test_months_range_accepted_after_bad_attempts(answers):
    """An empty answer and a bad format are both retried."""
    remaining = answers("", "13", "all")
    assert console_input.get_months_range(3) == ALL_TWELVE
    assert remaining == []


def test_months_range_attempts_run_out(answers):
    answers("nonsense", "still nonsense")
    with pytest.raises(FatalError, match="Maximum number of attempts"):
        console_input.get_months_range(2)


@pytest.mark.parametrize("max_attempts", [0, -1])
def test_months_range_rejects_a_non_positive_attempt_count(max_attempts):
    with pytest.raises(ValueError, match="at least 1"):
        console_input.get_months_range(max_attempts)


# --- supply_input -----------------------------------------------------------


def test_supply_input_returns_the_path_and_the_months(answers, excel_file, monkeypatch):
    monkeypatch.setattr(console_input.config, "get_value", lambda *args, **kwargs: 3)
    answers(excel_file, "5, 6")
    assert console_input.supply_input() == (excel_file, [5, 6])


def test_supply_input_asks_for_the_file_first(answers, excel_file, monkeypatch):
    """The months are never asked for when the file path is given up on."""
    monkeypatch.setattr(console_input.config, "get_value", lambda *args, **kwargs: 1)
    remaining = answers("bad", "4-6")
    with pytest.raises(FatalError):
        console_input.supply_input()
    assert remaining == ["4-6"]
