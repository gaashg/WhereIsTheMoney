# WhereIsTheMoney — Copyright (C) 2026 GaashG
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version. See <https://www.gnu.org/licenses/>.
#
# Additional terms under Section 7(b): see the NOTICE file.

"""Tests for services.expenses_analyzer.

The categories the analyzer works with are the ones the parser produces: a
shop's name pointing at up to three levels, sometimes ending with the conflict
marker.
"""

from datetime import datetime

import pytest

from models.expense import Expense
from parsers.categories_file_parser import CATEGORY_CONFLICT
from services import expenses_analyzer


def expense(shop="SUPER", category1=None, category2=None, category3=None,
            purchase_amount=10.0) -> Expense:
    return Expense(purchase_date=datetime(2024, 11, 9), shop=shop,
                   category1=category1, category2=category2, category3=category3,
                   purchase_amount=purchase_amount, billing_amount=purchase_amount)


def levels(one: Expense) -> list:
    return [one.category1, one.category2, one.category3]


# --- positive cases ---------------------------------------------------------


@pytest.mark.parametrize(
    "known, expected",
    [
        (["מזון"], ["מזון", None, None]),
        (["מזון", "מכולת"], ["מזון", "מכולת", None]),
        (["מזון", "מכולת", "שבועי"], ["מזון", "מכולת", "שבועי"]),
        ([CATEGORY_CONFLICT], [CATEGORY_CONFLICT, None, None]),
    ],
    ids=["one level", "two levels", "three levels", "a conflict"],
)
def test_a_shops_categories_are_copied_into_its_expenses(known, expected):
    one = expense("SUPER")

    expenses_analyzer.analyze_expenses([one], {"SUPER": known})

    assert levels(one) == expected


def test_the_categorized_expenses_are_returned():
    one = expense("SUPER")

    assert expenses_analyzer.analyze_expenses([one], {"SUPER": ["מזון"]}) == [one]


def test_every_expense_of_a_known_shop_is_categorized():
    first, second = expense("SUPER"), expense("SUPER")

    result = expenses_analyzer.analyze_expenses([first, second], {"SUPER": ["מזון"]})

    assert len(result) == 2
    assert levels(first) == levels(second) == ["מזון", None, None]


def test_the_order_of_the_expenses_is_kept():
    expenses = [expense("A"), expense("B"), expense("C")]
    categories = {"A": ["1"], "B": ["2"], "C": ["3"]}

    result = expenses_analyzer.analyze_expenses(expenses, categories)

    assert [one.shop for one in result] == ["A", "B", "C"]


def test_the_rest_of_an_expense_is_left_alone():
    one = expense("SUPER", purchase_amount=54.9)

    expenses_analyzer.analyze_expenses([one], {"SUPER": ["מזון"]})

    assert (one.purchase_date, one.shop, one.purchase_amount,
            one.billing_amount) == (datetime(2024, 11, 9), "SUPER", 54.9, 54.9)


def test_categories_already_on_the_expense_are_replaced():
    one = expense("SUPER", "ישן", "ישן יותר", "הישן מכל")

    expenses_analyzer.analyze_expenses([one], {"SUPER": ["מזון", "מכולת"]})

    assert levels(one) == ["מזון", "מכולת", None]


def test_a_shop_is_looked_up_by_its_whole_name():
    one = expense("SUPER PHARM")

    expenses_analyzer.analyze_expenses([one], {"SUPER": ["מזון"]})

    assert levels(one) == [None, None, None]


def test_more_than_three_levels_fill_the_three_there_are():
    one = expense("SUPER")

    expenses_analyzer.analyze_expenses([one], {"SUPER": ["a", "b", "c", "d"]})

    assert levels(one) == ["a", "b", "c"]


# --- negative cases ---------------------------------------------------------


def test_no_expenses_give_no_result():
    assert expenses_analyzer.analyze_expenses([], {"SUPER": ["מזון"]}) == []


def test_no_categories_leave_every_expense_as_it_is():
    one = expense("SUPER")

    result = expenses_analyzer.analyze_expenses([one], {})

    assert result == []
    assert levels(one) == [None, None, None]


def test_an_unknown_shop_is_left_out_of_the_result():
    known, unknown = expense("SUPER"), expense("AMAZON")

    result = expenses_analyzer.analyze_expenses([known, unknown], {"SUPER": ["מזון"]})

    assert result == [known]
    assert levels(unknown) == [None, None, None]


def test_a_shop_with_an_empty_list_of_categories_is_left_out():
    one = expense("SUPER")

    result = expenses_analyzer.analyze_expenses([one], {"SUPER": []})

    assert result == []
    assert levels(one) == [None, None, None]


def test_an_expense_without_a_shop_is_left_out():
    one = expense(None)

    result = expenses_analyzer.analyze_expenses([one], {"SUPER": ["מזון"]})

    assert result == []
    assert levels(one) == [None, None, None]
