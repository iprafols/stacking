"""This file contains normalizer tests"""
from configparser import ConfigParser
from copy import copy
import os
import unittest

import numpy as np
import pandas as pd

from stacking.errors import NormalizerError
from stacking.normalizer import Normalizer
from stacking.normalizers.multiple_regions_normalization import (
    defaults as defaults_multiple_regions_normalization)
from stacking.normalizers.multiple_regions_normalization import (
    MultipleRegionsNormalization, ACCEPTED_SAVE_FORMATS)
from stacking.normalizers.no_normalization import NoNormalization
from stacking.spectrum import Spectrum
from stacking.tests.abstract_test import AbstractTest
from stacking.tests.test_utils import REBINNED_SPECTRA, NORM_FACTORS, CORRECTION_FACTORS

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
os.environ["THIS_DIR"] = THIS_DIR

MULTIPLE_REGIONS_NORMALIZATION_KWARGS = {
    "log directory": f"{THIS_DIR}/results/",
    "num processors": 1,
    "intervals": "4400 - 4600, 4600 - 4800",
    "main interval": 1,
}


class NormalizerTest(AbstractTest):
    """Test the normalizers.

    Methods
    -------
    (see AbstractTest in stacking/tests/abstract_test.py)

    """

    def run_multiple_regions_normalization_with_errors(self, normalizer_kwargs,
                                                       expected_message):
        """Check behaviour of MultipleRegionsNormalization when errors are
        expected

        Arguments
        ---------
        normalizer_kwargs: dict
        Keyword arguments to set the configuration run

        expected_message: str
        Expected error message
        """
        config = create_multiple_regions_normalization_config(normalizer_kwargs)

        with self.assertRaises(NormalizerError) as context_manager:
            MultipleRegionsNormalization(config["normalizer"])
        self.compare_error_message(context_manager, expected_message)

    def test_multiple_regions_normalization(self):
        """Test the class MultipleRegionsNormalization"""
        test_dir = f"{THIS_DIR}/data/multiple_regions_normalization/"

        for num_processors in [0, 1, 2]:
            out_dir = f"{THIS_DIR}/results/multiple_regions_normalization/"
            if not os.path.exists(out_dir):
                os.makedirs(out_dir)
            spectra = [copy(spectrum) for spectrum in REBINNED_SPECTRA]

            normalizer_kwargs = MULTIPLE_REGIONS_NORMALIZATION_KWARGS.copy()
            normalizer_kwargs.update({
                "log directory": out_dir,
                "num processors": f"{num_processors}"
            })
            config = create_multiple_regions_normalization_config(
                normalizer_kwargs)

            normalizer = MultipleRegionsNormalization(config["normalizer"])
            normalizer.compute_norm_factors(spectra)
            normalizer.save_norm_factors()
            spectra = [
                normalizer.normalize_spectrum(spectrum) for spectrum in spectra
            ]

            # save results
            with open(f"{out_dir}normalized_fluxes.txt", "w",
                      encoding="utf-8") as results:
                results.write("# ")
                for spectrum in spectra:
                    results.write(f"normalized_flux_{spectrum.specid} ")
                results.write("\n")

                for index in range(spectra[0].normalized_flux.size):
                    for spectrum in spectra:
                        results.write(f"{spectrum.normalized_flux[index]} ")
                    results.write("\n")

            # compare against expectations
            self.assertTrue(normalizer.save_format == "fits.gz")
            self.compare_fits(f"{test_dir}normalization_factors.fits.gz",
                              f"{out_dir}normalization_factors.fits.gz")
            self.compare_ascii_numeric(f"{test_dir}normalized_fluxes.txt",
                                       f"{out_dir}normalized_fluxes.txt")

    def test_multiple_regions_normalization_compute_correction_factors(self):
        """Test method compute_correction_factors from MultipleRegionsNormalization"""
        out_file = f"{THIS_DIR}/results/correction_factors.txt"
        test_file = f"{THIS_DIR}/data/correction_factors.txt"

        config = create_multiple_regions_normalization_config(
            MULTIPLE_REGIONS_NORMALIZATION_KWARGS)

        normalizer = MultipleRegionsNormalization(config["normalizer"])
        normalizer.norm_factors = NORM_FACTORS

        normalizer.compute_correction_factors()

        # save results
        with open(out_file, "w", encoding="utf-8") as results:
            results.write("# interval correction_factor\n")
            for index, correction_factor in enumerate(
                    normalizer.correction_factors):
                results.write(f"{index} {correction_factor}\n")

        # compare against expectations
        self.compare_ascii_numeric(test_file, out_file)

    def test_multiple_regions_normalization_compute_correction_factors_errors(
            self):
        """Check that an error is raised in compute_correction_factors
        from MultipleRegionsNormalization when an interval has no common measurements
        with the main interval"""
        config = create_multiple_regions_normalization_config(
            MULTIPLE_REGIONS_NORMALIZATION_KWARGS)

        normalizer = MultipleRegionsNormalization(config["normalizer"])
        norm_factors = copy(NORM_FACTORS)
        norm_factors["norm factor 0"] = np.nan
        normalizer.norm_factors = norm_factors

        expected_message = ("Error computing the correction for normalisation "
                            "factor interval 0. No common measurements with "
                            "the main intervals were found.")
        with self.assertRaises(NormalizerError) as context_manager:
            normalizer.compute_correction_factors()
        self.compare_error_message(context_manager, expected_message)

    def test_multiple_regions_normalization_compute_norm_factors(self):
        """Test method compute_norm_factors from MultipleRegionsNormalization"""
        out_file = f"{THIS_DIR}/results/multiple_regions_normalization_compute_norm_factors.txt"
        test_file = f"{THIS_DIR}/data/multiple_regions_normalization_compute_norm_factors.txt"

        config = create_multiple_regions_normalization_config(
            MULTIPLE_REGIONS_NORMALIZATION_KWARGS)

        normalizer = MultipleRegionsNormalization(config["normalizer"])
        normalizer.compute_norm_factors(REBINNED_SPECTRA)

        self.assertTrue(normalizer.norm_factors is not None)
        self.assertTrue(isinstance(normalizer.norm_factors, pd.DataFrame))

        # save results
        normalizer.norm_factors.to_csv(out_file, sep=" ", index=False)

        # compare against expectations
        self.compare_ascii_numeric(test_file, out_file)

    def test_multiple_regions_normalization_invalid_intervals(self):
        """Check that errors are raised when the given intervals are not
        properly formatted"""

        # wrong string format
        normalizer_kwargs = MULTIPLE_REGIONS_NORMALIZATION_KWARGS.copy()
        normalizer_kwargs.update({"intervals": "4400 to 4600, 4600 to 4800"})

        expected_message = (
            "Wrong format for variable 'intervals'. Expected "
            "'start0 - end0, start1 - end1, ..., startN - endN'"
            " where startX and endX are positive numbers. Found: "
            "4400 to 4600, 4600 to 4800")
        self.run_multiple_regions_normalization_with_errors(
            normalizer_kwargs, expected_message)

        # interval start wavelength < interval end wavelength
        normalizer_kwargs = MULTIPLE_REGIONS_NORMALIZATION_KWARGS.copy()
        normalizer_kwargs.update({"intervals": "4600 - 4500, 4600 - 4800"})
        expected_message = (
            "Invalid interval found: [4600. 4500.]. Starting wavelength "
            "should be smaller than ending interval")
        self.run_multiple_regions_normalization_with_errors(
            normalizer_kwargs, expected_message)

        # main interval too large
        normalizer_kwargs = MULTIPLE_REGIONS_NORMALIZATION_KWARGS.copy()
        normalizer_kwargs.update({"main interval": "999"})
        expected_message = (
            "Invalid value for 'main interval'. Selected interval "
            "999 as main interval, but I only read "
            "2 intervals (keep in mind the zero-based "
            "indexing in python)")
        self.run_multiple_regions_normalization_with_errors(
            normalizer_kwargs, expected_message)

        # negative main interval
        normalizer_kwargs = MULTIPLE_REGIONS_NORMALIZATION_KWARGS.copy()
        normalizer_kwargs.update({"main interval": "-1"})
        expected_message = (
            "Invalid value for 'main interval'. Expected a positive integer. "
            "Found: -1")
        self.run_multiple_regions_normalization_with_errors(
            normalizer_kwargs, expected_message)

    def test_multiple_regions_normalization_invalid_save_format(self):
        """Check the behaviour when the save format is not valid"""
        normalizer_kwargs = MULTIPLE_REGIONS_NORMALIZATION_KWARGS.copy()
        normalizer_kwargs.update({"save format": "invalid"})

        expected_message = ("Invalid save format. Accepted options are '" +
                            " ".join(ACCEPTED_SAVE_FORMATS) +
                            "' Found: invalid")
        self.run_multiple_regions_normalization_with_errors(
            normalizer_kwargs, expected_message)

    def test_multiple_regions_normalization_missing_options(self):
        """Check that errors are raised when required options are missing"""
        options_and_values = [
            ("intervals", "1300 - 1500, 2000 - 2600, 4400 - 4800"),
            ("log directory", f"{THIS_DIR}/results/"),
            ("main interval", "1"),
            ("num processors", "1"),
            ("save format", "fits.gz"),
        ]

        self.check_missing_options(options_and_values,
                                   MultipleRegionsNormalization,
                                   NormalizerError, Normalizer)

    def test_multiple_regions_normalization_normalize_spectrum(self):
        """Test method normalize_spectrum from MultipleRegionsNormalization"""
        out_file = f"{THIS_DIR}/results/multiple_regions_normalization_normalize_spectrum.txt"
        test_file = f"{THIS_DIR}/data/multiple_regions_normalization_normalize_spectrum.txt"

        config = create_multiple_regions_normalization_config(
            MULTIPLE_REGIONS_NORMALIZATION_KWARGS)
        normalizer = MultipleRegionsNormalization(config["normalizer"])

        norm_factors = copy(NORM_FACTORS)
        norm_factors.loc[norm_factors["specid"] == REBINNED_SPECTRA[1].specid,
                         "norm factor"] = 0
        normalizer.norm_factors = norm_factors

        # normalize a spectrum with non-zero normallization factor
        normalized_spectrum = normalizer.normalize_spectrum(
            copy(REBINNED_SPECTRA[0]))

        # normalize a spectrum with zero normallization factor
        normalized_spectrum2 = normalizer.normalize_spectrum(
            copy(REBINNED_SPECTRA[1]))

        # save results
        with open(out_file, "w", encoding="utf-8") as results:
            results.write("# wavelength norm_flux norm_flux2\n")
            for wavelength, norm_flux, norm_flux2 in zip(
                    Spectrum.common_wavelength_grid,
                    normalized_spectrum.normalized_flux,
                    normalized_spectrum2.normalized_flux):
                results.write(f"{wavelength} {norm_flux}  {norm_flux2}\n")

        # compare against expectations
        self.compare_ascii_numeric(test_file, out_file)

    def test_multiple_regions_normalization_save_norm_factors(self):
        """Test method compute_norm_factors from MultipleRegionsNormalization"""
        out_dir = f"{THIS_DIR}/results/multiple_regions_normalization_save_norm_factors/"
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)
        test_dir = f"{THIS_DIR}/data/multiple_regions_normalization_save_norm_factors/"

        save_formats = ["txt", "fits.gz"]

        for save_format in save_formats:

            normalizer_kwargs = MULTIPLE_REGIONS_NORMALIZATION_KWARGS.copy()
            normalizer_kwargs.update({
                "log directory": out_dir,
                "save format": save_format,
            })
            config = create_multiple_regions_normalization_config(
                normalizer_kwargs)

            normalizer = MultipleRegionsNormalization(config["normalizer"])
            normalizer.norm_factors = NORM_FACTORS
            normalizer.correction_factors = CORRECTION_FACTORS

            # save results
            normalizer.save_norm_factors()

            # compare against expectations
            self.compare_files(f"{test_dir}normalization_factors.{save_format}",
                               f"{out_dir}normalization_factors.{save_format}")

            if save_format == "txt":
                self.compare_ascii_numeric(
                    f"{test_dir}normalization_intervals.{save_format}",
                    f"{out_dir}normalization_intervals.{save_format}")
                self.compare_ascii_numeric(
                    f"{test_dir}correction_factors.{save_format}",
                    f"{out_dir}correction_factors.{save_format}")

    def test_no_normalization(self):
        """Test the class NoNormalization"""
        config = ConfigParser()
        config.read_dict({"normalizer": {}})
        normalizer = NoNormalization(config["normalizer"])

        spectra = [copy(spectrum) for spectrum in REBINNED_SPECTRA]

        normalizer.compute_norm_factors(spectra)
        spectra = [
            normalizer.normalize_spectrum(spectrum) for spectrum in spectra
        ]
        for spectrum in spectra:
            self.assertTrue(np.allclose(spectrum.flux_common_grid, spectrum.normalized_flux))

    def test_normalizer(self):
        """Test the abstract normalizer"""
        normalizer = Normalizer()

        # calling compute_norm_factors should raise an error
        expected_message = (
            "Method 'compute_norm_factors' was not overloaded by child class")
        with self.assertRaises(NormalizerError) as context_manager:
            normalizer.compute_norm_factors(REBINNED_SPECTRA)
        self.compare_error_message(context_manager, expected_message)

        # calling normalize_spectrum should raise an error
        expected_message = (
            "Method 'normalize_spectrum' was not overloaded by child class")
        with self.assertRaises(NormalizerError) as context_manager:
            normalizer.normalize_spectrum(copy(REBINNED_SPECTRA[0]))
        self.compare_error_message(context_manager, expected_message)

        # calling save_norm_factors should not raise an error
        self.assertTrue(normalizer.save_norm_factors() is None)


def create_multiple_regions_normalization_config(normalizer_kwargs):
    """Create a configuration instance to run MultipleRegionsNormalization

    Arguments
    ---------
    normalizer_kwargs: dict
    Keyword arguments to set the configuration run

    Return
    ------
    config: ConfigParser
    Run configuration
    """
    config = ConfigParser()
    config.read_dict({"normalizer": normalizer_kwargs})
    for key, value in defaults_multiple_regions_normalization.items():
        if key not in config["normalizer"]:
            config["normalizer"][key] = str(value)

    return config


if __name__ == '__main__':
    unittest.main()
