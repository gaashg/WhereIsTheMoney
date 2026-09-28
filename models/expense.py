# WhereIsTheMoney — Copyright (C) 2026 GaashG
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version. See <https://www.gnu.org/licenses/>.
#
# Additional terms under Section 7(b): see the NOTICE file.

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Expense:
    """A class that describes a purchase that was made"""
    purchase_date: datetime
    shop: str
    category1: str | None
    category2: str | None
    category3: str | None
    purchase_amount: float | None = None
    billing_amount: float | None = None
    extra_detail: str | None = None
