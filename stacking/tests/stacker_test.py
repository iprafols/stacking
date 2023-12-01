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
from stacking.stackers.split_stacker import defaults as defaults_split_stacker
from stacking.stacker import Stacker
from stacking.tests.abstract_test import AbstractTest, highlight_print
from stacking.tests.utils import COMMON_WAVELENGTH_GRID, NORMALIZED_SPECTRA

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
os.environ["THIS_DIR"] = THIS_DIR


SPLIT_STACKER_KWARGS = {
    "specid name": "THING_ID",
    "split catalogue name": f"{THIS_DIR}/data/drq_catalogue_plate3655.fits.gz",
    "split on": "Z",
    "split type": "OR",
    "split cuts": "[1.1 1.2 1.3]",
}

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
    test_split_stacker_missing_options
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

    def test_split_stacker_assign_groups(self):
        """Check method assign_groups from SplitStacker"""

        # case: split_type == "OR"
        out_file = f"{THIS_DIR}/results/split_stacker_assign_groups_or.txt"
        test_file = f"{THIS_DIR}/data/split_stacker_assign_groups_or.txt"

        split_stacker_kwargs = SPLIT_STACKER_KWARGS.copy()
        split_stacker_kwargs.update({
            "split type": "OR",
            "split on": "Z BI_CIV",
            "split cuts": "[1.0 1.5 2.0 2.5 3.0]; [0.0 0.5 1.0 1.5]",
        })
        config = create_split_stacker_config(split_stacker_kwargs)
        stacker = SplitStacker(config["stacker"])

        # __init__ calls the method assign_groups
        # case "OR" should have one group column per variable
        # expecting 5 columns: Z, BI_CIV, specid, GROUP_0 and GROUP_1
        # the first three columns are added as __init__ also calls read_catalogue
        self.assertTrue(stacker.split_catalogue.columns.size == 5)
        self.assertTrue(stacker.split_catalogue.columns[0] == "Z")
        self.assertTrue(stacker.split_catalogue.columns[1] == "BI_CIV")
        self.assertTrue(stacker.split_catalogue.columns[2] == "specid")
        self.assertTrue(stacker.split_catalogue.columns[3] == "GROUP_0")
        self.assertTrue(stacker.split_catalogue.columns[4] == "GROUP_1")
        self.assertTrue(stacker.split_catalogue.shape[0] == 79)

        # save output and check against expectations
        stacker.split_catalogue.to_csv(out_file, sep=" ", index=False)
        self.compare_ascii_numeric(test_file, out_file)


        # case: split_type == "AND"
        out_file = f"{THIS_DIR}/results/split_stacker_assign_groups_and.txt"
        test_file = f"{THIS_DIR}/data/split_stacker_assign_groups_and.txt"

        split_stacker_kwargs = SPLIT_STACKER_KWARGS.copy()
        split_stacker_kwargs.update({
            "split type": "AND",
            "split on": "Z BI_CIV",
            "split cuts": "[1.0 1.5 2.0 2.5 3.0]; [0.0 0.5 1.0 1.5]",
        })
        config = create_split_stacker_config(split_stacker_kwargs)
        stacker = SplitStacker(config["stacker"])

        # __init__ calls the method assign_groups
        # case "OR" should have one group column per variable
        # expecting 5 columns: Z, BI_CIV, specid, GROUP
        # the first three columns are added as __init__ also calls read_catalogue
        self.assertTrue(stacker.split_catalogue.columns.size == 4)
        self.assertTrue(stacker.split_catalogue.columns[0] == "Z")
        self.assertTrue(stacker.split_catalogue.columns[1] == "BI_CIV")
        self.assertTrue(stacker.split_catalogue.columns[2] == "specid")
        self.assertTrue(stacker.split_catalogue.columns[3] == "GROUP")
        self.assertTrue(stacker.split_catalogue.shape[0] == 79)

        # save output and check against expectations
        stacker.split_catalogue.to_csv(out_file, sep=" ", index=False)
        self.compare_ascii_numeric(test_file, out_file)


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

    def test_split_stacker_read_catalogue(self):
        """Check method read_catalogue from SplitStacker"""
        # case 1: normal execution
        config = create_split_stacker_config(SPLIT_STACKER_KWARGS)
        stacker = SplitStacker(config["stacker"])

        # __init__ calls the method read_catalogue
        self.assertTrue(stacker.split_catalogue.columns.size == 3)
        self.assertTrue(stacker.split_catalogue.columns[0] == "Z")
        self.assertTrue(stacker.split_catalogue.columns[1] == "specid")
        # this third column is added as __init__ also calls method assing_groups
        self.assertTrue(stacker.split_catalogue.columns[2] == "GROUP_0")
        self.assertTrue(stacker.split_catalogue.shape[0] == 79)

        # case 2: missing file
        # calling read_catalogue should raise an error
        config["stacker"]["split catalogue name"] = "missing.fits"
        expected_message = "SplitStacker: Could not find catalogue: missing.fits"
        with self.assertRaises(StackerError) as context_manager:
            SplitStacker(config["stacker"])
        self.compare_error_message(context_manager, expected_message)

    def test_split_stacker_stack(self):
        """Check method stack from SplitStacker"""
        # case 1: initializing SplitStacker
        # this should raise an error as this is an abstract class
        config = create_split_stacker_config(SPLIT_STACKER_KWARGS)
        stacker = SplitStacker(config["stacker"])
        expected_message = (
            "I expected 2 stackers but found 0. Make sure the member 'stackers' is "
            "properly intialized in the child class"
        )
        with self.assertRaises(StackerError) as context_manager:
            stacker.stack(NORMALIZED_SPECTRA)
        self.compare_error_message(context_manager, expected_message)

        # case 2: normal run intialized from a child class
        # TODO: add test

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

def create_split_stacker_config(stacker_kwargs):
    """Create a configuration instance to run Dr16Reader

    Arguments
    ---------
    reader_kwargs: dict
    Keyword arguments to set the configuration run

    Return
    ------
    config: ConfigParser
    Run configuration
    """
    config = ConfigParser()
    config.read_dict({"stacker": stacker_kwargs})
    for key, value in defaults_split_stacker.items():
        if key not in config["stacker"]:
            config["stacker"][key] = str(value)

    return config

if __name__ == '__main__':
    unittest.main()
