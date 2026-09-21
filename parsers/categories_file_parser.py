# WhereIsTheMoney — Copyright (C) 2026 GaashG
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version. See <https://www.gnu.org/licenses/>.
#
# Additional terms under Section 7(b): see the NOTICE file.

import logging

from file_readers import xlsx_file_reader, categories_file_reader
from models.expense import Expense

logger = logging.getLogger(__name__)

# Stands in the level where a shop's expenses disagree, ending its list.
CATEGORY_CONFLICT = "category conflict"


def parse_categories_file(file_path: str, months_range: list[int]) -> dict | None:
    expenses = xlsx_file_reader.read_file(file_path)
    return None if expenses is None else _categories_by_shop(expenses)


def _categories_by_shop(expenses: list[Expense]) -> dict[str, list[str]]:
    """Each shop's categories, category1 first, with the empty ones left out.

    An expense without a shop has nothing to key its categories by, so it is
    dropped. When one list only goes further than the other (["a"] and
    ["a", "b"]), they agree, and the longer one is kept. When they part ways,
    the levels before the first difference are kept, and CATEGORY_CONFLICT
    takes the level where they differ (["a", "b"] and ["a", "c"] give
    ["a", CATEGORY_CONFLICT]). No category matches the conflict, so that
    shop's list never grows past it again.
    """
    categories: dict[str, list[str]] = {}
    for index, expense in enumerate(expenses):
        if expense.shop is None:
            logger.warning("Entry %s has no shop, dropping it: %s", index, expense)
            continue
        levels = [expense.category1, expense.category2, expense.category3]
        found = [level for level in levels if level is not None]
        known = categories.get(expense.shop)
        if known is None:
            categories[expense.shop] = found
            continue

        shared = _shared_start(known, found)
        if shared == known:
            # This expense repeats the known list or goes further on it.
            categories[expense.shop] = found
        elif shared != found:
            # The lists part ways: neither is the start of the other.
            marked = [*shared, CATEGORY_CONFLICT]
            # A conflict already marked at this level is no news.
            if marked != known:
                logger.warning("Shop %s appears with different categories (%s and %s), "
                               "marking the conflict: %s",
                               expense.shop, known, found, marked)
                categories[expense.shop] = marked
    return categories


def _shared_start(first: list[str], second: list[str]) -> list[str]:
    """The levels both lists begin with, up to their first difference."""
    shared = []
    for mine, theirs in zip(first, second):
        if mine != theirs:
            break
        shared.append(mine)
    return shared


def parse_existing_categories() -> dict[str, list[str]]:
    return categories_file_reader.read_categories_file()
