# WhereIsTheMoney — Copyright (C) 2026 GaashG
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version. See <https://www.gnu.org/licenses/>.
#
# Additional terms under Section 7(b): see the NOTICE file.

from validators import input_file_validator
import logging
from collections.abc import Callable
from input import console_input

logger = logging.getLogger(__name__)


def learn(input_supplier: Callable[[], tuple[str, list[str]]]):
    try:
        # validate the file path
        input_file_validator.validate()


    except (FileNotFoundError, ValueError) as ex:
        logger.exception("A failure happened during input file validation %s", file_path)

