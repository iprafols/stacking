""" This module defines the abstract class MergeStacker to compute the stack
using different partial runs"""
from astropy.io import fits
import numpy as np

from stacking.errors import StackerError
from stacking.spectrum import Spectrum


def load_stacks(stack_list):
    """ Load stacks from previous runs

    Arguments
    ---------
    stack_list: list of str
    Fits files containing the stacks. All files should have the same wavelength
    grid

    Return
    ------
    stacks: list of (array of float, array of float)
    List of stacks. Each item contains a tuple with the flux and weight arrays

    Raise
    -----
    StackerError if the wavelength arrays of the different files are not equal
    """
    stacks = []

    for file in stack_list:
        hdul = fits.open(file)

        # disabling pylint no-members as they are false positives here
        wavelength = hdul["STACKED_SPECTRUM"].data["WAVELENGTH"]  # pylint: disable=no-member
        flux = hdul["STACKED_SPECTRUM"].data["STACKED_FLUX"]  # pylint: disable=no-member
        weight = hdul["STACKED_SPECTRUM"].data["STACKED_WEIGHT"]  # pylint: disable=no-member

        hdul.close()

        # check wavelength grid
        if Spectrum.common_wavelength_grid is None:
            Spectrum.set_common_wavelength_grid(wavelength)
        elif Spectrum.common_wavelength_grid.size != wavelength.size:
            raise StackerError(
                "Error loading stacked spectra. Expecting the stacks to have the "
                "same wavelengths, but found wavelength grids of different sizes "
                f"({Spectrum.common_wavelength_grid.size} and {wavelength.size})"
            )
        elif not np.allclose(Spectrum.common_wavelength_grid, wavelength):
            error_message = (
                "Error loading stacked spectra. Expecting the stacks to have the "
                "same wavelengths, but found differnt wavelength grids:\n"
                "wave1 wave2 areclose\n")
            for item1, item2 in zip(Spectrum.common_wavelength_grid,
                                    wavelength):
                error_message += f"{item1} {item2} {np.isclose(item1, item2)}\n"

            raise StackerError(error_message)

        # add to list
        stacks.append((flux, weight))

    return stacks
