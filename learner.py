# WhereIsTheMoney — Copyright (C) 2026 GaashG
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version. See <https://www.gnu.org/licenses/>.
#
# Additional terms under Section 7(b): see the NOTICE file.

import utils.logging_config as logging_config
from services import learn_service


def main():
    learn_service.learn()



if __name__ == "__main__":
    logging_config.setup_logger()
    main()
