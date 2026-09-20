import logging
from logging.handlers import RotatingFileHandler


def setup_logger():
    handler = RotatingFileHandler("reports_parser.log", maxBytes=5_000_000, backupCount=3,
                                  encoding="utf-8")
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s:%(lineno)d: %(message)s"))
    logging.basicConfig(level=logging.INFO, handlers=[handler])
