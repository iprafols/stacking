"""This file contains configuration tests"""
from configparser import ConfigParser
import os
import unittest

import numpy as np

from stacking.errors import StackerError
from stacking.stackers.mean_stacker import MeanStacker
from stacking.stackers.median_stacker import MedianStacker
from stacking.spectrum import Spectrum
from stacking.stacker import Stacker
from stacking.tests.abstract_test import AbstractTest
from stacking.tests.test_utils import COMMON_WAVELENGTH_GRID, NORMALIZED_SPECTRA

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
    run_simple_stack
    test_mean_stacker
    test_median_stacker
    test_stacker
    test_stacker_missing_options
    test_stacker_unset_spectrum
    """

    def run_simple_stack(self, stacker, test_file, out_file):
        """Compute the stack and check its output

        Arguments
        ---------
        stacker: Stacker
        The initialized stacker

        test_file: str
        Name of the test file against which we compare the results

        out_file: str
        Name of the output file
        """
        # compute stack
        stacker.stack(NORMALIZED_SPECTRA)

        # save results
        with open(out_file, "w", encoding="utf-8") as results:
            results.write("# wavelength stacked_flux total_weight\n")
            for wavelength, stacked_flux, stacked_weight in zip(
                    COMMON_WAVELENGTH_GRID, stacker.stacked_flux,
                    stacker.stacked_weight):
                results.write(f"{wavelength} {stacked_flux} {stacked_weight}\n")

        # compare with test
        self.compare_ascii_numeric(test_file, out_file)

    def test_mean_stacker(self):
        """Test the class MeanStacker"""
        out_file = f"{THIS_DIR}/results/mean_stacking.txt"
        test_file = f"{THIS_DIR}/data/mean_stacking.txt"

        config = ConfigParser()
        config.read_dict({"stacker": STACKER_KWARGS})

        stacker = MeanStacker(config["stacker"])

        self.run_simple_stack(stacker, test_file, out_file)

    def test_median_stacker(self):
        """Test the class MeanStacker"""
        out_file = f"{THIS_DIR}/results/median_stacking.txt"
        test_file = f"{THIS_DIR}/data/median_stacking.txt"

        config = ConfigParser()
        config.read_dict({"stacker": STACKER_KWARGS})

        stacker = MedianStacker(config["stacker"])

        self.run_simple_stack(stacker, test_file, out_file)

    def test_stacker(self):
        """Test the abstract normalizer"""
        config = ConfigParser()
        config.read_dict({"stacker": STACKER_KWARGS})
        stacker = Stacker(config["stacker"])

        self.assertEqual(stacker.stacked_flux.size, COMMON_WAVELENGTH_GRID.size)
        self.assertTrue(
            np.allclose(stacker.stacked_flux,
                        np.zeros_like(COMMON_WAVELENGTH_GRID)))
        self.assertEqual(stacker.stacked_weight.size,
                         COMMON_WAVELENGTH_GRID.size)
        self.assertTrue(
            np.allclose(stacker.stacked_weight,
                        np.zeros_like(COMMON_WAVELENGTH_GRID)))

        # calling compute_norm_factors should raise an error
        expected_message = "Method 'stack' was not overloaded by child class"
        with self.assertRaises(StackerError) as context_manager:
            stacker.stack(NORMALIZED_SPECTRA)
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
