"""This file contains spectrum tests"""
import unittest

import numpy as np

from stacking.errors import SpectrumError
from stacking.spectrum import Spectrum
from stacking.tests.abstract_test import AbstractTest

SIZE = 60
HALF_SIZE = SIZE // 2
THIRD_SIZE = SIZE // 3

FLUX = np.arange(SIZE, dtype=float)
IVAR = np.ones(SIZE, dtype=float)
RESDHIFT = 2.1
SPECID = 1234
WAVELENGTH = np.arange(SIZE, dtype=float) - 0.5


class SpectrumTest(AbstractTest):
    """Test the class Spectrum

    Methods
    -------
    (see AbstractTest in stacking/tests/abstract_test.py)
    check_spectrum
    test_spectrum_init
    test_spectrum_set_common_wavelength_grid
    test_spectrum_set_flux_ivar_common_grid
    test_spectrum_set_normalized_flux
    """

    def check_spectrum(self,
                       spectrum,
                       common_wavelength_grid=None,
                       flux_common_grid=None,
                       ivar_common_grid=None,
                       normalized_flux=None):
        """Check the spectrum properties

        Arguments
        ---------
        spectrum: Spectrum
        The spectrum to be checked

        common_wavelength_grid: array or None - Default: None
        The common wavelength grid. None for no grid.

        flux_wavelength_grid: array or None - Default: None
        The flux in the common wavelength grid. None for no flux.

        common_wavelength_grid: array or None - Default: None
        The inverse variance in the common wavelength grid. None for no ivar.

        normalized_flux: array or None - Default: None
        The normalized flux. None for no ivar.
        """
        self.assertTrue(spectrum.specid == SPECID)

        self.assertTrue(spectrum.flux.size, SIZE)
        self.assertTrue(np.allclose(spectrum.flux, FLUX))

        self.assertTrue(spectrum.ivar.size, SIZE)
        self.assertTrue(np.allclose(spectrum.ivar, IVAR))

        self.assertTrue(spectrum.wavelength.size, SIZE)
        self.assertTrue(np.allclose(spectrum.wavelength, WAVELENGTH))

        self.assertTrue(np.isclose(spectrum.redshift, RESDHIFT))

        if flux_common_grid is None:
            self.assertTrue(spectrum.flux_common_grid is None)
        else:
            self.assertTrue(
                spectrum.flux_common_grid.size == flux_common_grid.size)
            self.assertTrue(
                np.allclose(spectrum.flux_common_grid, flux_common_grid))

        if ivar_common_grid is None:
            self.assertTrue(spectrum.ivar_common_grid is None)
        else:
            self.assertTrue(
                spectrum.ivar_common_grid.size == ivar_common_grid.size)
            self.assertTrue(
                np.allclose(spectrum.ivar_common_grid, ivar_common_grid))

        if normalized_flux is None:
            self.assertTrue(spectrum.normalized_flux is None)
        else:
            self.assertTrue(
                spectrum.normalized_flux.size == normalized_flux.size)
            self.assertTrue(
                np.allclose(spectrum.normalized_flux, normalized_flux))

        if common_wavelength_grid is None:
            self.assertTrue(Spectrum.common_wavelength_grid is None)
        else:
            self.assertTrue(spectrum.common_wavelength_grid.size ==
                            common_wavelength_grid.size)
            self.assertTrue(
                np.allclose(Spectrum.common_wavelength_grid,
                            common_wavelength_grid))

    def test_spectrum_init(self):
        """ Test the method Spectrum.__init__"""
        # make sure Spectrum.common_wavelength_grid is not set
        # (this is set in the test setUp)
        Spectrum.common_wavelength_grid = None

        spectrum = Spectrum(SPECID, FLUX, IVAR, WAVELENGTH, RESDHIFT)
        self.check_spectrum(spectrum)

    def test_spectrum_set_common_wavelength_grid(self):
        """ Test the class method Spectrum.set_common_wavelength_grid"""
        Spectrum.set_common_wavelength_grid(WAVELENGTH)

        self.assertTrue(np.allclose(Spectrum.common_wavelength_grid,
                                    WAVELENGTH))

    def test_spectrum_set_flux_ivar_common_grid(self):
        """ Test the method Spectrum.set_flux_ivar_common_grid"""
        spectrum = Spectrum(SPECID, FLUX, IVAR, WAVELENGTH, RESDHIFT)
        Spectrum.set_common_wavelength_grid(WAVELENGTH[:HALF_SIZE])

        self.check_spectrum(spectrum,
                            common_wavelength_grid=WAVELENGTH[:HALF_SIZE])

        # case: wrong flux size
        expected_message = (
            "Normalized flux should be based on the common wavelength grid "
            f"but sizes differ. flux_common_grid.size = {THIRD_SIZE} "
            f"Spectrum.common_wavelength_grid.size = {HALF_SIZE}")
        with self.assertRaises(SpectrumError) as context_manager:
            spectrum.set_flux_ivar_common_grid(FLUX[:THIRD_SIZE],
                                               IVAR[:HALF_SIZE])
        self.compare_error_message(context_manager, expected_message)

        # case: wrong ivar size
        expected_message = (
            "Normalized ivar should be based on the common wavelength grid "
            f"but sizes differ. ivar_common_grid.size = {THIRD_SIZE} "
            f"Spectrum.common_wavelength_grid.size = {HALF_SIZE}")
        with self.assertRaises(SpectrumError) as context_manager:
            spectrum.set_flux_ivar_common_grid(FLUX[:HALF_SIZE],
                                               IVAR[:THIRD_SIZE])
        self.compare_error_message(context_manager, expected_message)

        # case: correct execution
        spectrum.set_flux_ivar_common_grid(FLUX[:HALF_SIZE], IVAR[:HALF_SIZE])

        self.check_spectrum(
            spectrum,
            common_wavelength_grid=WAVELENGTH[:HALF_SIZE],
            flux_common_grid=FLUX[:HALF_SIZE],
            ivar_common_grid=IVAR[:HALF_SIZE],
        )

    def test_spectrum_set_normalized_flux(self):
        """ Test the method Spectrum.set_normalized_flux"""
        spectrum = Spectrum(SPECID, FLUX, IVAR, WAVELENGTH, RESDHIFT)
        Spectrum.set_common_wavelength_grid(WAVELENGTH[:HALF_SIZE])

        self.check_spectrum(spectrum,
                            common_wavelength_grid=WAVELENGTH[:HALF_SIZE])

        # case: wrong flux size
        expected_message = (
            "Normalized flux should be based on the common wavelength grid "
            f"but sizes differ. normalized_flux.size = {THIRD_SIZE} "
            f"Spectrum.common_wavelength_grid.size = {HALF_SIZE}")
        with self.assertRaises(SpectrumError) as context_manager:
            spectrum.set_normalized_flux(FLUX[:THIRD_SIZE])
        self.compare_error_message(context_manager, expected_message)

        # case: correct execution
        spectrum.set_normalized_flux(FLUX[:HALF_SIZE])
        self.check_spectrum(spectrum,
                            common_wavelength_grid=WAVELENGTH[:HALF_SIZE],
                            normalized_flux=FLUX[:HALF_SIZE])


if __name__ == '__main__':
    unittest.main()
