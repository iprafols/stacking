"""This file contains rebin tests"""
import logging
import os
import unittest

from stacking.logging_utils import reset_logger, setup_logger
from stacking.tests.abstract_test import AbstractTest

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
os.environ["THIS_DIR"] = THIS_DIR

LOGGING_LEVELS = [
    "NOTSET",
    0,
    "DEBUG",
    10,
    "PROGRESS",
    15,
    "INFO",
    20,
    "WARN",
    30,
    "WARN_OK",
    31,
    "ERROR",
    40,
    "CRITICAL",
    50,
]


class LoggingTest(AbstractTest):
    """Test the logging.

    Methods
    -------
    (see AbstractTest in stacking/tests/abstract_test.py)
    """

    def test_logging(self):
        """ Test the loggin utils"""
        out_dir = f"{THIS_DIR}/results/log_tests/"
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)
        test_dir = f"{THIS_DIR}/data/log_tests/"

        for level in LOGGING_LEVELS:
            if isinstance(level, str):
                out_file = f"{out_dir}log_level_{level.lower()}.txt"
                test_file = f"{test_dir}log_level_{level.lower()}.txt"
            else:
                out_file = f"{out_dir}log_level_{level}.txt"
                test_file = f"{test_dir}log_level_{level}.txt"

            # make sure logging is reset
            reset_logger()

            setup_logger(
                logging_level_console=level,
                log_file=out_file,
                logging_level_file=level,
            )

            print_log_test_messages()

            self.compare_ascii(test_file, out_file)


def print_log_test_messages():
    """Print log test messages"""
    logger = logging.getLogger("stacking")
    logger.debug("debug")
    logger.progress("progress")
    logger.info("info")
    logger.warning("warning")
    logger.ok_warning("warning ok")
    logger.error("error")
    logger.critical("critical")


if __name__ == '__main__':
    unittest.main()
