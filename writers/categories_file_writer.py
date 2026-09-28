# WhereIsTheMoney — Copyright (C) 2026 GaashG
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version. See <https://www.gnu.org/licenses/>.
#
# Additional terms under Section 7(b): see the NOTICE file.

import json
import logging
from pathlib import Path

from utils import config

logger = logging.getLogger(__name__)


def write_categories_file(categories: dict[str, list[str]]):
    categories_folder = config.get_value("existing_categories_folder", "categories")
    categories_file_name = config.get_value("existing_categories_file_name", "categories")
    path = Path(categories_folder + categories_file_name)
    logger.info(f"Writing merged categories into file {categories_folder 
                                                       + categories_file_name}")
    with open(path, "w", encoding="utf-8") as file:
        json.dump(categories, file, indent=4, ensure_ascii=False)
