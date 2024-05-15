"""This file contains rebin tests"""
from configparser import ConfigParser
import os
import unittest

from astropy.io import fits
import numpy as np

from stacking.errors import RebinError
from stacking.rebin import defaults as defaults_rebin
from stacking.rebin import Rebin, VALID_STEP_TYPES
from stacking.rebin import find_bins_lin as function_find_bins_lin
from stacking.rebin import find_bins_log as function_find_bins_log
from stacking.rebin import rebin as function_rebin
from stacking.tests.utils import SPECTRA
from stacking.tests.abstract_test import AbstractTest

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
os.environ["THIS_DIR"] = THIS_DIR


class RebinTest(AbstractTest):
    """Test the data rebinning.

    Methods
    -------
    (see AbstractTest in stacking/tests/abstract_test.py)
    run_rebin_with_errors
    run_rebin_without_errors
    test_rebin_invalid_step_type
    test_rebin_invalid_wavelength_cuts
    test_rebin_lin
    test_rebin_log
    test_rebin_missing_options
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

    def test_function_find_bins_lin(self):
        """Test function find_bins"""
        wavelength = np.arange(50)
        common_wavelength_grid = np.arange(0, 50, 2.5)
        expected_bins = np.array([
            0, 0, 1, 1, 2, 2, 2, 3, 3, 4, 4, 4, 5, 5, 6, 6, 6, 7, 7, 8, 8, 8, 9,
            9, 10, 10, 10, 11, 11, 12, 12, 12, 13, 13, 14, 14, 14, 15, 15, 16,
            16, 16, 17, 17, 18, 18, 18, 19, 19, 20
        ])

        # test function
        bins_jit = function_find_bins_lin(wavelength, common_wavelength_grid)
        self.assertTrue(np.allclose(bins_jit, expected_bins))

        bins_python = function_find_bins_lin.py_func(wavelength,
                                                     common_wavelength_grid)
        self.assertTrue(np.allclose(bins_jit, bins_python))

    def test_function_find_bins_log(self):
        """Test function find_bins"""
        log_wavelength = np.array([
            3.5562825, 3.5563225, 3.5565825, 3.5566225, 3.5568825, 3.5569225,
            3.5571825, 3.5572225, 3.5574825, 3.5575225
        ])
        common_log_wavelength_grid = np.array([
            3.5562, 3.5564, 3.5566, 3.5568, 3.5570, 3.5572, 3.5574, 3.5576
        ])
        expected_bins = np.array([
            0, 1, 2, 2, 3, 4, 5, 5, 6, 7
        ])

        wavelength = 10**log_wavelength
        common_wavelength_grid = 10**common_log_wavelength_grid

        # test function
        bins_jit = function_find_bins_log(wavelength, common_wavelength_grid)
        for i1, i2 in zip(bins_jit, expected_bins):
            print(i1, i2, np.isclose(i1, i2))
        self.assertTrue(np.allclose(bins_jit, expected_bins))

        bins_python = function_find_bins_log.py_func(wavelength,
                                                     common_wavelength_grid)
        self.assertTrue(np.allclose(bins_jit, bins_python))

    def test_function_rebin(self):
        """Test function rebin"""
        wavelength = np.linspace(1000, 5000, 100)
        flux = np.arange(wavelength.size)
        ivar = np.arange(wavelength.size) * 0.01
        common_wavelength_grid = np.linspace(1000, 5000, 10)
        expected_rebin_flux = np.array([
            0., 11.90909091, 22.45454545, 33.3030303, 44.22727273, 55.18181818,
            66.15151515, 77.12987013, 88.11363636, 96.53022453
        ])
        expected_rebin_ivar = np.array(
            [0., 1.21, 2.42, 3.63, 4.84, 6.05, 7.26, 8.47, 9.68, 5.79])

        # test function
        rebinned_flux_jit, rebinned_ivar_jit = function_rebin(
            flux, ivar, wavelength, common_wavelength_grid,
            function_find_bins_lin)
        self.assertTrue(np.allclose(rebinned_flux_jit, expected_rebin_flux))
        self.assertTrue(np.allclose(rebinned_ivar_jit, expected_rebin_ivar))

        rebinned_flux_python, rebinned_ivar_python = function_rebin.py_func(
            flux, ivar, wavelength, common_wavelength_grid, function_find_bins_lin)
        self.assertTrue(np.allclose(rebinned_flux_jit, rebinned_flux_python))
        self.assertTrue(np.allclose(rebinned_ivar_jit, rebinned_ivar_python))

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
            "'step wavelength' (0.0001) and 'step type' (log). Limiting wavelengths "
            "should be separated by N times the step with N being an integer. "
            "Expected a maximum wavelength of 5000.345349769783")
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
