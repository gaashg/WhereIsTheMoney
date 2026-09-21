# WhereIsTheMoney — Copyright (C) 2026 GaashG
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version. See <https://www.gnu.org/licenses/>.
#
# Additional terms under Section 7(b): see the NOTICE file.

"""Tests for parsers.categories_file_parser.

The xlsx reader has tests of its own, so here it is replaced by a fake that
hands over a ready list of expenses, and only the conversion is tested.
"""

import logging
from datetime import datetime

import pytest

from file_readers import categories_file_reader, xlsx_file_reader
from models.expense import Expense
from parsers import categories_file_parser
from parsers.categories_file_parser import CATEGORY_CONFLICT

MONTHS = [10]


def expense(shop="NETFLIX", category1="תקשורת", category2=None, category3=None) -> Expense:
    return Expense(purchase_date=datetime(2024, 10, 9), shop=shop,
                   category1=category1, category2=category2, category3=category3)


@pytest.fixture
def read(monkeypatch):
    """Return a function that makes the reader hand over the given result."""

    def hand_over(result):
        paths = []

        def fake_read_file(file_path):
            paths.append(file_path)
            return result

        monkeypatch.setattr(xlsx_file_reader, "read_file", fake_read_file)
        return paths

    return hand_over


def parse():
    return categories_file_parser.parse_categories_file("expenses.xlsx", MONTHS)


def conflict_messages(caplog) -> list[str]:
    return [r.getMessage() for r in caplog.records
            if "different categories" in r.getMessage()]


# --- positive cases ---------------------------------------------------------


def test_the_file_path_is_passed_to_the_reader(read):
    paths = read([])

    parse()

    assert paths == ["expenses.xlsx"]


def test_shops_map_to_their_categories_in_level_order(read):
    read([expense("NETFLIX", "תקשורת", "טלוויזיה", "נטפליקס"),
          expense("SUPER", "מזון", "סופר", "שבועי")])

    assert parse() == {
        "NETFLIX": ["תקשורת", "טלוויזיה", "נטפליקס"],
        "SUPER": ["מזון", "סופר", "שבועי"],
    }


@pytest.mark.parametrize(
    "levels, expected",
    [
        (("תקשורת", None, None), ["תקשורת"]),
        (("תקשורת", "טלוויזיה", None), ["תקשורת", "טלוויזיה"]),
        (("תקשורת", None, "נטפליקס"), ["תקשורת", "נטפליקס"]),
        ((None, None, None), []),
    ],
    ids=["category1 only", "no category3", "no category2", "no categories"],
)
def test_empty_categories_are_left_out(read, levels, expected):
    read([expense("NETFLIX", *levels)])

    assert parse() == {"NETFLIX": expected}


def test_a_shop_repeated_with_the_same_categories_appears_once(read):
    read([expense("SUPER", "מזון", "סופר")] * 3)

    assert parse() == {"SUPER": ["מזון", "סופר"]}


def test_no_expenses_give_an_empty_dictionary(read):
    read([])

    assert parse() == {}


# --- lists where one goes further than the other ----------------------------


@pytest.mark.parametrize(
    "first, second",
    [
        (("מזון",), ("מזון", "סופר")),
        (("מזון", "סופר"), ("מזון",)),
        (("מזון",), ("מזון", "סופר", "שבועי")),
        (("מזון", "סופר", "שבועי"), ("מזון",)),
        ((None,), ("מזון", "סופר")),
    ],
    ids=["longer comes second", "longer comes first", "two levels further",
         "two levels shorter", "no categories at all"],
)
def test_the_longer_of_two_agreeing_lists_is_kept(read, first, second):
    read([expense("SUPER", *first), expense("SUPER", *second)])

    longest = max((first, second), key=lambda levels: len([x for x in levels if x]))
    assert parse() == {"SUPER": [level for level in longest if level]}


def test_the_longest_list_wins_across_many_expenses(read):
    read([expense("SUPER", "מזון"),
          expense("SUPER", "מזון", "סופר", "שבועי"),
          expense("SUPER", "מזון", "סופר")])

    assert parse() == {"SUPER": ["מזון", "סופר", "שבועי"]}


def test_a_longer_list_is_not_logged_as_a_conflict(read, caplog):
    read([expense("SUPER", "מזון"), expense("SUPER", "מזון", "סופר")])

    with caplog.at_level(logging.WARNING):
        parse()

    assert conflict_messages(caplog) == []


# --- lists that part ways: the conflict takes the level they differ in ------


@pytest.mark.parametrize(
    "first, second, marked",
    [
        (("קניות", "ספרים"), ("פנאי", "ספרים"), [CATEGORY_CONFLICT]),
        (("מזון", "סופר"), ("מזון", "מכולת"), ["מזון", CATEGORY_CONFLICT]),
        (("מזון", "סופר"), ("מזון", "מכולת", "שבועי"), ["מזון", CATEGORY_CONFLICT]),
        (("מזון", "סופר", "שבועי"), ("מזון", "סופר", "חודשי"),
         ["מזון", "סופר", CATEGORY_CONFLICT]),
        (("מזון", "סופר", "שבועי"), ("מזון", "מכולת", "שבועי"),
         ["מזון", CATEGORY_CONFLICT]),
    ],
    ids=["first level differs", "second level differs", "second differs, one is longer",
         "last level differs", "a level after the difference matches again"],
)
def test_the_conflict_is_marked_where_the_lists_differ(read, first, second, marked):
    read([expense("SUPER", *first), expense("SUPER", *second)])

    assert parse() == {"SUPER": marked}


