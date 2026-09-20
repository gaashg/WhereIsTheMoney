# WhereIsTheMoney — Copyright (C) 2026 GaashG
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version. See <https://www.gnu.org/licenses/>.
#
# Additional terms under Section 7(b): see the NOTICE file.

import logging

logger = logging.getLogger(__name__)


FILE_TYPES = {
    b"PK\x03\x04": [".xlsx", ".xlsm", ".ods"]
}


def parse_file(file_path : str) -> dict:
    logger.info(f"Going to open {file_path} in order to parse it")
    with open(file_path, "rb") as file:
        header = file.read(8)

