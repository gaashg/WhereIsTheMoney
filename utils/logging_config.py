# WhereIsTheMoney — Copyright (C) 2026 GaashG
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version. See <https://www.gnu.org/licenses/>.
#
# Additional terms under Section 7(b): see the NOTICE file.

import logging
from logging.handlers import RotatingFileHandler


def setup_logger():
    handler = RotatingFileHandler("reports_parser.log", maxBytes=5_000_000, backupCount=3,
                                  encoding="utf-8")
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s:%(lineno)d: %(message)s"))
    logging.basicConfig(level=logging.INFO, handlers=[handler])
