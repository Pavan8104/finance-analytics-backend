import logging
import sys

def setup_logging():
    logger = logging.getLogger("finance_api")
    logger.setLevel(logging.INFO)

    # Console Handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)

    # Formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)

    # Add handler
    logger.addHandler(ch)

    return logger

logger = setup_logging()
