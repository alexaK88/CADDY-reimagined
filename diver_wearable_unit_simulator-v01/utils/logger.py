import logging
import sys

LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"


def setup_logging(level: int = logging.INFO) -> None:
    """
    Configure application-wide logging.
    This should be called once from main.py.
    """
    logging.basicConfig(level=level, format=LOG_FORMAT,
                        handlers=[logging.StreamHandler(sys.stdout)])


def get_logger(name: str) -> logging.Logger:
    """
    Return a module-specific logger.
    """
    return logging.getLogger(name)
