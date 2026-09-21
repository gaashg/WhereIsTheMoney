# WhereIsTheMoney — Copyright (C) 2026 GaashG
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version. See <https://www.gnu.org/licenses/>.
#
# Additional terms under Section 7(b): see the NOTICE file.

from pathlib import Path
import json
from utils import config


def read_categories_file() -> dict[str, list[str]]:
    categories_folder = config.get_value("existing_categories_folder", "categories")
    categories_file_name = config.get_value("existing_categories_file_name", "categories")
    path = Path(categories_folder + categories_file_name)
    # An empty file holds no JSON at all, so it is treated like a missing one.
    if path.exists() and path.stat().st_size > 0:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)

    return {}
