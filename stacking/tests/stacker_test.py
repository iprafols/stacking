"""This file contains stacker tests"""
from configparser import ConfigParser
import os
import unittest

from astropy.io import fits
import numpy as np

from stacking.errors import StackerError
from stacking.spectrum import Spectrum
from stacking.stackers.mean_stacker import MeanStacker
from stacking.stackers.median_stacker import MedianStacker
from stacking.stackers.merge_mean_stacker import MergeMeanStacker
from stacking.stackers.merge_median_stacker import MergeMedianStacker
from stacking.stackers.merge_stacker import MergeStacker
from stacking.stackers.merge_stacker import defaults as defaults_merge_stacker
from stacking.stackers.split_mean_stacker import SplitMeanStacker
from stacking.stackers.split_median_stacker import SplitMedianStacker
from stacking.stackers.split_merge_mean_stacker import SplitMergeMeanStacker
from stacking.stackers.split_merge_median_stacker import SplitMergeMedianStacker
from stacking.stackers.split_stacker import SplitStacker, VALID_SPLIT_TYPES
from stacking.stackers.split_stacker import defaults as defaults_split_stacker
from stacking.stacker import Stacker
from stacking.tests.abstract_test import AbstractTest
from stacking.tests.utils import COMMON_WAVELENGTH_GRID, NORMALIZED_SPECTRA

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
os.environ["THIS_DIR"] = THIS_DIR

MERGE_STACKER_KWARGS = {
    "stack list": (f"{THIS_DIR}/data/standard_writer.fits.gz "
                   f"{THIS_DIR}/data/standard_writer.fits.gz")
}

MERGE_STACKER_OPTIONS_AND_VALUES = [
    ("stack list", (f"{THIS_DIR}/data/standard_writer.fits.gz "
                    f"{THIS_DIR}/data/standard_writer.fits.gz")),
]

SPLIT_STACKER_KWARGS = {
    "specid name": "THING_ID",
    "split catalogue name": f"{THIS_DIR}/data/drq_catalogue_plate3655.fits.gz",
    "split on": "Z",
    "split type": "OR",
    "split cuts": "[1.1 1.2 1.3]",
}

SPLIT_STACKER_OPTIONS_AND_VALUES = [
    ("specid name", "THING_ID"),
    ("split catalogue name",
     f"{THIS_DIR}/data/drq_catalogue_plate3655.fits.gz"),
    ("split on", "Z"),
    ("split type", "OR"),
    ("split cuts", "[1.1 1.2 1.3]"),
]


