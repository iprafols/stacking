"""This file contains normalizer tests"""
from copy import copy
import os
import unittest

import numpy as np
import pandas as pd

from stacking.normalizers.multiple_regions_normalization_utils import (
    compute_norm_factors,
    save_correction_factors_ascii,
    save_norm_factors_ascii,
    save_norm_factors_fits,
    save_norm_intervals_ascii,
    select_final_normalisation_factor,
)
from stacking.tests.abstract_test import AbstractTest
from stacking.tests.utils import NORM_FACTORS, INTERVALS, CORRECTION_FACTORS

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
os.environ["THIS_DIR"] = THIS_DIR


class MultipleRegionsNormalizationUtilsTest(AbstractTest):
    """Test the MultipleRegionsNormalization utils.

    Methods
    -------
    (see AbstractTest in stacking/tests/abstract_test.py)
    test_compute_norm_factors
    test_save_correction_factors_ascii
    test_save_norm_factors_ascii
    test_save_norm_factors_fits
    test_save_norm_intervals_ascii
    test_select_final_normalisation_factor
    """

    def test_compute_norm_factors(self):
        """Test function compute_norm_factors"""
        # We add three intervals, one empty, one with negative flux and
        # one wiht positive flux
        flux = np.arange(10, dtype=float) - 5.0
        ivar = np.arange(10, dtype=float) / 5.
        wavelength = np.arange(10, dtype=float)
        num_intervals = 3
        intervals = np.array([(-5., 0.), (0., 5.), (5., 10.)])
        sigma_i2 = 0.0025

        results_jit = compute_norm_factors(flux,
                                           ivar,
                                           wavelength,
                                           num_intervals,
                                           intervals,
                                           sigma_i2=sigma_i2)

        self.assertTrue(results_jit.shape[0] == 4 * num_intervals)
        # check first interval: empty
        self.assertTrue(np.isnan(results_jit[0]))
        self.assertTrue(np.isnan(results_jit[1]))
        self.assertTrue(results_jit[2] == 0)
        self.assertTrue(np.isnan(results_jit[3]))
        # check second interval: negative flux
        self.assertTrue(np.isnan(results_jit[4]))
        self.assertTrue(np.isnan(results_jit[5]))
        self.assertTrue(results_jit[6] == 5)
        self.assertTrue(np.isnan(results_jit[7]))
        # check second interval: positive flux
        self.assertTrue(np.isclose(results_jit[8], 2.28475841))
        self.assertTrue(np.isclose(results_jit[9], 2.70317018))
        self.assertTrue(results_jit[10] == 5)
        self.assertTrue(np.isclose(results_jit[11], 6.97459588))

        results_python = compute_norm_factors.py_func(flux,
                                                      ivar,
                                                      wavelength,
                                                      num_intervals,
                                                      intervals,
                                                      sigma_i2=sigma_i2)

        self.assertTrue(results_jit.shape[0] == results_python.shape[0])
        self.assertTrue(np.allclose(results_jit, results_python,
                                    equal_nan=True))

    def test_compute_norm_factors_no_sigma_i(self):
        """Test function compute_norm_factors"""
        # we run a single interval with positive flux and 0 sigma_I
        flux = np.arange(10, dtype=float) - 5.0
        ivar = np.arange(10, dtype=float) / 5.
        wavelength = np.arange(10, dtype=float)
        num_intervals = 1
        intervals = np.array([(5., 10.)])
        sigma_i2 = 0.0

        results_jit = compute_norm_factors(flux,
                                           ivar,
                                           wavelength,
                                           num_intervals,
                                           intervals,
                                           sigma_i2=sigma_i2)

        self.assertTrue(results_jit.shape[0] == 4)
        self.assertTrue(np.isclose(results_jit[0], 2.2857142857142856))
        self.assertTrue(np.isclose(results_jit[1], 2.704493615131253))
        self.assertTrue(results_jit[2] == 5)
        self.assertTrue(np.isclose(results_jit[3], 7.0))

        results_python = compute_norm_factors.py_func(flux,
                                                      ivar,
                                                      wavelength,
                                                      num_intervals,
                                                      intervals,
                                                      sigma_i2=sigma_i2)

        self.assertTrue(results_jit.shape[0] == results_python.shape[0])
        self.assertTrue(np.allclose(results_jit, results_python,
                                    equal_nan=True))

    def test_save_correction_factors_ascii(self):
        """Test function save_correction_factors_ascii"""
        out_file = f"{THIS_DIR}/results/save_correction_factors_ascii.txt"

        correction_factors = np.arange(5) + 1

        save_correction_factors_ascii(out_file, correction_factors)

        # load output
        correction_factors_loaded = np.genfromtxt(
            out_file, names=["intervals", "correction_factors"])

        # check against expectations
        self.assertTrue(
            np.allclose(correction_factors_loaded["intervals"], np.arange(5)))
        self.assertTrue(
            np.allclose(correction_factors_loaded["correction_factors"],
                        correction_factors))

    def test_save_norm_factors_ascii(self):
        """Test function save_norm_factors_ascii"""
        out_file = f"{THIS_DIR}/results/save_norm_factors_ascii.txt"

        save_norm_factors_ascii(out_file, NORM_FACTORS)

        # load output
        norm_factors = pd.read_csv(out_file, delim_whitespace=True)

        # check against expectations
        self.compare_df(NORM_FACTORS, norm_factors)

    def test_save_norm_factors_fits(self):
        """Test function save_norm_factors_fits"""
        out_file = f"{THIS_DIR}/results/save_norm_factors_fits.txt"
        test_file = f"{THIS_DIR}/data/save_norm_factors_fits.txt"

        save_norm_factors_fits(out_file, NORM_FACTORS, INTERVALS,
                               CORRECTION_FACTORS)

        self.compare_fits(out_file, test_file)

    def test_save_norm_intervals_ascii(self):
        """Test function save_norm_intervals_ascii"""
        out_file = f"{THIS_DIR}/results/save_norm_intervals_ascii.txt"

        save_norm_intervals_ascii(out_file, INTERVALS)

        # load output
        intervals = np.genfromtxt(out_file, names=["start", "end"])

        # load output
        intervals = np.genfromtxt(out_file)

        # check against expectations
        self.assertTrue(intervals.shape == INTERVALS.shape)
        self.assertTrue(np.allclose(intervals, INTERVALS))

    def test_select_final_normalisation_factor(self):
        """Test function select_final_normalisation_factor"""
        norm_factors = copy(NORM_FACTORS)

        cases = {
            "normal run": 0.05,
            "very large S/N requirement": 100,
        }

        for case_name, min_nrom_sn in cases.items():
            results = pd.DataFrame()
            results[["norm factor", "norm S/N",
                     "chosen interval"]] = norm_factors.apply(
                         select_final_normalisation_factor,
                         axis=1,
                         args=(CORRECTION_FACTORS, min_nrom_sn),
                         result_type='expand',
                     )
            if case_name == "normal run":
                self.compare_df(
                    NORM_FACTORS[["norm factor", "norm S/N",
                                  "chosen interval"]], results)
            else:
                comp = copy(
                    NORM_FACTORS[["norm factor", "norm S/N",
                                  "chosen interval"]])
                comp["norm factor"] = np.nan
                comp["norm S/N"] = np.nan
                comp["chosen interval"] = -1.0
                self.compare_df(
                    comp[["norm factor", "norm S/N", "chosen interval"]],
                    results)


if __name__ == '__main__':
    unittest.main()
