# WhereIsTheMoney — Copyright (C) 2026 GaashG
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version. See <https://www.gnu.org/licenses/>.
#
# Additional terms under Section 7(b): see the NOTICE file.

"""Exceptions raised across the project."""


class ConfigError(Exception):
    """Raised when a requested configuration value is missing."""


class FatalError(Exception):
    """Raised when the execution of the application must be stopped."""

