# WhereIsTheMoney — Copyright (C) 2026 GaashG
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version. See <https://www.gnu.org/licenses/>.
#
# Additional terms under Section 7(b): see the NOTICE file.

"""Tests for models.expense and exceptions."""

from dataclasses import fields
from datetime import datetime

import pytest

from exceptions import ConfigError, FatalError
from models.expense import Expense


def an_expense(**changes) -> Expense:
    values = dict(purchase_date=datetime(2024, 10, 9), shop="NETFLIX",
                  category1="תקשורת", category2="טלוויזיה", category3=None)
    values.update(changes)
    return Expense(**values)


# --- Expense, positive cases ------------------------------------------------


def test_the_fields_and_their_order():
    """xlsx_file_reader takes its columns from these fields, in this order."""
    assert [field.name for field in fields(Expense)] == [
        "purchase_date", "shop", "category1", "category2", "category3"]


def test_expenses_with_the_same_values_are_equal():
    assert an_expense() == an_expense()


def test_expenses_differing_in_one_field_are_not_equal():
    assert an_expense() != an_expense(category3="נטפליקס")


def test_an_expense_can_be_built_from_a_dictionary():
    row = {"purchase_date": datetime(2024, 10, 9), "shop": "SUPER",
           "category1": "מזון", "category2": None, "category3": None}

    assert Expense(**row).shop == "SUPER"


# --- Expense, negative cases ------------------------------------------------


def test_a_missing_field_raises():
    with pytest.raises(TypeError):
        Expense(purchase_date=datetime(2024, 10, 9), shop="SUPER",  # type: ignore[call-arg]
                category1="מזון", category2=None)


def test_an_unknown_field_raises():
    with pytest.raises(TypeError):
        an_expense(amount=10.0)


# --- exceptions -------------------------------------------------------------


@pytest.mark.parametrize("error_type", [ConfigError, FatalError])
def test_project_errors_are_ordinary_exceptions(error_type):
    assert issubclass(error_type, Exception)


@pytest.mark.parametrize("error_type", [ConfigError, FatalError])
def test_project_errors_are_not_value_errors(error_type):
    """categories_learner.learn() catches ValueError; these must get past it."""
    assert not issubclass(error_type, ValueError)


@pytest.mark.parametrize("error_type", [ConfigError, FatalError])
def test_project_errors_carry_their_message(error_type):
    with pytest.raises(error_type, match="something went wrong"):
        raise error_type("something went wrong")
