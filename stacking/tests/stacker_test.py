"""This file contains configuration tests"""
from configparser import ConfigParser
from copy import copy
import os
import unittest

from stacking.errors import StackerError
from stacking.spectrum import Spectrum
from stacking.stacker import Stacker
from stacking.tests.abstract_test import AbstractTest
from stacking.tests.test_utils import NORMALIZED_SPECTRA

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
os.environ["THIS_DIR"] = THIS_DIR

STACKER_KWARGS = {
    "num processors": 1,
}


class StackerTest(AbstractTest):
    """Test the stackers.

    Methods
    -------
    (see AbstractTest in stacking/tests/abstract_test.py)
    test_stacker
    test_stacker_missing_options
    test_stacker_unset_spectrum
    """

    def test_stacker(self):
        """Test the abstract normalizer"""
        config = ConfigParser()
        config.read_dict({"stacker": STACKER_KWARGS})
        stacker = Stacker(config["stacker"])

        # calling compute_norm_factors should raise an error
        expected_message = "Method 'stack' was not overloaded by child class"
        with self.assertRaises(StackerError) as context_manager:
            stacker.stack(copy(NORMALIZED_SPECTRA))
        self.compare_error_message(context_manager, expected_message)

    def test_stacker_missing_options(self):
        """Check that errors are raised when required options are missing"""
        options_and_values = [
            ("num processors", "1"),
        ]

        self.check_missing_options(options_and_values, Stacker, StackerError)

    def test_stacker_unset_spectrum(self):
        """Test the abstract normalizer"""
        config = ConfigParser()
        config.read_dict({"stacker": STACKER_KWARGS})

        # make sure Spectrum.common_wavelength_grid is not set
        # (this is set in the test setUp)
        Spectrum.common_wavelength_grid = None

        # calling compute_norm_factors should raise an error
        expected_message = (
            "Spectrum.common_wavelength_grid must be set to initialize any "
            "Stacker instances")
        with self.assertRaises(StackerError) as context_manager:
            Stacker(config["stacker"])
        self.compare_error_message(context_manager, expected_message)


if __name__ == '__main__':
    unittest.main()
