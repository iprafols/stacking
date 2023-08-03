"""This file contains configuration tests"""
from configparser import ConfigParser
import os
import unittest

from stacking.errors import ReaderError
from stacking.reader import Reader
from stacking.tests.abstract_test import AbstractTest

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
os.environ["THIS_DIR"] = THIS_DIR


class ReaderTest(AbstractTest):
    """Test the readers.

    Methods
    -------
    (see AbstractTest in stacking/tests/abstract_test.py)
    test_config
    """

    def test_reader(self):
        """Test the abstract reader"""
        config = ConfigParser()
        config.read_dict({"reader": {"input directory": f"{THIS_DIR}/data/"}})

        reader = Reader(config["reader"])

        self.assertTrue(len(reader.spectra) == 0)
        self.assertTrue(reader.catalogue is None)
        self.assertTrue(reader.input_directory == f"{THIS_DIR}/data/")

        expected_message = "Method 'read_data' was not overloaded by child class"
        with self.assertRaises(ReaderError) as context_manager:
            reader.read_data()
        self.compare_error_message(context_manager, expected_message)

    def test_reader_missing_options(self):
        """Check that errors are raised when required options are missing"""
        options_and_values = [
            ("input directory", f"{THIS_DIR}/data/"),
        ]

        self.check_missing_options(options_and_values, Reader, ReaderError)


if __name__ == '__main__':
    unittest.main()
