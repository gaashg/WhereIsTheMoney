import logging

logger = logging.getLogger(__name__)


FILE_TYPES = {
    b"PK\x03\x04": [".xlsx", ".xlsm", ".ods"]
}


def parse_file(file_path : str) -> dict:
    logger.info(f"Going to open {file_path} in order to parse it")
    with open(file_path, "rb") as file:
        header = file.read(8)

