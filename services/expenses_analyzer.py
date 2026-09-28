# WhereIsTheMoney — Copyright (C) 2026 GaashG
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version. See <https://www.gnu.org/licenses/>.
#
# Additional terms under Section 7(b): see the NOTICE file.

from models.expense import Expense


def analyze_expenses(expenses: list[Expense], categories: dict[str, list[str]]) -> list[Expense]:
    expenses_categorized: list[Expense] = []
    for expense in expenses:
        expense_categories = categories.get(expense.shop)
        if expense_categories:
            expense.category1, expense.category2, expense.category3 = (expense_categories + [None, None, None])[:3]
            expenses_categorized.append(expense)

    return expenses_categorized
