"""This file contains stacker tests"""
from configparser import ConfigParser
import os
import unittest

import numpy as np

from stacking.errors import StackerError
from stacking.spectrum import Spectrum
from stacking.stackers.mean_stacker import MeanStacker
from stacking.stackers.median_stacker import MedianStacker
from stacking.stackers.split_stacker import SplitStacker
from stacking.stackers.split_stacker_utils import (
    extract_split_cut_sets,
    format_split_on,
    format_splits,
)
from stacking.stacker import Stacker
from stacking.tests.abstract_test import AbstractTest, highlight_print
from stacking.tests.utils import COMMON_WAVELENGTH_GRID, NORMALIZED_SPECTRA

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
os.environ["THIS_DIR"] = THIS_DIR


class StackerTest(AbstractTest):
    """Test the stackers

    Methods
    -------
    (see AbstractTest in stacking/tests/abstract_test.py)
    run_simple_stack
    test_mean_stacker
    test_mean_stacker_invalid_sigma_i
    test_mean_stacker_missing_options
    test_median_stacker
    test_median_stacker_missing_options
    test_stacker
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
        config.read_dict({"stacker": {"sigma_I": 0.05,}})

        stacker = MeanStacker(config["stacker"])

        self.run_simple_stack(stacker, test_file, out_file)

    def test_mean_stacker_invalid_sigma_i(self):
        """Check the behaviour when the save format is not valid"""
        config = ConfigParser()
        config.read_dict({"stacker": {"sigma_I": -1.0,}})

        expected_message = "Argument 'sigma_I' should be positive. Found -1.0"
        with self.assertRaises(StackerError) as context_manager:
            MeanStacker(config["stacker"])
        self.compare_error_message(context_manager, expected_message)

    def test_mean_stacker_missing_options(self):
        """Check that errors are raised when required options are missing"""
        options_and_values = [
            ("sigma_I", "0.05"),
        ]

        self.check_missing_options(options_and_values, MeanStacker,
                                   StackerError, Stacker)

    def test_median_stacker(self):
        """Test the class MeanStacker"""
        out_file = f"{THIS_DIR}/results/median_stacking.txt"
        test_file = f"{THIS_DIR}/data/median_stacking.txt"

        # case 1: normal median
        config = ConfigParser()
        config.read_dict({"stacker": {"weighted": "False"}})
        stacker = MedianStacker(config["stacker"])
        self.run_simple_stack(stacker, test_file, out_file)

        # case 1: weighted median (currently not implemented)
        config = ConfigParser()
        config.read_dict({"stacker": {"weighted": "True"}})
        stacker = MedianStacker(config["stacker"])
        expected_message = "Not implemented"
        with self.assertRaises(StackerError) as context_manager:
            MedianStacker(config["stacker"])
            self.run_simple_stack(stacker, test_file, out_file)
        self.compare_error_message(context_manager, expected_message)

    def test_median_stacker_missing_options(self):
        """Check that errors are raised when required options are missing"""
        options_and_values = [
            ("weighted", "False"),
        ]

        self.check_missing_options(options_and_values, MedianStacker,
                                   StackerError, Stacker)

    def test_split_stacker_missing_options(self):
        """Check that errors are raised when required options are missing"""
        options_and_values = [
            ("specid name", "THING_ID"),
            ("split catalogue name", f"{THIS_DIR}/data/drq_catalogue_plate3655.fits.gz"),
            ("split on", "Z"),
            ("split type", "OR"),
            ("split cuts", "[1.1 1.2 1.3]"),
        ]

        self.check_missing_options(options_and_values, SplitStacker,
                                   StackerError, Stacker)

    def test_split_stacker_utils_extract_split_cut_sets(self):
        """Test function extract_split_cut_sets"""
        tests = [
            # single set
            ("1 2 3 4", ["1 2 3 4"]),
            # two sets
            ("1.1, 2.2; 3.3, 4.4", ["1.1, 2.2", "3.3, 4.4"]),
            # three sets
            ("1.1, 2.2; 3.3, 4.4; 5.5, 6", ["1.1, 2.2", "3.3, 4.4", "5.5, 6"]),
        ]

        for value, expectation in tests:
            splits_cuts_sets = extract_split_cut_sets(value)

            if splits_cuts_sets != expectation:
                highlight_print()
                print(
                    "Incorrect extraction of split cut sets. Expected "
                    f"{expectation}. Found {splits_cuts_sets}")
                self.fail("Extract split_cut_sets: incorrect formatting")

    def test_split_stacker_utils_format_split_on(self):
        """Test function format_split_on"""
        # test different cases
        tests = [
            # single split
            ("Z", ["Z"]),
            ("z", ["Z"]),
            # multiple splits using space
            ("Z BI_CIV", ["Z", "BI_CIV"]),
            ("z bi_civ", ["Z", "BI_CIV"]),
            ("Z BI_CIV RA", ["Z", "BI_CIV", "RA"]),
            # multiple splits using comma
            ("Z,BI_CIV", ["Z", "BI_CIV"]),
            ("z,bi_civ", ["Z", "BI_CIV"]),
            ("Z,BI_CIV,RA", ["Z", "BI_CIV", "RA"]),
            # multiple splits using semicolon
            ("Z;BI_CIV", ["Z", "BI_CIV"]),
            ("z;bi_civ", ["Z", "BI_CIV"]),
            ("Z;BI_CIV;RA", ["Z", "BI_CIV", "RA"]),
            # multiple splits using multiple separators
            ("Z; BI_CIV", ["Z", "BI_CIV"]),
            ("z, bi_civ", ["Z", "BI_CIV"]),
            ("Z;BI_CIV RA", ["Z", "BI_CIV", "RA"]),
        ]

        for value, expectation in tests:
            split_on = format_split_on(value)

            if split_on != expectation:
                highlight_print()
                print(
                    "Incorrect formatting of variable 'split on'. Expected "
                    f"{expectation}. Found {split_on}")
                self.fail("Format split_on: incorrect formatting")

    def test_split_stacker_utils_format_splits(self):
        """Test function format_splits"""
        # test different cases
        tests = [
            # single set
            (["1 2 3 4"], [np.array([1, 2, 3, 4], dtype=float)]),
            (["1.1 2.2 3.3 4.4"], [np.array([1.1, 2.2, 3.3, 4.4])]),
            (["1.1,2.2,3.3,4.4"], [np.array([1.1, 2.2, 3.3, 4.4])]),
            (["1.1, 2.2, 3.3, 4.4"], [np.array([1.1, 2.2, 3.3, 4.4])]),
            (["[1.1, 2.2, 3.3, 4.4]"], [np.array([1.1, 2.2, 3.3, 4.4])]),
            # two sets
            (["1.1, 2.2", "3.3, 4.4"], [np.array([1.1, 2.2]), np.array([3.3, 4.4])]),
            (["[1.1, 2.2]", "[3.3, 4.4]"], [np.array([1.1, 2.2]), np.array([3.3, 4.4])]),
            # three sets
            (["1.1, 2.2", "3.3, 4.4", "5.5, 6"], [np.array([1.1, 2.2]),
                                                  np.array([3.3, 4.4]),
                                                  np.array([5.5, 6.0])]),
            (["[1.1, 2.2]", "[3.3, 4.4]", "[5.5, 6]"], [np.array([1.1, 2.2]),
                                                        np.array([3.3, 4.4]),
                                                        np.array([5.5, 6.0])]),
        ]

        for value, expectations in tests:
            splits = format_splits(value)

            if len(splits) != len(expectations):
                highlight_print()
                print(
                    "Incorrect formatting of 'splits'. Expected "
                    f"a list of {len(expectations)} items. Found "
                    f"{len(splits)} items instead.\nInput string: {value}\n"
                    f"Expected output: {expectations}")
                self.fail("Format splits: incorrect number of items")

            for split, expectation in zip(splits, expectations):
                if not isinstance(split, np.ndarray):
                    highlight_print()
                    print("Incorrect formatting of 'splits'. List items are "
                         f"expected to be arrays. Found:{split}\nInput string: "
                         f"{value}\n")
                    self.fail("Format splits: item not an array")
                if not np.allclose(split, expectation):
                    highlight_print()
                    print(
                        "Incorrect loading of 'splits'. Format is fine but cuts"
                        f"do not meet expectations. Found {split}. Expected "
                        f"{expectation}")
                    self.fail("Format splits: incorrect cuts")

    def test_stacker(self):
        """Test the abstract normalizer"""
        config = ConfigParser()
        config.read_dict({"stacker": {}})
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

    def test_stacker_unset_spectrum(self):
        """Test the abstract normalizer"""
        config = ConfigParser()
        config.read_dict({"stacker": {}})

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
