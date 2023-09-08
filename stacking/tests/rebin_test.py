"""This file contains configuration tests"""
from configparser import ConfigParser
import os
import unittest

from astropy.io import fits

from stacking.errors import RebinError
from stacking.rebin import defaults as defaults_rebin
from stacking.rebin import Rebin, VALID_STEP_TYPES
from stacking.tests.test_utils import SPECTRA
from stacking.tests.abstract_test import AbstractTest

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
os.environ["THIS_DIR"] = THIS_DIR


class RebinTest(AbstractTest):
    """Test the data rebinning.

    Methods
    -------
    (see AbstractTest in stacking/tests/abstract_test.py)
    run_rebin_without_errors
    test_rebin_lin
    test_rebin_log
    test_rebin_missing_options
    test_rebin_wrong_wavelength_cuts
    """

    def run_rebin_with_errors(self, rebin_kwargs, expected_message):
        """Check behaviour of Rebin when errors are expected

        Arguments
        ---------
        rebin_kwargs: dict
        Keyword arguments to set the configuration run

        expected_message: str
        Expected error message
        """
        config = create_rebin_config(rebin_kwargs)

        with self.assertRaises(RebinError) as context_manager:
            Rebin(config["rebin"])
        self.compare_error_message(context_manager, expected_message)

    def run_rebin_without_errors(self, rebin_kwargs, test_file, out_file):
        """Check behaviour of Rebin when no errors are expected

        Arguments
        ---------
        rebin_kwargs: dict
        Keyword arguments to set the configuration run

        test_file: str
        Name of the test file against which we compare the results

        out_file: str
        Name of the output file
        """
        config = create_rebin_config(rebin_kwargs)

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

        # compare against expectations
        self.compare_fits(test_file, out_file)

    def test_rebin_invalid_step_type(self):
        """Check the behaviour when the step type is not valid"""
        rebin_kwargs = {
            "max wavelength": 5000,
            "min wavelength": 1000,
            "step type": "invalid",
        }
        expected_message = (
            "Error loading Rebin instance. 'step type' = 'invalid' "
            " is not supported. Supported modes are " +
            " ".join(VALID_STEP_TYPES))
        self.run_rebin_with_errors(rebin_kwargs, expected_message)

    def test_rebin_invalid_wavelength_cuts(self):
        """Check the behaviour when the wavelength cuts are not correct"""

        # max wavelength < min wavelength
        rebin_kwargs = {
            "max wavelength": 1000,
            "min wavelength": 5000,
        }
        expected_message = (
            "The minimum wavelength must be smaller than the maximum wavelength"
            "Found values: min = 5000.0, max = 1000.0")
        self.run_rebin_with_errors(rebin_kwargs, expected_message)

        # problems with limiting wavelengths
        rebin_kwargs = {
            "max wavelength": 5000,
            "min wavelength": 1000,
            "step type": "log",
            "step wavelength": 0.0001,
        }
        expected_message = (
            "Inconsistent values given for 'min wavelength' (1000.0), "
            "'max wavelength' (5000.0) and "
            "'step wavelength' (0.0001). Limiting wavelengths "
            "should be separated by N times the step with N being an integer. "
            "Expected a maximum wavelength of 4999.1941102499995")
        self.run_rebin_with_errors(rebin_kwargs, expected_message)

    def test_rebin_lin(self):
        """Test the data rebinning using linear wavelength solution"""
        out_file = f"{THIS_DIR}/results/rebinned_lin.fits.gz"
        test_file = f"{THIS_DIR}/data/rebinned_lin.fits.gz"

        rebin_kwargs = {
            "max wavelength": 5000,
            "min wavelength": 1000,
            "step type": "lin",
            "step wavelength": 0.8,
        }
        self.run_rebin_without_errors(rebin_kwargs, test_file, out_file)

    def test_rebin_log(self):
        """Test the data rebinning using loglinear wavelength solution"""
        out_file = f"{THIS_DIR}/results/rebinned_log.fits.gz"
        test_file = f"{THIS_DIR}/data/rebinned_log.fits.gz"

        rebin_kwargs = {
            "max wavelength": 4999.1941102499995,
            "min wavelength": 1000,
            "step type": "log",
            "step wavelength": 1e-4,
        }
        self.run_rebin_without_errors(rebin_kwargs, test_file, out_file)

    def test_rebin_missing_options(self):
        """Check that errors are raised when required options are missing"""
        options_and_values = [
            ("max wavelength", "4999.1941102499995"),
            ("min wavelength", "1000"),
            ("step type", "log"),
            ("step wavelength", "1e-4"),
        ]

        self.check_missing_options(options_and_values, Rebin, RebinError)


def create_rebin_config(rebin_kwargs):
    """Create a configuration instance to run Rebin

    Arguments
    ---------
    rebin_kwargs: dict
    Keyword arguments to set the configuration run

    Return
    ------
    config: ConfigParser
    Run configuration
    """
    config = ConfigParser()
    config.read_dict({"rebin": rebin_kwargs})
    for key, value in defaults_rebin.items():
        if key not in config["rebin"]:
            config["rebin"][key] = str(value)

    return config


if __name__ == '__main__':
    unittest.main()
