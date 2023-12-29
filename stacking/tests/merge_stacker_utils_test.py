"""This file contains stacker tests"""
import os
import unittest

from astropy.io import fits
import numpy as np

from stacking.errors import StackerError
from stacking.spectrum import Spectrum
from stacking.stackers.merge_stacker_utils import (
    load_stacks,)
from stacking.tests.abstract_test import AbstractTest

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
os.environ["THIS_DIR"] = THIS_DIR

STACK_LIST = [
    f"{THIS_DIR}/data/standard_writer.fits.gz",
    f"{THIS_DIR}/data/standard_writer.fits.gz",
]


class MergeStackerUtilsTest(AbstractTest):
    """Test the MergeStacker utils

    Methods
    -------
    (see AbstractTest in stacking/tests/abstract_test.py)
    test_assign_group_multiple_cuts
    test_assign_group_one_cut
    test_extract_split_cut_sets
    test_find_interval_index
    test_format_split_on
    test_format_splits
    test_retreive_group
    """

    def test_load_stacks(self):
        """Test function load_stacks"""
        test_file = f"{THIS_DIR}/data/standard_writer.fits.gz"
        hdu = fits.open(test_file)
        test_wavelength = hdu["STACKED_SPECTRUM"].data["WAVELENGTH"]  # pylint: disable=no-member
        test_flux = hdu["STACKED_SPECTRUM"].data["STACKED_FLUX"]  # pylint: disable=no-member
        test_weight = hdu["STACKED_SPECTRUM"].data["STACKED_WEIGHT"]  # pylint: disable=no-member
        hdu.close()

        # case 1: normal execution
        stacks = load_stacks(STACK_LIST)
        self.assertTrue(len(stacks) == 2)
        self.assertTrue(len(stacks[0]) == 2)
        self.assertTrue(len(stacks[1]) == 2)
        self.assertTrue(np.allclose(stacks[0][0], test_flux))
        self.assertTrue(np.allclose(stacks[1][0], test_flux))
        self.assertTrue(np.allclose(stacks[0][1], test_weight))
        self.assertTrue(np.allclose(stacks[1][1], test_weight))

        # case 2: missing common wavelength grid
        # make sure Spectrum.common_wavelength_grid is not set
        # (this is set in the test setUp)
        Spectrum.common_wavelength_grid = None
        # run test
        load_stacks(STACK_LIST)
        stacks = load_stacks(STACK_LIST)
        self.assertTrue(len(stacks) == 2)
        self.assertTrue(len(stacks[0]) == 2)
        self.assertTrue(len(stacks[1]) == 2)
        self.assertTrue(np.allclose(stacks[0][0], test_flux))
        self.assertTrue(np.allclose(stacks[1][0], test_flux))
        self.assertTrue(np.allclose(stacks[0][1], test_weight))
        self.assertTrue(np.allclose(stacks[1][1], test_weight))

        # case 3: common wavelength grid of different size
        # reset Spectrum.common_wavelength_grid
        Spectrum.common_wavelength_grid = test_wavelength[::2]
        # run test
        expected_message = (
            "Error loading stacked spectra. Expecting the stacks to have the "
            "same wavelengths, but found wavelength grids of different sizes "
            f"({test_wavelength[::2].size} and {test_wavelength.size})")
        with self.assertRaises(StackerError) as context_manager:
            load_stacks(STACK_LIST)
        self.compare_error_message(context_manager, expected_message)

        # case 4: different commong wavelength grid
        # reset Spectrum.common_wavelength_grid
        Spectrum.common_wavelength_grid = test_wavelength * 2
        # run test
        expected_message = (
            "Error loading stacked spectra. Expecting the stacks to have the "
            "same wavelengths, but found differnt wavelength grids:\n"
            "wave1 wave2 areclose\n")
        for item1, item2 in zip(Spectrum.common_wavelength_grid,
                                test_wavelength):
            expected_message += f"{item1} {item2} {np.isclose(item1, item2)}\n"
        with self.assertRaises(StackerError) as context_manager:
            load_stacks(STACK_LIST)
        self.compare_error_message(context_manager, expected_message)


if __name__ == '__main__':
    unittest.main()
