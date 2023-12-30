"""This file contains writer tests"""
import unittest

from astropy.io import fits

from stacking.tests.abstract_test import AbstractTest
from stacking.tests.utils import stacker
from stacking.writers.writer_utils import (
    get_primary_hdu,)


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


if __name__ == '__main__':
    unittest.main()
