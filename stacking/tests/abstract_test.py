"""This file contains an abstract class to define functions common to all tests"""
from configparser import ConfigParser
import os
import re
import unittest

from stacking.logging_utils import setup_logger

THIS_DIR = os.path.dirname(os.path.abspath(__file__))


class AbstractTest(unittest.TestCase):
    """Abstract test class to define functions used in all tests

    Methods
    -------
    (check unittest.TestCase)

    compare_ascii
    compare_fits
    setUp
    """

    def setUp(self):
        """ Actions done at test startup
        Check that the results folder exists and create it
        if it does not.
        Also make sure that Forest and Pk1dForest class variables are reset
        """
        # setup results folder
        if not os.path.exists(f"{THIS_DIR}/results/"):
            os.makedirs(f"{THIS_DIR}/results/")

        # setup logger
        setup_logger()

    def check_missing_options(self, options_and_values, test_class, error_type):
        """Check that errors are raised when required options are missing

        Arguments
        ---------
        options_and_values: list of tuples
        The tuples on the list are pairs of (option, value). They are added to
        the initializing config file iteratively and thus should be sorted

        test_class: class
        Class to be tested

        error_type: class
        Expected error type
        """
        config = ConfigParser()
        config.read_dict({"test": {}})

        for option, value in options_and_values:
            # check that the error is raised
            expected_message = (
                f"Missing argument '{option}' required by {test_class.__name__}"
            )
            with self.assertRaises(error_type) as context_manager:
                test_class(config["test"])
            self.compare_error_message(context_manager, expected_message)

            # add the option to test the next option
            config["test"][option] = value

    def compare_error_message(self,
                              context_manager,
                              expected_message,
                              startswith=False):
        """Check the received error message is the same as the expected

        Arguments
        ---------
        context_manager: unittest.case._AssertRaisesContext
        Context manager when errors are expected to be raised.

        expected_message: str
        Expected error message

        startswith: bool - Default: False
        If True, check that expected_message is the beginning of the actual error
        message. Otherwise check that expected_message is the entire message
        """
        if "stacking/tests/" in expected_message:
            expected_message = re.sub(r"\/[^ ]*\/stacking\/tests\/", "",
                                      expected_message)
        received_message = str(context_manager.exception)
        if "stacking/tests/" in received_message:
            received_message = re.sub(r"\/[^ ]*\/stacking\/tests\/", "",
                                      received_message)

        if startswith:
            if not received_message.startswith(expected_message):
                print("\nReceived incorrect error message")
                print("Expected message to start with:")
                print(expected_message)
                print("Received:")
                print(received_message)
            self.assertTrue(received_message.startswith(expected_message))
        else:
            if not received_message == expected_message:
                print("\nReceived incorrect error message")
                print("Expected:")
                print(expected_message)
                print("Received:")
                print(received_message)
            self.assertTrue(received_message == expected_message)


if __name__ == '__main__':
    pass
