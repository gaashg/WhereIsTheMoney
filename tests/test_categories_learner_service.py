# WhereIsTheMoney — Copyright (C) 2026 GaashG
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version. See <https://www.gnu.org/licenses/>.
#
# Additional terms under Section 7(b): see the NOTICE file.

"""Tests for services.categories_learner.

The parser and the writer have tests of their own, so here they are replaced by
fakes, and only learn()'s own work is tested: asking for input, merging and
handing the result over.
"""

import json
import logging

import pytest

from exceptions import ConfigError, FatalError
from parsers import categories_file_parser
from services import categories_learner
from utils import categories_file_writer

FILE_PATH = "D:\\budget\\2024-11.xlsx"
MONTHS = [10, 11]


def supplier(file_path=FILE_PATH, months=None):
    return lambda: (file_path, MONTHS if months is None else months)


@pytest.fixture
def world(monkeypatch):
    """Replace the parser and the writer, and record how they were called."""
    calls: dict = {"parsed": [], "written": []}
    results = {"new": {}, "existing": {}}

    def fake_parse(file_path, months_range):
        calls["parsed"].append((file_path, months_range))
        outcome = results["new"]
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    def fake_existing():
        outcome = results["existing"]
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    def fake_write(categories):
        calls["written"].append(categories)
        outcome = results.get("write")
        if isinstance(outcome, Exception):
            raise outcome

    monkeypatch.setattr(categories_file_parser, "parse_categories_file", fake_parse)
    monkeypatch.setattr(categories_file_parser, "parse_existing_categories", fake_existing)
    monkeypatch.setattr(categories_file_writer, "write_categories_file", fake_write)
    return calls, results


# --- positive cases ---------------------------------------------------------


def test_the_input_is_handed_to_the_parser(world):
    calls, _ = world

    categories_learner.learn(supplier())

    assert calls["parsed"] == [(FILE_PATH, MONTHS)]


def test_the_supplier_is_asked_once(world):
    asked = []

    def counting_supplier():
        asked.append(True)
        return FILE_PATH, MONTHS

    categories_learner.learn(counting_supplier)

    assert len(asked) == 1


def test_new_and_existing_shops_are_all_written(world):
    calls, results = world
    results["new"] = {"NETFLIX": ["תקשורת"]}
    results["existing"] = {"SUPER": ["מזון"]}

    categories_learner.learn(supplier())

    assert calls["written"] == [{"NETFLIX": ["תקשורת"], "SUPER": ["מזון"]}]


def test_a_shop_in_both_keeps_the_existing_categories(world):
    """a | b keeps b's value for a shared key, and existing_categories is b."""
    calls, results = world
    results["new"] = {"SUPER": ["מזון", "סופר"]}
    results["existing"] = {"SUPER": ["מזון"]}

    categories_learner.learn(supplier())

    assert calls["written"] == [{"SUPER": ["מזון"]}]


@pytest.mark.parametrize(
    "new, existing, merged",
    [
        (None, {"SUPER": ["מזון"]}, {"SUPER": ["מזון"]}),
        ({"SUPER": ["מזון"]}, {}, {"SUPER": ["מזון"]}),
        (None, {}, {}),
        ({}, {}, {}),
    ],
    ids=["no table in the file", "no existing categories", "nothing at all", "both empty"],
)
def test_missing_categories_are_merged_as_empty(world, new, existing, merged):
    calls, results = world
    results["new"], results["existing"] = new, existing

    categories_learner.learn(supplier())

    assert calls["written"] == [merged]


def test_the_inputs_are_not_changed_by_the_merge(world):
    _, results = world
    new, existing = {"NETFLIX": ["תקשורת"]}, {"SUPER": ["מזון"]}
    results["new"], results["existing"] = new, existing

    categories_learner.learn(supplier())

    assert new == {"NETFLIX": ["תקשורת"]}
    assert existing == {"SUPER": ["מזון"]}


# --- handled failures: logged, nothing written ------------------------------


@pytest.mark.parametrize(
    "error",
    [FileNotFoundError("gone"), ValueError("No purchase date in the table could be read")],
    ids=["file not found", "value error"],
)
def test_a_parser_failure_is_logged_and_nothing_is_written(world, caplog, error):
    calls, results = world
    results["new"] = error

    with caplog.at_level(logging.ERROR):
        categories_learner.learn(supplier())

    assert calls["written"] == []
    assert FILE_PATH in caplog.text
    assert str(error) in caplog.text


def test_a_broken_existing_categories_file_is_logged(world, caplog):
    """A JSONDecodeError is a ValueError, so it is handled like one."""
    calls, results = world
    results["existing"] = json.JSONDecodeError("Expecting value", "", 0)

    with caplog.at_level(logging.ERROR):
        categories_learner.learn(supplier())

    assert calls["written"] == []
    assert "Expecting value" in caplog.text


def test_a_supplier_failure_is_logged_and_nothing_is_parsed(world, caplog):
    calls, _ = world

    def failing_supplier():
        raise ValueError("bad input")

    with caplog.at_level(logging.ERROR):
        categories_learner.learn(failing_supplier)

    assert calls["parsed"] == []
    assert "bad input" in caplog.text


# --- negative cases: failures that stop the application ---------------------


def test_running_out_of_input_attempts_stops_the_application(world):
    def exhausted_supplier():
        raise FatalError("Maximum number of attempts (3) has reached. Exiting")

    with pytest.raises(FatalError):
        categories_learner.learn(exhausted_supplier)


def test_a_missing_config_value_is_not_swallowed(world):
    _, results = world
    results["new"] = ConfigError("Key categories_table_structure.columns_names was not found")

    with pytest.raises(ConfigError):
        categories_learner.learn(supplier())


def test_a_write_failure_other_than_file_not_found_is_not_swallowed(world):
    _, results = world
    results["write"] = PermissionError("the file is open in another program")

    with pytest.raises(PermissionError):
        categories_learner.learn(supplier())
