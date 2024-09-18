"""This file contains writer tests"""
from copy import copy
import unittest

from astropy.io import fits
import numpy as np

from stacking.spectrum import Spectrum
from stacking.tests.abstract_test import AbstractTest
from stacking.tests.utils import split_stacker_or, stacker
from stacking.writers.writer_utils import (get_groups_info_hdu,
                                           get_metadata_hdu, get_primary_hdu,
                                           get_simple_stack_hdu,
                                           get_split_stack_hdu)

HEADER_KEYS = [
    "XTENSION",
    "BITPIX",
    "NAXIS",
    "NAXIS1",
    "NAXIS2",
    "PCOUNT",
    "GCOUNT",
    "TFIELDS",
    "TTYPE1",
    "TFORM1",
    "TDISP1",
    "TTYPE2",
    "TFORM2",
    "TDISP2",
    "TTYPE3",
    "TFORM3",
    "TDISP3",
    "EXTNAME",
]

HEADER_KEYS_METADATA = HEADER_KEYS.copy() + [
    "TTYPE4",
    "TFORM4",
    "TDISP4",
]

HEADER_KEYS_GROUP = HEADER_KEYS_METADATA.copy() + [
    "TTYPE5",
    "TFORM5",
    "TDISP5",
    "NGROUPS",
]


