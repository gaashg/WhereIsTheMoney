# WhereIsTheMoney — Copyright (C) 2026 GaashG
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version. See <https://www.gnu.org/licenses/>.
#
# Additional terms under Section 7(b): see the NOTICE file.
import logging
from collections.abc import Callable

from parsers import categories_file_parser

logger = logging.getLogger(__name__)


def learn(input_supplier: Callable[[], tuple[str, list[int]]]):
    try:
        # get and validate the input: the path to the input file and the months range
        file_path, months_range = input_supplier()
        categories_file_parser.parse_categories_file(file_path, months_range)



    except (FileNotFoundError, ValueError) as ex:
        logger.exception("A failure happened during input file validation %s", file_path)

