"""This file contains configuration tests"""
from configparser import ConfigParser
import os
import unittest

from astropy.io import fits

from stacking.errors import RebinError
from stacking.rebin import defaults as defaults_rebin
from stacking.rebin import Rebin
from stacking.tests.test_utils import SPECTRA
from stacking.tests.abstract_test import AbstractTest

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
os.environ["THIS_DIR"] = THIS_DIR


class RebinTest(AbstractTest):
    """Test the data rebinning.

    Methods
    -------
    (see AbstractTest in stacking/tests/abstract_test.py)
    run_rebin_whitout_errors
    test_rebin_lin
    test_rebin_log
    """

    def run_rebin_whitout_errors(self, config, test_file, out_file):
        """Check behaviour when no errors are expected

        Arguments
        ---------
        config: ConfigParser
        Run configuration

        test_file: str
        Name of the test file against which we compare the results

        out_file: str
        Name of the output file
        """
        for key, value in defaults_rebin.items():
            if key not in config["rebin"]:
                config["rebin"][key] = str(value)

        rebin = Rebin(config["rebin"])
        rebinned_spectra = [rebin(spectrum) for spectrum in SPECTRA]

        # save results
        hdu_list = [fits.PrimaryHDU()]
        cols = [
            fits.Column(name="wavelength_common_grid",
                        format="E",
                        array=rebin.common_wavelength_grid),
        ]
        hdu_list.append(fits.BinTableHDU.from_columns(cols, name="WAVELENGTH"))
        for spectrum in rebinned_spectra:
            cols = [
                fits.Column(name="flux_common_grid",
                            format="E",
                            array=spectrum.flux_common_grid),
                fits.Column(name="ivar_common_grid",
                            format="E",
                            array=spectrum.ivar_common_grid),
            ]
            hdu_list.append(
                fits.BinTableHDU.from_columns(cols, name=f"{spectrum.specid}"))
        hdul = fits.HDUList(hdu_list)
        hdul.writeto(out_file, overwrite=True)

        self.compare_fits(test_file, out_file)

    def test_rebin_lin(self):
        """Test the data rebinning using linear wavelength solution"""
        out_file = f"{THIS_DIR}/results/rebinned_lin.fits.gz"
        test_file = f"{THIS_DIR}/data/rebinned_lin.fits.gz"

        config = ConfigParser()
        config.read_dict({
            "rebin": {
                "max wavelength": 5000,
                "min wavelength": 1000,
                "step type": "lin",
                "step wavelength": 0.8,
            }
        })

        self.run_rebin_whitout_errors(config, test_file, out_file)

    def test_rebin_log(self):
        """Test the data rebinning using loglinear wavelength solution"""
        out_file = f"{THIS_DIR}/results/rebinned_log.fits.gz"
        test_file = f"{THIS_DIR}/data/rebinned_log.fits.gz"

        config = ConfigParser()
        config.read_dict({
            "rebin": {
                "max wavelength": 4999.1941102499995,
                "min wavelength": 1000,
                "step type": "log",
                "step wavelength": 1e-4,
            }
        })

        self.run_rebin_whitout_errors(config, test_file, out_file)

    def test_rebin_missing_options(self):
        """Check that errors are raised when required options are missing"""
        options_and_values = [
            ("convert to restframe", "False"),
            ("max wavelength", "4999.1941102499995"),
            ("min wavelength", "1000"),
            ("rebin", "True"),
            ("step type", "log"),
            ("step wavelength", "1e-4"),
        ]

        self.check_missing_options(options_and_values, Rebin, RebinError)


if __name__ == '__main__':
    unittest.main()
