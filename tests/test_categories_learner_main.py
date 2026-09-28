# WhereIsTheMoney — Copyright (C) 2026 GaashG
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version. See <https://www.gnu.org/licenses/>.
#
# Additional terms under Section 7(b): see the NOTICE file.

"""Tests for the menu in categories_learner.py, the project's entry point.

Not to be confused with services.categories_learner, which does the learning.
The two services are replaced by fakes, so only the menu itself is tested.
"""

import builtins
import runpy

import pytest

import categories_learner
from input import console_input
from services import categories_analyzer, categories_learner as learner_service
from utils import logging_config


@pytest.fixture
def menu(monkeypatch):
    """Answer the menu with the given choices, and record what was called."""
    calls: dict = {"learn": [], "categorize": [], "setup_logger": 0}

    def use(*choices: str):
        answers = iter(choices)

        def fake_input(prompt=""):
            # Running out of answers means the menu asked more often than it should.
            return next(answers)

        monkeypatch.setattr(builtins, "input", fake_input)

    monkeypatch.setattr(learner_service, "learn",
                        lambda supplier: calls["learn"].append(supplier))
    monkeypatch.setattr(categories_analyzer, "categorize_expenses",
                        lambda *args: calls["categorize"].append(args))
    monkeypatch.setattr(logging_config, "setup_logger",
                        lambda: calls.__setitem__("setup_logger", calls["setup_logger"] + 1))
    return use, calls


# --- positive cases ---------------------------------------------------------


def test_choosing_three_exits(menu):
    use, calls = menu
    use("3")

    assert categories_learner.main() is None
    assert (calls["learn"], calls["categorize"]) == ([], [])


def test_choosing_one_learns_new_categories(menu):
    use, calls = menu
    use("1", "3")

    categories_learner.main()

    assert calls["learn"] == [console_input.supply_input]


def test_choosing_two_categorizes_the_expenses(menu):
    use, calls = menu
    use("2", "3")

    categories_learner.main()

    assert calls["categorize"] == [(console_input.supply_input,)]


@pytest.mark.parametrize("choice, service", [("1", "learn"), ("2", "categorize")],
                         ids=["learning", "categorizing"])
def test_the_supplier_is_handed_over_and_not_called(menu, choice, service):
    """Called here, supply_input would ask for input before the service runs."""
    use, calls = menu
    use(choice, "3")

    categories_learner.main()

    handed_over = calls[service][0]
    assert callable(handed_over[0] if isinstance(handed_over, tuple) else handed_over)


def test_the_menu_keeps_asking_until_it_is_told_to_exit(menu):
    use, calls = menu
    use("1", "1", "3")

    categories_learner.main()

    assert len(calls["learn"]) == 2


def test_running_as_a_script_sets_up_logging(menu):
    use, calls = menu
    use("3")

    runpy.run_module("categories_learner", run_name="__main__")

    assert calls["setup_logger"] == 1


# --- negative cases ---------------------------------------------------------


@pytest.mark.parametrize("choice", ["", "4", "0", "one", " 3", "3 "],
                         ids=["nothing", "too high", "zero", "a word",
                              "a leading space", "a trailing space"])
def test_an_unknown_choice_is_refused_and_the_menu_asks_again(menu, capsys, choice):
    use, calls = menu
    use(choice, "3")

    categories_learner.main()

    assert "Invalid option" in capsys.readouterr().out
    assert (calls["learn"], calls["categorize"]) == ([], [])


def test_importing_does_not_show_the_menu(menu):
    use, calls = menu
    use()  # any question the menu asks would raise StopIteration

    runpy.run_module("categories_learner", run_name="categories_learner")

    assert calls["setup_logger"] == 0


def test_a_failure_in_a_service_reaches_the_caller(menu, monkeypatch):
    use, _ = menu
    use("1", "3")

    def failing_learn(supplier):
        raise RuntimeError("boom")

    monkeypatch.setattr(learner_service, "learn", failing_learn)

    with pytest.raises(RuntimeError, match="boom"):
        categories_learner.main()