class WriterUtilsTest(AbstractTest):
    """Test the writing utils

    Methods
    -------
    (see AbstractTest in stacking/tests/abstract_test.py)
    """

    def test_get_group_info_hdu(self):
        """Test function get_grouo_info_hdu"""
        hdu = get_groups_info_hdu(split_stacker_or)

        for key in hdu.header:
            self.assertTrue(key in HEADER_KEYS_GROUP)
        self.assertTrue(hdu.data.shape == (2,))
        self.assertTrue(all(hdu.data["VARIABLE"] == ["Z"] * 2))
        self.assertTrue(np.allclose(hdu.data["MIN_VALUE"], [1.0, 1.5]))
        self.assertTrue(np.allclose(hdu.data["MAX_VALUE"], [1.5, 2.0]))
        self.assertTrue(all(hdu.data["COLNAME"] == ["GROUP_0"] * 2))
        self.assertTrue(np.allclose(hdu.data["GROUP_NUM"], [0, 1]))
        self.assertTrue(hdu.header["EXTNAME"] == "GROUPS_INFO")

    def test_get_metadata_hdu(self):
        """Test function get_metadata_hdu"""
        hdu = get_metadata_hdu(split_stacker_or)

        for key in hdu.header:
            self.assertTrue(key in HEADER_KEYS_METADATA)
        self.assertTrue(hdu.data.shape == (79,))
        print(hdu.header)
        print(split_stacker_or.split_catalogue.columns)
        print(hdu.data["Z"])
        print(split_stacker_or.split_catalogue["Z"])
        self.assertTrue(
            np.allclose(hdu.data["Z"], split_stacker_or.split_catalogue["Z"]))
        self.assertTrue(
            np.allclose(hdu.data["SPECID"],
                        split_stacker_or.split_catalogue["SPECID"]))
        self.assertTrue(
            np.allclose(hdu.data["IN_STACK"],
                        split_stacker_or.split_catalogue["IN_STACK"]))
        self.assertTrue(
            np.allclose(hdu.data["GROUP_0"],
                        split_stacker_or.split_catalogue["GROUP_0"]))
        self.assertTrue(hdu.header["EXTNAME"] == "METADATA_SPECTRA")

    def test_get_primary_hdu(self):
        """Test function get_primary_hdu"""
        primary_hdu = get_primary_hdu(stacker)

        self.assertTrue(isinstance(primary_hdu, fits.hdu.image.PrimaryHDU))
        self.assertEqual(primary_hdu.header["COMMENT"], (
            f"Stacked spectrum computed using class {stacker.__class__.__name__}"
            f" of code stacking"))

    def test_get_simple_stack_hdu(self):
        """Test function get_simple_stack_hdu"""
        # case 1: no writing errors
        hdu = get_simple_stack_hdu(stacker, hdu_name="CASE1")

        for key in hdu.header:
            self.assertTrue(key in HEADER_KEYS)
        self.assertTrue(hdu.data.shape == (6989,))
        self.assertTrue(
            np.allclose(hdu.data["WAVELENGTH"],
                        Spectrum.common_wavelength_grid))
        self.assertTrue(
            np.allclose(hdu.data["STACKED_FLUX"], stacker.stacked_flux))
        self.assertTrue(
            np.allclose(hdu.data["STACKED_WEIGHT"], stacker.stacked_weight))
        self.assertTrue(hdu.header["EXTNAME"] == "CASE1")

        # case 2: writing errors
        stacker_copy = copy(stacker)
        stacker_copy.stacked_error = np.ones_like(
            stacker_copy.stacked_flux) + 0.5

        hdu = get_simple_stack_hdu(stacker_copy,
                                   hdu_name="CASE2",
                                   write_errors=True)

        header_keys = HEADER_KEYS.copy() + [
            "TTYPE4",
            "TFORM4",
            "TDISP4",
        ]
        for key in hdu.header:
            self.assertTrue(key in header_keys)
        self.assertTrue(hdu.data.shape == (6989,))
        self.assertTrue(
            np.allclose(hdu.data["WAVELENGTH"],
                        Spectrum.common_wavelength_grid))
        self.assertTrue(
            np.allclose(hdu.data["STACKED_FLUX"], stacker_copy.stacked_flux))
        self.assertTrue(
            np.allclose(hdu.data["STACKED_WEIGHT"],
                        stacker_copy.stacked_weight))
        self.assertTrue(
            np.allclose(hdu.data["STACKED_ERROR"], stacker_copy.stacked_error))
        self.assertTrue(hdu.header["EXTNAME"] == "CASE2")

    def test_get_split_stack_hdu(self):
        """Test function get_simple_stack_hdu"""
        # case 1: no writing errors
        hdu = get_split_stack_hdu(split_stacker_or, hdu_name="CASE1")

        header_keys = HEADER_KEYS.copy() + [
            "COMMENT",
        ]

        for key in hdu.header:
            self.assertTrue(key in header_keys)
        self.assertTrue(hdu.data.shape == (6989,))
        self.assertTrue(
            np.allclose(hdu.data["WAVELENGTH"],
                        Spectrum.common_wavelength_grid))
        self.assertTrue(
            np.allclose(hdu.data["STACKED_FLUX"],
                        split_stacker_or.stacked_flux))
        self.assertTrue(
            np.allclose(hdu.data["STACKED_WEIGHT"],
                        split_stacker_or.stacked_weight))
        self.assertTrue(hdu.header["EXTNAME"] == "CASE1")

        # case 2: writing errors
        split_stacker_or_copy = copy(split_stacker_or)
        split_stacker_or_copy.stacked_error = np.ones_like(
            split_stacker_or_copy.stacked_flux) + 0.5

        hdu = get_split_stack_hdu(split_stacker_or_copy,
                                  hdu_name="CASE2",
                                  write_errors=True)

        header_keys += [
            "TTYPE4",
            "TFORM4",
            "TDISP4",
        ]
        for key in hdu.header:
            self.assertTrue(key in header_keys)
        self.assertTrue(hdu.data.shape == (6989,))
        self.assertTrue(
            np.allclose(hdu.data["WAVELENGTH"],
                        Spectrum.common_wavelength_grid))
        self.assertTrue(
            np.allclose(hdu.data["STACKED_FLUX"],
                        split_stacker_or_copy.stacked_flux))
        self.assertTrue(
            np.allclose(hdu.data["STACKED_WEIGHT"],
                        split_stacker_or_copy.stacked_weight))
        self.assertTrue(
            np.allclose(hdu.data["STACKED_ERROR"],
                        split_stacker_or_copy.stacked_error))
        self.assertTrue(hdu.header["EXTNAME"] == "CASE2")


if __name__ == '__main__':
    unittest.main()
