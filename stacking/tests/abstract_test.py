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

    def check_missing_options(self,
                              options_and_values,
                              test_class,
                              error_type,
                              parent_classes=None):
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

        parent_classes: class or list of class - Default: []
        Parent(s) of the test class

        """
        if parent_classes is None:
            parent_classes = []
        elif not isinstance(parent_classes, list):
            parent_classes = [parent_classes]

        config = ConfigParser()
        config.read_dict({"test": {}})

        for option, value in options_and_values:
            # check that the error is raised
            expected_messages = [
                f"Missing argument '{option}' required by {test_class.__name__}"
            ]
            for parent_class in parent_classes:
                expected_messages.append(
                    f"Missing argument '{option}' required by {parent_class.__name__}"
                )
            with self.assertRaises(error_type) as context_manager:
                test_class(config["test"])

            self.compare_error_message(context_manager, expected_messages)

            # add the option to test the next option
            config["test"][option] = value

    def compare_error_message(self,
                              context_manager,
                              expected_messages,
                              startswith=False):
        """Check the received error message is the same as the expected

        Arguments
        ---------
        context_manager: unittest.case._AssertRaisesContext
        Context manager when errors are expected to be raised.

        expected_messages: str or list of str
        Expected error message(s)

        startswith: bool - Default: False
        If True, check that one of the expected messages is the beginning of the
        actual error message. Otherwise check that one of the expected messages
        is the entire message
        """
        if not isinstance(expected_messages, list):
            expected_messages = [expected_messages]

        # remove system dependent bits of the expected messages
        for index, expected_message in enumerate(expected_messages):
            if "stacking/tests/" in expected_message:
                expected_messages[index] = re.sub(r"\/[^ ]*\/stacking\/tests\/",
                                                  "", expected_message)

        # remove system dependent bits of the received message
        received_message = str(context_manager.exception)
        if "stacking/tests/" in received_message:
            received_message = re.sub(r"\/[^ ]*\/stacking\/tests\/", "",
                                      received_message)

        if startswith:
            if not any(
                    received_message.startswith(expected_message)
                    for expected_message in expected_messages):
                print("\nReceived incorrect error message")
                print("Expected message to start with one of:")
                for expected_message in expected_messages:
                    print(expected_message)
                print("Received:")
                print(received_message)
            self.assertTrue(
                any(
                    received_message.startswith(expected_message)
                    for expected_message in expected_messages))
        else:
            if received_message not in expected_messages:
                print("\nReceived incorrect error message")
                print("Expected one of:")
                for expected_message in expected_messages:
                    print(expected_message)
                print("Received:")
                print(received_message)
            self.assertTrue(received_message in expected_messages)


if __name__ == '__main__':
    pass