class StackerTest(AbstractTest):  # pylint: disable=too-many-public-methods
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

    def test_merge_stacker(self):
        """Check that class MergeStacker"""
        config = create_merge_stacker_config(MERGE_STACKER_KWARGS)
        stacker = MergeStacker(config["stacker"])
        expected_message = "Method 'stack' was not overloaded by child class"
        with self.assertRaises(StackerError) as context_manager:
            stacker.stack(NORMALIZED_SPECTRA)
        self.compare_error_message(context_manager, expected_message)

    def test_merge_stacker_invalid_files(self):
        """Check that errors are raised when invalid files are passed to MergeStacker"""
        # case 1: missing files
        config = ConfigParser()
        config.read_dict({
            "stacker": {
                "stack list": f"{THIS_DIR}/data/missing_file.fits.gz"
            }
        })
        expected_message = (
            f"Could not find file '{THIS_DIR}/data/missing_file.fits.gz' required by "
            "MergeStacker")
        with self.assertRaises(StackerError) as context_manager:
            MergeStacker(config["stacker"])
        self.compare_error_message(context_manager, expected_message)

        # case 1: invalid format
        config = ConfigParser()
        config.read_dict(
            {"stacker": {
                "stack list": f"{THIS_DIR}/data/mean_stacking.txt"
            }})
        expected_message = ("MergeStacker: Expected a fits file, found "
                            f"{THIS_DIR}/data/mean_stacking.txt")
        with self.assertRaises(StackerError) as context_manager:
            MergeStacker(config["stacker"])
        self.compare_error_message(context_manager, expected_message)

    def test_merge_stacker_missing_options(self):
        """Check that errors are raised when required options are missing"""
        self.check_missing_options(MERGE_STACKER_OPTIONS_AND_VALUES,
                                   MergeStacker, StackerError, Stacker)

    def test_merge_mean_stacker(self):
        """Check that class MergeStacker"""
        config = create_merge_stacker_config(MERGE_STACKER_KWARGS)
        stacker = MergeMeanStacker(config["stacker"])

        test_file = f"{THIS_DIR}/data/standard_writer.fits.gz"
        hdu = fits.open(test_file)
        test_flux = hdu["STACKED_SPECTRUM"].data["STACKED_FLUX"]  # pylint: disable=no-member
        test_weight = hdu["STACKED_SPECTRUM"].data["STACKED_WEIGHT"]  # pylint: disable=no-member
        hdu.close()
        self.assertTrue(
            np.allclose(stacker.stacked_flux, np.zeros(test_flux.size)))
        self.assertTrue(
            np.allclose(stacker.stacked_weight, np.zeros(test_flux.size)))

        # case 1: passing spectra to method 'stack'
        expected_message = (
            "MergeMeanStacker expects the argument 'spectra' to be 'None'. "
            "This means you probably called this class from "
            "'run_stacking.py' and it should be called only with "
            "'merge_stack_partial_runs.py'. Please double check your "
            "configuration or contact stacking developers if the problem "
            "persists")
        with self.assertRaises(StackerError) as context_manager:
            stacker.stack(NORMALIZED_SPECTRA)
        self.compare_error_message(context_manager, expected_message)

        # case 2: normal execution passing 'None' to method stack
        stacker.stack(None)
        self.assertTrue(np.allclose(stacker.stacked_flux, test_flux))
        self.assertTrue(np.allclose(stacker.stacked_weight, test_weight * 2))

    def test_merge_mean_stacker_missing_options(self):
        """Check that errors are raised when required options are missing"""
        self.check_missing_options(MERGE_STACKER_OPTIONS_AND_VALUES,
                                   MergeMeanStacker, StackerError, [MergeStacker, MeanStacker, Stacker])

    def test_merge_median_stacker(self):
        """Check that class MergeStacker"""
        merge_median_stacker_kwargs = MERGE_STACKER_KWARGS.copy()
        merge_median_stacker_kwargs.update({
            "weighted": False
        })
        config = create_merge_stacker_config(merge_median_stacker_kwargs)
        stacker = MergeMedianStacker(config["stacker"])

        test_file = f"{THIS_DIR}/data/standard_writer.fits.gz"
        hdu = fits.open(test_file)
        test_flux = hdu["STACKED_SPECTRUM"].data["STACKED_FLUX"]  # pylint: disable=no-member
        test_weight = hdu["STACKED_SPECTRUM"].data["STACKED_WEIGHT"]  # pylint: disable=no-member
        hdu.close()
        self.assertTrue(
            np.allclose(stacker.stacked_flux, np.zeros(test_flux.size)))
        self.assertTrue(
            np.allclose(stacker.stacked_weight, np.zeros(test_flux.size)))

        # case 1: passing spectra to method 'stack'
        expected_message = (
            "MergeMedianStacker expects the argument 'spectra' to be 'None'. "
            "This means you probably called this class from "
            "'run_stacking.py' and it should be called only with "
            "'merge_stack_partial_runs.py'. Please double check your "
            "configuration or contact stacking developers if the problem "
            "persists")
        with self.assertRaises(StackerError) as context_manager:
            stacker.stack(NORMALIZED_SPECTRA)
        self.compare_error_message(context_manager, expected_message)

        # case 2: normal execution passing 'None' to method stack
        stacker.stack(None)
        self.assertTrue(np.allclose(stacker.stacked_flux, test_flux))
        self.assertTrue(np.allclose(stacker.stacked_weight, test_weight * 2))

        # case 3:
        merge_median_stacker_kwargs = MERGE_STACKER_KWARGS.copy()
        merge_median_stacker_kwargs.update({
            "weighted": True
        })
        config = create_merge_stacker_config(merge_median_stacker_kwargs)
        stacker = MergeMedianStacker(config["stacker"])
        expected_message = "Not implemented"
        with self.assertRaises(StackerError) as context_manager:
            stacker.stack(None)
        self.compare_error_message(context_manager, expected_message)

    def test_merge_median_stacker_missing_options(self):
        """Check that errors are raised when required options are missing"""
        options_and_values = [("weighted", "False")] + MERGE_STACKER_OPTIONS_AND_VALUES.copy()
        self.check_missing_options(options_and_values,
                                   MergeMedianStacker, StackerError, [MergeStacker, MedianStacker, Stacker])

    def test_split_mean_stacker(self):
        """Check initialization of SplitMeanStacker"""
        split_stacker_kwargs = SPLIT_STACKER_KWARGS.copy()
        split_stacker_kwargs.update({
            "sigma_I": 0.05,
        })
        config = create_split_stacker_config(split_stacker_kwargs)
        stacker = SplitMeanStacker(config["stacker"])

        self.assertTrue(isinstance(stacker, SplitMeanStacker))
        self.assertTrue(isinstance(stacker, SplitStacker))
        self.assertTrue(len(stacker.stackers) == stacker.num_groups)
        for item in stacker.stackers:
            self.assertTrue(isinstance(item, MeanStacker))

    def test_split_mean_stacker_missing_options(self):
        """Check that errors are raised when required options are missing"""
        options_and_values = SPLIT_STACKER_OPTIONS_AND_VALUES.copy()
        options_and_values.append(("sigma_I", "0.05"))

        self.check_missing_options(options_and_values, SplitMeanStacker,
                                   StackerError,
                                   [SplitStacker, MeanStacker, Stacker])

    def test_split_median_stacker(self):
        """Check initialization of SplitMedianStacker"""
        split_stacker_kwargs = SPLIT_STACKER_KWARGS.copy()
        split_stacker_kwargs.update({
            "weighted": False,
        })
        config = create_split_stacker_config(split_stacker_kwargs)
        stacker = SplitMedianStacker(config["stacker"])

        self.assertTrue(isinstance(stacker, SplitMedianStacker))
        self.assertTrue(isinstance(stacker, SplitStacker))
        self.assertTrue(len(stacker.stackers) == stacker.num_groups)
        for item in stacker.stackers:
            self.assertTrue(isinstance(item, MedianStacker))

    def test_split_median_stacker_missing_options(self):
        """Check that errors are raised when required options are missing"""
        options_and_values = SPLIT_STACKER_OPTIONS_AND_VALUES.copy()
        options_and_values.append(("weighted", "False"))

        self.check_missing_options(options_and_values, SplitMedianStacker,
                                   StackerError,
                                   [SplitStacker, MedianStacker, Stacker])

    def test_split_merge_mean_stacker(self):
        """Check initialization of SplitMeanStacker"""
        split_stacker_kwargs = SPLIT_STACKER_KWARGS.copy()
        split_stacker_kwargs.update({
            "stack list": f"{THIS_DIR}/data/standard_writer.fits.gz",
        })
        config = create_split_stacker_config(split_stacker_kwargs)
        stacker = SplitMergeMeanStacker(config["stacker"])

        self.assertTrue(isinstance(stacker, SplitMergeMeanStacker))
        self.assertTrue(isinstance(stacker, SplitStacker))
        self.assertTrue(len(stacker.stackers) == stacker.num_groups)
        for item in stacker.stackers:
            self.assertTrue(isinstance(item, MergeMeanStacker))

    def test_split_merge_mean_stacker_missing_options(self):
        """Check that errors are raised when required options are missing"""
        options_and_values = SPLIT_STACKER_OPTIONS_AND_VALUES.copy()
        options_and_values.append(
            ("stack list", f"{THIS_DIR}/data/standard_writer.fits.gz"))

        self.check_missing_options(
            options_and_values, SplitMergeMeanStacker, StackerError,
            [SplitStacker, MergeMeanStacker, MergeStacker, Stacker])

    def test_split_merge_median_stacker(self):
        """Check initialization of SplitMedianStacker"""
        split_stacker_kwargs = SPLIT_STACKER_KWARGS.copy()
        split_stacker_kwargs.update({
            "stack list": f"{THIS_DIR}/data/standard_writer.fits.gz",
            "weighted": False,
        })
        config = create_split_stacker_config(split_stacker_kwargs)
        stacker = SplitMergeMedianStacker(config["stacker"])

        self.assertTrue(isinstance(stacker, SplitMergeMedianStacker))
        self.assertTrue(isinstance(stacker, SplitStacker))
        self.assertTrue(len(stacker.stackers) == stacker.num_groups)
        for item in stacker.stackers:
            self.assertTrue(isinstance(item, MergeMedianStacker))

    def test_split_merge_median_stacker_missing_options(self):
        """Check that errors are raised when required options are missing"""
        options_and_values = SPLIT_STACKER_OPTIONS_AND_VALUES.copy()
        options_and_values += [
            ("weighted", "False"),
            ("stack list", f"{THIS_DIR}/data/standard_writer.fits.gz"),
        ]

        self.check_missing_options(options_and_values, SplitMergeMedianStacker,
                                   StackerError, [
                                       SplitStacker, MedianStacker,
                                       MergeMedianStacker, MergeStacker, Stacker
                                   ])

    def test_split_stacker_assign_groups(self):
        """Check method assign_groups from SplitStacker"""

        # case: split_type == "OR"
        out_file = f"{THIS_DIR}/results/split_stacker_assign_groups_or.txt"
        test_file = f"{THIS_DIR}/data/split_stacker_assign_groups_or.txt"
        out_file_groups = f"{THIS_DIR}/results/split_stacker_assign_groups_or_groups_info.txt"
        test_file_groups = f"{THIS_DIR}/data/split_stacker_assign_groups_or_groups_info.txt"

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
        stacker.groups_info.to_csv(out_file_groups, sep=" ", index=False)
        self.compare_ascii(test_file_groups, out_file_groups)

        # case: split_type == "AND"
        out_file = f"{THIS_DIR}/results/split_stacker_assign_groups_and.txt"
        test_file = f"{THIS_DIR}/data/split_stacker_assign_groups_and.txt"
        out_file_groups = f"{THIS_DIR}/results/split_stacker_assign_groups_and_groups_info.txt"
        test_file_groups = f"{THIS_DIR}/data/split_stacker_assign_groups_and_groups_info.txt"

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
        stacker.groups_info.to_csv(out_file_groups, sep=" ", index=False)
        self.compare_ascii(test_file_groups, out_file_groups)

    def test_split_stacker_inconsistent_split_cuts_and_split_on(self):
        """Check the behaviour when 'split cuts' is not consistent with
        'split on'
        """
        split_stacker_kwargs = SPLIT_STACKER_KWARGS.copy()
        split_stacker_kwargs.update({
            "split on": "Z",
            "split cuts": "[1.0 1.5 2.0 2.5 3.0]; [0.0 0.5 1.0 1.5]",
        })
        config = create_split_stacker_config(split_stacker_kwargs)

        expected_message = (
            "Inconsistency found in reading the splits. The number of "
            "splitting variables is 1, but I found "
            "2 sets of cuts. Read vaues are\n"
            "'split on' = '['Z']'\n'split cuts' = '[1.0 1.5 2.0 2.5 3.0]; [0.0 0.5 1.0 1.5]'. "
            "Splitting variables are delimited by a semicolon (;), a comma"
            "(,) or a white space. Cuts sets should be delimited by the "
            "character ';'. Cut values within a given set should be delimited "
            "by commas and/or whitespaces)")
        with self.assertRaises(StackerError) as context_manager:
            SplitStacker(config["stacker"])
        self.compare_error_message(context_manager, expected_message)

    def test_split_stacker_invalid_split_type(self):
        """Check the behaviour when the split type is not valid"""
        split_stacker_kwargs = SPLIT_STACKER_KWARGS.copy()
        split_stacker_kwargs.update({"split type": "INVALID"})
        config = create_split_stacker_config(split_stacker_kwargs)

        expected_message = (
            "Invalid value for argument 'split on' required by SplitStacker. "
            "Expected one of '" + " ".join(VALID_SPLIT_TYPES) +
            " Found: 'INVALID'")
        with self.assertRaises(StackerError) as context_manager:
            SplitStacker(config["stacker"])
        self.compare_error_message(context_manager, expected_message)

    def test_split_stacker_missing_options(self):
        """Check that errors are raised when required options are missing"""
        self.check_missing_options(SPLIT_STACKER_OPTIONS_AND_VALUES,
                                   SplitStacker, StackerError, Stacker)

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
            "properly intialized in the child class")
        with self.assertRaises(StackerError) as context_manager:
            stacker.stack(NORMALIZED_SPECTRA)
        self.compare_error_message(context_manager, expected_message)

        # case 2: normal run intialized from a child class; split_type = "OR"
        out_file = f"{THIS_DIR}/results/split_stacking_or.txt"
        test_file = f"{THIS_DIR}/data/split_stacking_or.txt"
        split_stacker_kwargs = SPLIT_STACKER_KWARGS.copy()
        split_stacker_kwargs.update({
            "split cuts": "[1.0 1.5 2.0]",
            "sigma_I": 0.05,
        })
        config = create_split_stacker_config(split_stacker_kwargs)
        stacker = SplitMeanStacker(config["stacker"])
        stacker.stack(NORMALIZED_SPECTRA)
        self.assertTrue(len(stacker.stackers) == 2)

        # save results
        with open(out_file, "w", encoding="utf-8") as results:
            results.write(
                "# wavelength stacked_flux1 total_weight1 stacked_flux2 total_weight2\n"
            )
            for wavelength, stacked_flux1, stacked_weight1, stacked_flux2, stacked_weight2 in zip(
                    COMMON_WAVELENGTH_GRID, stacker.stackers[0].stacked_flux,
                    stacker.stackers[0].stacked_weight,
                    stacker.stackers[1].stacked_flux,
                    stacker.stackers[1].stacked_weight):
                results.write(f"{wavelength} {stacked_flux1} {stacked_weight1} "
                              f"{stacked_flux2} {stacked_weight2}\n")

        # compare with test
        self.compare_ascii_numeric(test_file, out_file)

        # case 2: normal run intialized from a child class; split_type = "AND"
        out_file = f"{THIS_DIR}/results/split_stacking_and.txt"
        test_file = f"{THIS_DIR}/data/split_stacking_and.txt"
        split_stacker_kwargs = SPLIT_STACKER_KWARGS.copy()
        split_stacker_kwargs.update({
            "split type": "AND",
            "split cuts": "[1.0 1.5 2.0]",
            "sigma_I": 0.05,
        })
        config = create_split_stacker_config(split_stacker_kwargs)
        stacker = SplitMeanStacker(config["stacker"])
        stacker.stack(NORMALIZED_SPECTRA)
        self.assertTrue(len(stacker.stackers) == 2)

        # save results
        with open(out_file, "w", encoding="utf-8") as results:
            results.write(
                "# wavelength stacked_flux1 total_weight1 stacked_flux2 total_weight2\n"
            )
            for wavelength, stacked_flux1, stacked_weight1, stacked_flux2, stacked_weight2 in zip(
                    COMMON_WAVELENGTH_GRID, stacker.stackers[0].stacked_flux,
                    stacker.stackers[0].stacked_weight,
                    stacker.stackers[1].stacked_flux,
                    stacker.stackers[1].stacked_weight):
                results.write(f"{wavelength} {stacked_flux1} {stacked_weight1} "
                              f"{stacked_flux2} {stacked_weight2}\n")

        # compare with test
        self.compare_ascii_numeric(test_file, out_file)

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


def create_merge_stacker_config(stacker_kwargs):
    """Create a configuration instance to run MergeStacker

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
    for key, value in defaults_merge_stacker.items():
        if key not in config["stacker"]:
            config["stacker"][key] = str(value)

    return config


def create_split_stacker_config(stacker_kwargs):
    """Create a configuration instance to run SplitStacker

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
