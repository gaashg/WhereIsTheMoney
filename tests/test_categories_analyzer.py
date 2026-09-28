# WhereIsTheMoney — Copyright (C) 2026 GaashG
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version. See <https://www.gnu.org/licenses/>.
#
# Additional terms under Section 7(b): see the NOTICE file.

"""Tests for services.categories_analyzer.

The parser, the analyzer and the writer have tests of their own, so here they
are replaced by fakes, and only what categorize_expenses() itself does is
tested: asking for input, merging the categories and handing the result over.
"""

import logging
from datetime import datetime

import pytest

from exceptions import ConfigError, FatalError
from models.expense import Expense
from parsers import categories_file_parser
from services import categories_analyzer, expenses_analyzer
from writers import expenses_analyzer_file_writer

FILE_PATH = "D:\\budget\\2024-11.xlsx"
MONTHS = [11]


def expense(shop="SUPER") -> Expense:
    return Expense(purchase_date=datetime(2024, 11, 9), shop=shop, category1=None,
                   category2=None, category3=None, purchase_amount=10.0)


def supplier(months=None):
    return lambda: (FILE_PATH, MONTHS if months is None else months)


@pytest.fixture
def world(monkeypatch):
    """Replace everything around the service, and record how it was called."""
    calls: dict = {"parsed": [], "analyzed": [], "written": []}
    results: dict = {"expenses": [expense()], "new": {}, "existing": {}}

    def raise_if_needed(outcome):
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    def fake_parse(file_path, months_range):
        calls["parsed"].append((file_path, months_range))
        return raise_if_needed(results["expenses"]), raise_if_needed(results["new"])

    def fake_existing():
        return raise_if_needed(results["existing"])

    def fake_analyze(expenses, categories):
        calls["analyzed"].append((expenses, categories))
        return raise_if_needed(results.get("analyzed", expenses))

    def fake_write(month, year, categorized_expenses):
        calls["written"].append((month, year, categorized_expenses))
        raise_if_needed(results.get("write"))

    monkeypatch.setattr(categories_file_parser, "parse_expenses_file", fake_parse)
    monkeypatch.setattr(categories_file_parser, "parse_existing_categories", fake_existing)
    monkeypatch.setattr(expenses_analyzer, "analyze_expenses", fake_analyze)
    monkeypatch.setattr(expenses_analyzer_file_writer, "write_categorized_expenses", fake_write)
    return calls, results


# --- positive cases ---------------------------------------------------------


def test_the_input_is_handed_to_the_parser(world):
    calls, _ = world

    categories_analyzer.categorize_expenses(supplier())

    assert calls["parsed"] == [(FILE_PATH, MONTHS)]


def test_the_supplier_is_asked_once(world):
    asked = []

    def counting_supplier():
        asked.append(True)
        return FILE_PATH, MONTHS

    categories_analyzer.categorize_expenses(counting_supplier)

    assert len(asked) == 1


def test_the_expenses_of_the_file_are_the_ones_analyzed(world):
    calls, results = world
    expenses = [expense("SUPER"), expense("AMAZON")]
    results["expenses"] = expenses

    categories_analyzer.categorize_expenses(supplier())

    assert calls["analyzed"][0][0] == expenses


def test_the_new_and_the_existing_categories_are_merged_for_the_analysis(world):
    calls, results = world
    results["new"] = {"NETFLIX": ["תקשורת"]}
    results["existing"] = {"SUPER": ["מזון"]}

    categories_analyzer.categorize_expenses(supplier())

    assert calls["analyzed"][0][1] == {"NETFLIX": ["תקשורת"], "SUPER": ["מזון"]}


@pytest.mark.parametrize(
    "new, existing, merged",
    [
        (None, {"SUPER": ["מזון"]}, {"SUPER": ["מזון"]}),
        ({"SUPER": ["מזון"]}, {}, {"SUPER": ["מזון"]}),
        (None, {}, {}),
    ],
    ids=["no categories in the file", "nothing learned before", "nothing at all"],
)
def test_missing_categories_are_merged_as_empty(world, new, existing, merged):
    calls, results = world
    results["new"], results["existing"] = new, existing

    categories_analyzer.categorize_expenses(supplier())

    assert calls["analyzed"][0][1] == merged


def test_the_analyzed_expenses_are_the_ones_written(world):
    calls, results = world
    categorized = [expense("SUPER")]
    results["analyzed"] = categorized

    categories_analyzer.categorize_expenses(supplier())

    assert [written[2] for written in calls["written"]] == [categorized]


def test_a_file_is_written_for_every_month_of_the_range(world):
    calls, _ = world

    categories_analyzer.categorize_expenses(supplier(months=[9, 10, 11]))

    assert [written[0] for written in calls["written"]] == [9, 10, 11]


# --- handled failures: logged, nothing written ------------------------------


def test_expenses_that_were_not_found_are_not_written(world, caplog):
    calls, results = world
    results["expenses"] = None

    with caplog.at_level(logging.ERROR):
        categories_analyzer.categorize_expenses(supplier())

    assert calls["written"] == []
    assert calls["analyzed"] == []
    assert "No expenses" in caplog.text


def test_an_empty_file_is_not_written(world):
    calls, results = world
    results["expenses"] = []

    categories_analyzer.categorize_expenses(supplier())

    assert calls["written"] == []


@pytest.mark.parametrize(
    "error",
    [FileNotFoundError("gone"), ValueError("No purchase date in the table could be read")],
    ids=["file not found", "value error"],
)
def test_a_parser_failure_is_logged_and_nothing_is_written(world, caplog, error):
    calls, results = world
    results["expenses"] = error

    with caplog.at_level(logging.ERROR):
        categories_analyzer.categorize_expenses(supplier())

    assert calls["written"] == []
    assert FILE_PATH in caplog.text
    assert str(error) in caplog.text


def test_a_supplier_failure_is_logged_and_nothing_is_parsed(world, caplog):
    calls, _ = world

    def failing_supplier():
        raise ValueError("bad input")

    with caplog.at_level(logging.ERROR):
        categories_analyzer.categorize_expenses(failing_supplier)

    assert calls["parsed"] == []
    assert "bad input" in caplog.text


# --- negative cases: failures that stop the application ---------------------


def test_running_out_of_input_attempts_stops_the_application(world):
    def exhausted_supplier():
        raise FatalError("Maximum number of attempts (3) has reached. Exiting")

    with pytest.raises(FatalError):
        categories_analyzer.categorize_expenses(exhausted_supplier)


def test_a_missing_config_value_is_not_swallowed(world):
    _, results = world
    results["existing"] = ConfigError("Key categories.existing_categories_folder was not found")

    with pytest.raises(ConfigError):
        categories_analyzer.categorize_expenses(supplier())


def test_a_write_failure_that_is_not_about_the_file_is_not_swallowed(world):
    _, results = world
    results["write"] = PermissionError("the file is open in another program")

    with pytest.raises(PermissionError):
        categories_analyzer.categorize_expenses(supplier())
