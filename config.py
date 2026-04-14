import logging
import sys

import colorlog

handler = colorlog.StreamHandler(stream=sys.stdout)  # stderr yerine stdout
handler.setFormatter(colorlog.ColoredFormatter(
    "%(log_color)s%(asctime)s - %(levelname)s - %(message)s",
    log_colors={
        "DEBUG": "cyan",
        "INFO": "green",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "bold_red",
    },
    reset=True,
    no_color=False,
))

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)

print(colorlog.escape_codes)