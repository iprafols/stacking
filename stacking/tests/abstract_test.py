"""This file contains an abstract class to define functions common to all tests"""
from configparser import ConfigParser
import os
import re
import unittest

from astropy.io import fits
import numpy as np

from stacking.logging_utils import setup_logger, reset_logger

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
        - Check that the results folder exists and create it
        if it does not.
        - Setup logger
        """
        # setup results folder
        if not os.path.exists(f"{THIS_DIR}/results/"):
            os.makedirs(f"{THIS_DIR}/results/")

        # setup logger
        setup_logger()

    def tearDown(self):
        """ Actions done at test end
        - Reset logger
        """
        reset_logger()

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

    def compare_fits(self, orig_file, new_file):
        """Compare two fits files to check that they are equal

        Arguments
        ---------
        orig_file: str
        Control file

        new_file: str
        New file
        """
        # open fits files
        orig_hdul = fits.open(orig_file)
        new_hdul = fits.open(new_file)
        try:
            # compare them
            if not len(orig_hdul) == len(new_hdul):
                print(f"\nOriginal file: {orig_file}")
                print(f"New file: {new_file}")
                print("Different number of extensions found")
                print("orig_hdul.info():")
                orig_hdul.info()
                print("new_hdul.info():")
                new_hdul.info()
                self.assertTrue(len(orig_hdul) == len(new_hdul))

            # loop over HDUs
            for hdu_index, _ in enumerate(orig_hdul):
                if "EXTNAME" in orig_hdul[hdu_index].header:
                    hdu_name = orig_hdul[hdu_index].header["EXTNAME"]
                else:
                    hdu_name = hdu_index
                # check header
                orig_header = orig_hdul[hdu_name].header
                new_header = new_hdul[hdu_name].header
                for key in orig_header:
                    self.assertTrue(key in new_header)
                    if not key in ["CHECKSUM", "DATASUM"]:
                        if (orig_header[key] != new_header[key] and
                                (isinstance(orig_header[key], str) or not
                                     np.isclose(orig_header[key],
                                                new_header[key]))):
                            print(f"\nOriginal file: {orig_file}")
                            print(f"New file: {new_file}")
                            print(f"\n For header {orig_header['EXTNAME']}")
                            print(
                                f"Different values found for key {key}: "
                                f"orig: {orig_header[key]}, new: {new_header[key]}"
                            )
                        self.assertTrue(
                            (orig_header[key] == new_header[key]) or
                            (not isinstance(orig_header[key], str) and np.isclose(orig_header[key], new_header[key])))
                for key in new_header:
                    if key not in orig_header:
                        print(f"\nOriginal file: {orig_file}")
                        print(f"New file: {new_file}")
                        print(f"key {key} missing in orig header")
                    self.assertTrue(key in orig_header)
                # check data
                orig_data = orig_hdul[hdu_name].data
                new_data = new_hdul[hdu_name].data
                if orig_data is None:
                    self.assertTrue(new_data is None)
                elif orig_data.dtype.names is None:
                    if not np.allclose(orig_data, new_data, equal_nan=True):
                        print(f"\nOriginal file: {orig_file}")
                        print(f"New file: {new_file}")
                        print(f"Different values found for hdu {hdu_name}")
                        print(f"original new isclose original-new\n")
                        for new, orig in zip(orig_data, new_data):
                            print(f"{orig} {new} "
                                  f"{np.isclose(orig, new, equal_nan=True)} "
                                  f"{orig-new}")
                    self.assertTrue(
                        np.allclose(orig_data, new_data, equal_nan=True))
                else:
                    for col in orig_data.dtype.names:
                        if not col in new_data.dtype.names:
                            print(f"\nOriginal file: {orig_file}")
                            print(f"New file: {new_file}")
                            print(
                                f"Column {col} in HDU {orig_header['EXTNAME']} "
                                "missing in new file")
                        self.assertTrue(col in new_data.dtype.names)
                        # This is passed to np.allclose and np.isclose to properly handle IDs
                        if col in ['LOS_ID', 'TARGETID', 'THING_ID']:
                            rtol = 0
                        # This is the default numpy rtol value
                        else:
                            rtol = 1e-5

                        if (np.all(orig_data[col] != new_data[col]) and
                                not np.allclose(orig_data[col],
                                                new_data[col],
                                                equal_nan=True,
                                                rtol=rtol)):
                            print(f"\nOriginal file: {orig_file}")
                            print(f"New file: {new_file}")
                            print(f"Different values found for column {col} in "
                                  f"HDU {orig_header['EXTNAME']}")
                            print("original new isclose original-new\n")
                            for new, orig in zip(new_data[col], orig_data[col]):
                                print(
                                    f"{orig} {new} "
                                    f"{np.isclose(orig, new, equal_nan=True, rtol=rtol)} "
                                    f"{orig-new}")
                            self.assertTrue(
                                np.all(orig_data[col] == new_data[col]) or
                                (np.allclose(orig_data[col],
                                             new_data[col],
                                             equal_nan=True,
                                             rtol=rtol)))
                    for col in new_data.dtype.names:
                        if col not in orig_data.dtype.names:
                            print(f"Column {col} missing in orig header")
                        self.assertTrue(col in orig_data.dtype.names)
        finally:
            orig_hdul.close()
            new_hdul.close()

if __name__ == '__main__':
    pass
