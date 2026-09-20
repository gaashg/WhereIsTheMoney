from pathlib import Path

SUPPORTED_FILE_EXTENSIONS = frozenset({".xlsx", ".xls", ".csv", ".xlsm", ".xlsb", ".ods"})


def validate(file_path_str):
    if file_path_str is None or file_path_str == "":
        raise ValueError("No file path was supplied. Please supply a full path")

    file_path = Path(file_path_str)
    if not file_path.exists() or not file_path.is_file():
        raise FileNotFoundError(f"File not found in the supplied path: {file_path_str}")

    if file_path.suffix not in SUPPORTED_FILE_EXTENSIONS:
        raise ValueError("Supplied file type is not supported")
