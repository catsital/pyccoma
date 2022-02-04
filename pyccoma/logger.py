import sys
import logging

from logging import CRITICAL, ERROR, DEBUG, INFO, WARN, NOTSET

_levels = {
    CRITICAL: "critical",
    ERROR: "error",
    WARN: "warning",
    INFO: "info",
    DEBUG: "debug",
    NOTSET: "none",
}

levels = [name for _, name in _levels.items()]


def setup_logging():
    for level, name in _levels.items():
        logging.addLevelName(level, name)

    handlers = [logging.StreamHandler(sys.stdout)]
    logging.basicConfig(
        handlers=handlers,
        format=("{asctime:^} - {levelname: ^7} - {funcName: ^16} - {message}"),
        style="{",
        datefmt="%m/%d/%Y %H:%M:%S",
    )
