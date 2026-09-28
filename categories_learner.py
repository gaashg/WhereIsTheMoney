# WhereIsTheMoney — Copyright (C) 2026 GaashG
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version. See <https://www.gnu.org/licenses/>.
#
# Additional terms under Section 7(b): see the NOTICE file.

import utils.logging_config as logging_config
from input import console_input
from services import categories_learner, categories_analyzer


def main():
    while True:
        choice = input("What would you like to do today?\n1 - Add new categories\n2 - "
                       "Process payments\n3 - Exit")
        match choice:
            case "1":
                categories_learner.learn(console_input.supply_input)
            case "2":
                categories_analyzer.categorize_expenses(console_input.supply_input)
            case "3":
                return
            case _:
                print("Invalid option (choose between 1, 2, 3")


if __name__ == "__main__":
    logging_config.setup_logger()
    main()
