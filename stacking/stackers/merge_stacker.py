""" This module defines the abstract class MergeStacker to compute the stack
using different partial runs"""
import os

from astropy.io import fits
import numpy as np

from stacking.errors import StackerError
from stacking.spectrum import Spectrum
from stacking.stacker import Stacker, accepted_options, required_options
from stacking.stacker import (  # pylint: disable=unused-import
    defaults)
from stacking.utils import update_accepted_options, update_required_options

accepted_options = update_accepted_options(accepted_options, ["stack list"])
required_options = update_required_options(required_options, ["stack list"])

ASSOCIATED_WRITER = "StandardWriter"


class MergeStacker(Stacker):
    """Abstract class to compute the satck using different partial runs

    Methods
    -------
    (see Stacker in stacking/stacker.py)
    __init__
    __parse_config

    Attributes
    ----------
    (see Stacker in stacking/stacker.py)
    stacks: list of (array of float, array of float)
    """

    def __init__(self, config):
        """Initialize class instance

        Arguments
        ---------
        config: configparser.SectionProxy
        Parsed options to initialize class

        Raise
        -----
        StackerError if the selected reading mode is not supported
        """
        super().__init__(config)

        self.stack_list = None
        self.__parse_config(config)

        self.stacks = load_stacks(self.stack_list)

    def __parse_config(self, config):
        """Parse the configuration options

        Arguments
        ---------
        config: configparser.SectionProxy
        Parsed options to initialize class

        Raise
        -----
        StackerError upon missing required variables
        StackerError if the stacking files are missing
        StackerError if the stacking files are not fits files
        """
        stack_list = config.get("stack list")
        if stack_list is None:
            raise StackerError("Missing argument 'stack list' required by "
                               "MergeMeanStacker")
        self.stack_list = stack_list.split()
        for stack_file in self.stack_list:
            if not os.path.exists(stack_file):
                raise StackerError(
                    f"Could not find file {stack_file} required by "
                    "MergeStacker")
            if not (stack_file.endswith(".fits") or
                    stack_file.endswith(".fits.gz")):
                raise StackerError(
                    f"MergeStacker: Expected a fits file, found {stack_file}")


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
