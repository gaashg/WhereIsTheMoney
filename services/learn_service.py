
from validators import input_file_validator
import logging
from collections.abc import Callable
from input import console_input

logger = logging.getLogger(__name__)


def learn(input_supplier: Callable[[], tuple[str, list[str]]]):
    try:
        # validate the file path
        input_file_validator.validate()


    except (FileNotFoundError, ValueError) as ex:
        logger.exception("A failure happened during input file validation %s", file_path)

