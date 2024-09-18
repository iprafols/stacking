"""This file contains writer tests"""
from copy import copy
import unittest

from astropy.io import fits
import numpy as np

from stacking.spectrum import Spectrum
from stacking.tests.abstract_test import AbstractTest
from stacking.tests.utils import stacker
from stacking.writers.writer_utils import (get_primary_hdu,
                                           get_simple_stack_hdu)


class WriterUtilsTest(AbstractTest):
    """Test the writing utils

    Methods
    -------
    (see AbstractTest in stacking/tests/abstract_test.py)
    """

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

        header_keys = [
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
        for key in hdu.header:
            self.assertTrue(key in header_keys)
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

        hdu = get_simple_stack_hdu(stacker, hdu_name="CASE2", write_errors=True)

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
            np.allclose(hdu.data["STACKED_FLUX"], stacker.stacked_flux))
        self.assertTrue(
            np.allclose(hdu.data["STACKED_WEIGHT"], stacker.stacked_weight))
        self.assertTrue(
            np.allclose(hdu.data["STACKED_ERROR"], stacker.stacked_error))
        self.assertTrue(hdu.header["EXTNAME"] == "CASE2")


if __name__ == '__main__':
    unittest.main()
