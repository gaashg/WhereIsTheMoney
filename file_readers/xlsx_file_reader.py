# WhereIsTheMoney — Copyright (C) 2026 GaashG
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version. See <https://www.gnu.org/licenses/>.
#
# Additional terms under Section 7(b): see the NOTICE file.
import logging
from typing import cast

import pandas as pd
from openpyxl import load_workbook
from openpyxl.utils import range_boundaries, get_column_letter

from utils import config

logger = logging.getLogger(__name__)


def read_file(file_path: str) -> list[dict] | None:
    wanted = set(config.get_value("columns_names", "categories_table_structure"))
    workbook = load_workbook(file_path, data_only=True)
    failures = {}
    # search for the appropriate table in the workbook.
    for worksheet in workbook.worksheets:
        for table in worksheet.tables.values():
            if wanted <= {c.name for c in table.tableColumns}:
                # A table ref always carries both columns and rows, unlike the
                # partial refs ("B:F") that range_boundaries also accepts.
                min_col, min_row, max_col, max_row = cast(
                    tuple[int, int, int, int], range_boundaries(table.ref))
                if None in (min_col, min_row, max_col, max_row):
                    raise ValueError(f"Unusable table range: {table.ref}")
                df = pd.read_excel(
                    file_path,
                    sheet_name=worksheet.title,
                    header=0,
                    # first row of the table is its header
                    skiprows=min_row - 1,
                    # rows above the table
                    nrows=max_row - min_row,
                    # data rows, header excluded
                    usecols=f"{get_column_letter(min_col)}:{get_column_letter(max_col)}",
                )
                return df.to_dict("records")
            else:
                failures[table.ref] = wanted - {c.name for c in table.tableColumns}

    logger.error(f"No suitable table data was found for file {file_path}. "
                 f"Inconsistencies: {failures}")
    return None
