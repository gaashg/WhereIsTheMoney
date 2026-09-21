# WhereIsTheMoney — Copyright (C) 2026 GaashG
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version. See <https://www.gnu.org/licenses/>.
#
# Additional terms under Section 7(b): see the NOTICE file.

"""Tests for the categories_learner.py entry point in the project root.

Not to be confused with services.categories_learner, which does the learning.
"""

import runpy

import pytest

import categories_learner
from input import console_input
from services import categories_learner as learner_service
from utils import logging_config


@pytest.fixture
def recorded(monkeypatch):
    """Replace learn() and setup_logger(), and record the calls made to them."""
    calls: dict = {"learn": [], "setup_logger": 0}

    def fake_learn(input_supplier):
        calls["learn"].append(input_supplier)

    def fake_setup_logger():
        calls["setup_logger"] += 1

    monkeypatch.setattr(learner_service, "learn", fake_learn)
    monkeypatch.setattr(logging_config, "setup_logger", fake_setup_logger)
    return calls


# --- positive cases ---------------------------------------------------------


def test_main_learns_from_the_console(recorded):
    categories_learner.main()

    assert recorded["learn"] == [console_input.supply_input]


def test_main_passes_the_function_not_its_result(recorded):
    """supply_input would ask for input if it were called here."""
    categories_learner.main()

    assert callable(recorded["learn"][0])


def test_running_as_a_script_sets_up_logging_and_learns(recorded):
    runpy.run_module("categories_learner", run_name="__main__")

    assert recorded["setup_logger"] == 1
    assert recorded["learn"] == [console_input.supply_input]


# --- negative cases ---------------------------------------------------------


def test_importing_does_not_start_learning(recorded):
    runpy.run_module("categories_learner", run_name="categories_learner")

    assert recorded["setup_logger"] == 0
    assert recorded["learn"] == []


def test_failures_in_learn_reach_the_caller(monkeypatch):
    def failing_learn(input_supplier):
        raise RuntimeError("boom")

    monkeypatch.setattr(learner_service, "learn", failing_learn)

    with pytest.raises(RuntimeError, match="boom"):
        categories_learner.main()
