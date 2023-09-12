"""This file contains normalizer tests"""
from configparser import ConfigParser
import os
import unittest

from stacking.errors import WriterError
from stacking.tests.abstract_test import AbstractTest
from stacking.tests.test_utils import stacker
from stacking.writer import Writer

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
os.environ["THIS_DIR"] = THIS_DIR


class WriterTest(AbstractTest):
    """Test the normalizers.

    Methods
    -------
    (see AbstractTest in stacking/tests/abstract_test.py)

    """

    def test_writer(self):
        """Test the abstract writer"""
        config = ConfigParser()
        config.read_dict(
            {"writer": {
                "output directory": f"{THIS_DIR}/results/"
            }})
        writer = Writer(config["writer"])

        # calling normalize_spectrum should raise an error
        expected_message = (
            "Method 'write_results' was not overloaded by child class")
        with self.assertRaises(WriterError) as context_manager:
            writer.write_results(stacker)
        self.compare_error_message(context_manager, expected_message)

    def test_writer_missing_options(self):
        """Check that errors are raised when required options are missing"""
        options_and_values = [
            ("output directory", f"{THIS_DIR}/results/"),
        ]

        self.check_missing_options(options_and_values, Writer, WriterError)


if __name__ == '__main__':
    unittest.main()
