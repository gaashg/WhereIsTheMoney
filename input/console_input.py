# WhereIsTheMoney — Copyright (C) 2026 GaashG
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version. See <https://www.gnu.org/licenses/>.
#
# Additional terms under Section 7(b): see the NOTICE file.

from validators import input_file_validator


def supply_input():
    attempts = 3
    file_path = input("Hello, which file would you like me to learn today? Write a "
                      f"full path ({attempts} attempts are left")

