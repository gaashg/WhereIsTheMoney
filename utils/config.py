# <שם הפרויקט> — Copyright (C) 2026 <השם שלך>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version. See <https://www.gnu.org/licenses/>.
#
# Additional terms under Section 7(b): see the NOTICE file.

"""Module docstring goes here."""

import tomllib
from pathlib import Path
import logging


logger = logging.getLogger(__name__)


def _load_toml():
    config_path = Path(__file__).resolve().parent.parent / "config.toml"

    with config_path.open("rb") as f:
        return tomllib.load(f)


_config = _load_toml()


def get_value(section: str, key: str):
    if key is None or key == "":
        logger.error("No key was sent")
        return None

    if section is None or section == "":
        logger.info("Section is None. Checking for high level key")
        if key not in _config:
            logger.error("Key %s was not found in config", key)
            return None
        else:
            return _config[key]

    value = _config.get(section, {}).get(key)
    if value is None:
        logger.error("Key %s.%s was not found in config", section, key)

    return value


