"""This file contains stacker tests"""
import os
import unittest

from astropy.io import fits
import numpy as np

from stacking.errors import StackerError
from stacking.spectrum import Spectrum
from stacking.stackers.merge_stacker_utils import (
    load_splits_info,
    load_stacks,
)
from stacking.tests.abstract_test import AbstractTest

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
os.environ["THIS_DIR"] = THIS_DIR

STACK_LIST = [f"{THIS_DIR}/data/standard_writer.fits.gz"] * 2


class MergeStackerUtilsTest(AbstractTest):
    """Test the MergeStacker utils

    Methods
    -------
    (see AbstractTest in stacking/tests/abstract_test.py)
    test_load_splits_info
    test_load_stacks
    """

    def test_load_splits_info(self):
        """Test function load_splits_info"""
        test_file = f"{THIS_DIR}/data/split_writer.fits.gz"
        hdu = fits.open(test_file)
        test_z = list(hdu["METADATA_SPECTRA"].data["Z"]) * 2  # pylint: disable=no-member
        test_specid = list(hdu["METADATA_SPECTRA"].data["SPECID"]) * 2  # pylint: disable=no-member
        test_group0 = list(hdu["METADATA_SPECTRA"].data["GROUP_0"]) * 2  # pylint: disable=no-member

        hdu.close()

        # case 1: normal execution
        groups_info, num_groups, split_catalogue = load_splits_info(
            [f"{THIS_DIR}/data/split_writer.fits.gz"] * 2)
        self.assertEqual(groups_info.shape[0], 2)
        self.assertEqual(groups_info.shape[1], 5)
        self.assertTrue("VARIABLE" in groups_info.columns)
        self.assertTrue("MIN_VALUE" in groups_info.columns)
        self.assertTrue("MAX_VALUE" in groups_info.columns)
        self.assertTrue("COLNAME" in groups_info.columns)
        self.assertTrue("GROUP_NUM" in groups_info.columns)
        self.assertTrue(all(groups_info["VARIABLE"] == b"Z"))
        self.assertTrue(np.allclose(groups_info["MIN_VALUE"], [1.0, 1.5]))
        self.assertTrue(np.allclose(groups_info["MAX_VALUE"], [1.5, 2.0]))
        self.assertTrue(all(groups_info["COLNAME"] == b"GROUP_0"))
        self.assertTrue(np.allclose(groups_info["GROUP_NUM"], [0, 1]))
        self.assertEqual(num_groups, 2)
        self.assertEqual(split_catalogue.shape[0], 79 * 2)
        self.assertEqual(split_catalogue.shape[1], 3)
        self.assertTrue("Z" in split_catalogue.columns)
        self.assertTrue("SPECID" in split_catalogue.columns)
        self.assertTrue("GROUP_0" in split_catalogue.columns)
        self.assertTrue(np.allclose(split_catalogue["Z"], test_z))
        self.assertTrue(np.allclose(split_catalogue["SPECID"], test_specid))
        self.assertTrue(np.allclose(split_catalogue["GROUP_0"], test_group0))

        # case 2: wrong num_groups
        expected_message = (
            "Error loading splits info. I expected all the files to have "
            "the same number of groups but found different values: 2 and 3")
        with self.assertRaises(StackerError) as context_manager:
            load_splits_info([
                f"{THIS_DIR}/data/split_writer.fits.gz",
                f"{THIS_DIR}/data/split_writer_wrong_num_groups.fits.gz",
            ])
        self.compare_error_message(context_manager, expected_message)

        # case 3: wrong groups_info
        expected_message = (
            "Error loading splits info. I expected all the files to have "
            "the same splits, but found different configurations. \n"
            "Info 1:\n  VARIABLE  MIN_VALUE  MAX_VALUE     COLNAME  GROUP_NUM\n"
            "0     b'Z'        1.0        1.5  b'GROUP_0'          0\n1     b'Z'"
            "        1.5        2.0  b'GROUP_0'          1\nInfo 2:\n"
            "  VARIABLE  MIN_VALUE  MAX_VALUE     COLNAME  GROUP_NUM\n0     b'Z'"
            "        1.0        1.5  b'GROUP_0'          1\n1     b'Z'        "
            "1.5        2.0  b'GROUP_0'          1")
        with self.assertRaises(StackerError) as context_manager:
            load_splits_info([
                f"{THIS_DIR}/data/split_writer.fits.gz",
                f"{THIS_DIR}/data/split_writer_wrong_groups_info.fits.gz",
            ])
        self.compare_error_message(context_manager, expected_message)

    def test_load_stacks(self):
        """Test function load_stacks"""
        test_file = f"{THIS_DIR}/data/standard_writer.fits.gz"
        hdu = fits.open(test_file)
        test_wavelength = hdu["STACK"].data["WAVELENGTH"]  # pylint: disable=no-member
        test_flux = hdu["STACK"].data["STACKED_FLUX"]  # pylint: disable=no-member
        test_weight = hdu["STACK"].data["STACKED_WEIGHT"]  # pylint: disable=no-member
        hdu.close()

        # case 1: normal execution
        stacks = load_stacks(STACK_LIST)
        self.assertEqual(len(stacks), 2)
        self.assertEqual(len(stacks[0]), 2)
        self.assertEqual(len(stacks[1]), 2)
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
