# WhereIsTheMoney — Copyright (C) 2026 GaashG
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version. See <https://www.gnu.org/licenses/>.
#
# Additional terms under Section 7(b): see the NOTICE file.

"""Read-only access to the project's config.toml.

The file is read once, on first use, and cached. Its location defaults to
config.toml in the project root; set WITM_CONFIG_PATH to read another file.
"""

import logging
import os
import tomllib
from functools import cache
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.toml"
CONFIG_PATH_ENV_VAR = "WITM_CONFIG_PATH"


def _config_path() -> Path:
    """The configured file, overridable with the WITM_CONFIG_PATH variable."""
    override = os.environ.get(CONFIG_PATH_ENV_VAR)
    return Path(override) if override else DEFAULT_CONFIG_PATH


@cache
def _load_toml() -> dict:
    """Read the config file. The result is cached, so it is read once."""
    config_path = _config_path()
    logger.debug("Loading configuration from %s", config_path)
    with config_path.open("rb") as f:
        return tomllib.load(f)


def get_value(key: str, section: str | None = None) -> Any:
    if not key:
        raise ValueError("No key was sent")

    config = _load_toml()

    if not section:
        logger.debug("No section was supplied. Checking for top level key %s", key)
        if key not in config:
            raise KeyError(f"Key {key} was not found in config")

        return config[key]

    value = config.get(section, {}).get(key)
    if value is None:
        raise KeyError(f"Key {section}.{key} was not found in config")

    return value
