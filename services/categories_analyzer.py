# WhereIsTheMoney — Copyright (C) 2026 GaashG
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version. See <https://www.gnu.org/licenses/>.
#
# Additional terms under Section 7(b): see the NOTICE file.

import logging
from typing import Callable

from parsers import categories_file_parser
from services import expenses_analyzer
from writers import expenses_analyzer_file_writer

logger = logging.getLogger(__name__)


def categorize_expenses(input_supplier: Callable[[], tuple[str, list[int]]]):
    file_path = None
    try:
        # get and validate the input: the path to the input file and the months range
        file_path, months_range = input_supplier()
        logger.info("Going to get the categories from the expenses file(s)")
        expenses, new_categories = categories_file_parser.parse_expenses_file(file_path,
                                                                    months_range)
        logger.info("Going to get the previously used categories")
        existing_categories = categories_file_parser.parse_existing_categories()
        merged_categories = (new_categories or {}) | (existing_categories or {})
        logger.info("The categories are read, going to categorize expenses")
        if not expenses:
            logger.error("No expenses")
            return
        categorized_expenses = expenses_analyzer.analyze_expenses(expenses, merged_categories)
        for month in months_range:
            expenses_analyzer_file_writer.write_categorized_expenses(month, 2026, categorized_expenses)
    except (FileNotFoundError, ValueError) as ex:
        logger.exception("A failure happened during input file validation %s", file_path)