def test_the_marker_text(read):
    assert CATEGORY_CONFLICT == "category conflict"


def test_a_conflict_is_logged_with_all_the_lists(read, caplog):
    read([expense("SUPER", "מזון", "סופר"), expense("SUPER", "מזון", "מכולת")])

    with caplog.at_level(logging.WARNING):
        parse()

    assert conflict_messages(caplog) == [
        "Shop SUPER appears with different categories (['מזון', 'סופר'] and "
        "['מזון', 'מכולת']), marking the conflict: ['מזון', 'category conflict']"]


def test_a_marked_list_does_not_grow_again(read):
    read([expense("SUPER", "מזון", "סופר"),
          expense("SUPER", "מזון", "מכולת"),
          expense("SUPER", "מזון", "סופר", "שבועי")])

    assert parse() == {"SUPER": ["מזון", CATEGORY_CONFLICT]}


def test_a_conflict_at_the_same_level_is_logged_once(read, caplog):
    read([expense("SUPER", "מזון", "סופר"),
          expense("SUPER", "מזון", "מכולת"),
          expense("SUPER", "מזון", "סופר"),
          expense("SUPER", "מזון", "אחר", "שבועי"),
          expense("SUPER", "מזון")])

    with caplog.at_level(logging.WARNING):
        assert parse() == {"SUPER": ["מזון", CATEGORY_CONFLICT]}

    assert len(conflict_messages(caplog)) == 1


def test_a_conflict_moves_up_when_an_earlier_level_differs(read, caplog):
    read([expense("SUPER", "מזון", "סופר", "שבועי"),
          expense("SUPER", "מזון", "סופר", "חודשי"),
          expense("SUPER", "מזון", "מכולת"),
          expense("SUPER", "קניות")])

    with caplog.at_level(logging.WARNING):
        assert parse() == {"SUPER": [CATEGORY_CONFLICT]}

    assert len(conflict_messages(caplog)) == 3


def test_a_first_level_conflict_stays_for_later_expenses(read, caplog):
    read([expense("AMAZON", "קניות", "ספרים"),
          expense("AMAZON", "פנאי", "ספרים"),
          expense("AMAZON", "קניות", "ספרים"),
          expense("AMAZON", "חינוך")])

    with caplog.at_level(logging.WARNING):
        assert parse() == {"AMAZON": [CATEGORY_CONFLICT]}

    assert len(conflict_messages(caplog)) == 1


def test_two_longer_lists_that_disagree_are_marked(read):
    """Both go further than ["מזון"], but not the same way."""
    read([expense("SUPER", "מזון"),
          expense("SUPER", "מזון", "סופר"),
          expense("SUPER", "מזון", "מכולת")])

    assert parse() == {"SUPER": ["מזון", CATEGORY_CONFLICT]}


def test_a_conflict_leaves_other_shops_alone(read):
    read([expense("SUPER", "מזון", "סופר"),
          expense("NETFLIX", "תקשורת", "טלוויזיה"),
          expense("SUPER", "מזון", "מכולת"),
          expense("NETFLIX", "תקשורת", "טלוויזיה", "נטפליקס")])

    assert parse() == {"SUPER": ["מזון", CATEGORY_CONFLICT],
                       "NETFLIX": ["תקשורת", "טלוויזיה", "נטפליקס"]}


# --- dropped expenses -------------------------------------------------------


def test_an_expense_without_a_shop_is_dropped_and_logged(read, caplog):
    read([expense("SHOP"), expense(None, "מזון")])

    with caplog.at_level(logging.WARNING):
        assert parse() == {"SHOP": ["תקשורת"]}

    assert "Entry 1 has no shop, dropping it" in caplog.text


# --- negative cases ---------------------------------------------------------


def test_no_suitable_table_returns_none(read):
    read(None)

    assert parse() is None


def test_reader_errors_are_not_swallowed(monkeypatch):
    def failing_read_file(file_path):
        raise FileNotFoundError(file_path)

    monkeypatch.setattr(xlsx_file_reader, "read_file", failing_read_file)

    with pytest.raises(FileNotFoundError):
        parse()


# --- parse_existing_categories ----------------------------------------------


def test_existing_categories_come_from_the_categories_file(monkeypatch):
    saved = {"SUPER": ["מזון"], "AMAZON": [CATEGORY_CONFLICT]}
    monkeypatch.setattr(categories_file_reader, "read_categories_file", lambda: saved)

    assert categories_file_parser.parse_existing_categories() == saved


def test_no_existing_categories_give_an_empty_dictionary(monkeypatch):
    monkeypatch.setattr(categories_file_reader, "read_categories_file", lambda: {})

    assert categories_file_parser.parse_existing_categories() == {}


def test_a_broken_categories_file_is_not_swallowed(monkeypatch):
    def failing_read():
        raise ValueError("Expecting value")

    monkeypatch.setattr(categories_file_reader, "read_categories_file", failing_read)

    with pytest.raises(ValueError):
        categories_file_parser.parse_existing_categories()
