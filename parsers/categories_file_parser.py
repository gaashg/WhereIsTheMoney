# WhereIsTheMoney — Copyright (C) 2026 GaashG
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version. See <https://www.gnu.org/licenses/>.
#
# Additional terms under Section 7(b): see the NOTICE file.

from file_readers import xlsx_file_reader
from utils import config


def parse_categories_file(file_path: str, months_range: list[int]) -> dict:
    categories = xlsx_file_reader.read_file(file_path)

    if not categories:
        return {}

    for row in categories:
        print(row)

    return {}
